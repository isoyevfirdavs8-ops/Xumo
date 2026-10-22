
from django.core.management.base import BaseCommand

from apps.hostel.services import expire_hostel_reservations


class Command(BaseCommand):
    help = "To'lov muddati tugagan hostel bronlarini bo'shatadi."

    def handle(self, *args, **options):
        count = expire_hostel_reservations()

        self.stdout.write(
            self.style.SUCCESS(
                f"Yakunlandi. {count} ta rezervatsiya "
                "expired holatiga o'tkazildi."
            )
        )
