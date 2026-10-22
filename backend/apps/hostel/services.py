
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.backends.postgresql.psycopg_any import DateRange
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import HostelBooking, HostelReservation, HostelRoom


PAYMENT_HOLD_MINUTES = 15


def _validate_existing_reservation(
    reservation,
    *,
    check_in,
    check_out,
    capacity,
    room_count,
):
    """
    Bir xil idempotency key boshqa ma'lumotlar bilan
    qayta ishlatilmaganini tekshiradi.
    """
    bookings = list(
        reservation.bookings.select_related("room").all()
    )

    same_request = (
        reservation.check_in == check_in
        and reservation.check_out == check_out
        and len(bookings) == room_count
        and all(
            booking.room.capacity == capacity
            for booking in bookings
        )
    )

    if not same_request:
        raise ValidationError({
            "idempotency_key": (
                "Bu Idempotency-Key boshqa bron so'rovi "
                "uchun ishlatilgan."
            )
        })

    return reservation


def create_hostel_reservation(
    *,
    user,
    check_in,
    check_out,
    capacity,
    room_count,
    idempotency_key=None,
):
    """
    Bir yoki bir nechta xonani atomik bron qiladi.

    Himoya:
    - transaction.atomic()
    - user row lock
    - room row locks
    - PostgreSQL ExclusionConstraint
    - Idempotency-Key
    """

    if not user or not user.is_authenticated:
        raise ValidationError(
            "Bron qilish uchun tizimga kiring."
        )

    if check_in < timezone.localdate():
        raise ValidationError({
            "check_in": "O'tgan sanaga bron qilish mumkin emas."
        })

    if check_out <= check_in:
        raise ValidationError({
            "check_out": (
                "Ketish sanasi kelish sanasidan keyin "
                "bo'lishi kerak."
            )
        })

    if capacity not in (2, 3, 4):
        raise ValidationError({
            "capacity": "Faqat 2, 3 yoki 4 kishilik xona mavjud."
        })

    if not 1 <= room_count <= 20:
        raise ValidationError({
            "room_count": (
                "Xonalar soni 1 dan 20 gacha bo'lishi kerak."
            )
        })

    nights = (check_out - check_in).days

    try:
        with transaction.atomic():

            # Bir foydalanuvchining bir vaqtda kelgan
            # bron so'rovlarini ketma-ket qayta ishlaymiz.
            user_model = type(user)

            user_model.objects.select_for_update().get(
                pk=user.pk
            )

            # Idempotency tekshiruvi lock olingandan keyin.
            if idempotency_key is not None:
                existing = (
                    HostelReservation.objects
                    .filter(
                        user_id=user.pk,
                        idempotency_key=idempotency_key,
                    )
                    .first()
                )

                if existing is not None:
                    return _validate_existing_reservation(
                        existing,
                        check_in=check_in,
                        check_out=check_out,
                        capacity=capacity,
                        room_count=room_count,
                    )

            # Xonalarni barqaror tartibda bloklaymiz.
            rooms = list(
                HostelRoom.objects
                .filter(
                    status=HostelRoom.Status.ACTIVE,
                    capacity=capacity,
                )
                .order_by("pk")
                .select_for_update()
            )

            if not rooms:
                raise ValidationError({
                    "capacity": (
                        "Tanlangan sig'imda faol xonalar "
                        "mavjud emas."
                    )
                })

            room_ids = [room.pk for room in rooms]

            occupied_ids = set(
                HostelBooking.objects.filter(
                    room_id__in=room_ids,
                    status__in=[
                        HostelBooking.Status.PENDING_PAYMENT,
                        HostelBooking.Status.PAID,
                    ],
                    stay_period__overlap=(
                        check_in,
                        check_out,
                    ),
                ).values_list(
                    "room_id",
                    flat=True,
                )
            )

            available_rooms = [
                room for room in rooms
                if room.pk not in occupied_ids
            ]

            if len(available_rooms) < room_count:
                raise ValidationError({
                    "room_count": (
                        f"Tanlangan sanalarda faqat "
                        f"{len(available_rooms)} ta xona bo'sh."
                    )
                })

            selected_rooms = available_rooms[:room_count]

            total_price = sum(
                (
                    room.daily_price * Decimal(nights)
                    for room in selected_rooms
                ),
                Decimal("0.00"),
            )

            now = timezone.now()

            reservation = HostelReservation.objects.create(
                user=user,
                check_in=check_in,
                check_out=check_out,
                status=HostelReservation.Status.PENDING_PAYMENT,
                total_price=total_price,
                payment_expires_at=(
                    now + timedelta(
                        minutes=PAYMENT_HOLD_MINUTES
                    )
                ),
                idempotency_key=idempotency_key,
            )

            period = DateRange(
                check_in,
                check_out,
                bounds="[)",
            )

            HostelBooking.objects.bulk_create([
                HostelBooking(
                    reservation=reservation,
                    room=room,
                    stay_period=period,
                    status=HostelBooking.Status.PENDING_PAYMENT,
                    daily_price_snapshot=room.daily_price,
                )
                for room in selected_rooms
            ])

            return reservation

    except IntegrityError as exc:
        raise ValidationError({
            "detail": (
                "Bron yaratishda konflikt yuz berdi. "
                "Bo'sh xonalarni qayta tekshiring."
            )
        }) from exc


def expire_hostel_reservations(*, batch_size=100):
    """
    To'lov muddati tugagan rezervatsiyalarni
    atomik ravishda expired holatiga o'tkazadi.
    """
    if batch_size < 1:
        raise ValueError("batch_size musbat bo'lishi kerak.")

    expired_count = 0

    while True:
        now = timezone.now()

        with transaction.atomic():
            reservations = list(
                HostelReservation.objects
                .select_for_update(skip_locked=True)
                .filter(
                    status=(
                        HostelReservation.Status.PENDING_PAYMENT
                    ),
                    payment_expires_at__lte=now,
                )
                .order_by(
                    "payment_expires_at",
                    "pk",
                )[:batch_size]
            )

            if not reservations:
                break

            reservation_ids = [
                reservation.pk
                for reservation in reservations
            ]

            HostelBooking.objects.filter(
                reservation_id__in=reservation_ids,
                status=HostelBooking.Status.PENDING_PAYMENT,
            ).update(
                status=HostelBooking.Status.EXPIRED
            )

            updated = HostelReservation.objects.filter(
                pk__in=reservation_ids,
                status=HostelReservation.Status.PENDING_PAYMENT,
            ).update(
                status=HostelReservation.Status.EXPIRED,
                updated_at=now,
            )

            expired_count += updated

    return expired_count
