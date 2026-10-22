
import { useEffect, useRef, useState } from "react";
import {
  BedDouble,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Minus,
  Plus,
  RefreshCw,
  ShieldCheck,
  Users,
} from "lucide-react";

import {
  createHostelBooking,
  getHostelAvailability,
} from "../services/hostelApi";

import "./HostelBookingPage.css";

const CAPACITIES = [2, 3, 4];

function localDate(offset = 0) {
  const now = new Date();

  const date = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate() + offset
  );

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function addDays(dateString, days) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    return "";
  }

  const [year, month, day] = dateString
    .split("-")
    .map(Number);

  const date = new Date(year, month - 1, day + days);

  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");

  return `${y}-${m}-${d}`;
}

function formatMoney(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return "—";
  }

  return `${new Intl.NumberFormat("uz-UZ", {
    maximumFractionDigits: 2,
  }).format(amount)} so'm`;
}

function formatDateTime(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString("uz-UZ");
}

function getErrorMessage(error) {
  if (error?.name === "AbortError") {
    return "";
  }

  const raw = error?.message || "Xatolik yuz berdi.";

  try {
    const parsed = JSON.parse(raw);

    if (parsed && typeof parsed === "object") {
      return Object.entries(parsed)
        .map(([field, messages]) => {
          const text = Array.isArray(messages)
            ? messages.join(", ")
            : typeof messages === "object" && messages !== null
              ? JSON.stringify(messages)
              : String(messages);

          return `${field}: ${text}`;
        })
        .join(" | ");
    }
  } catch {
    // Oddiy matnli xabar.
  }

  return raw;
}

function getSummary(data, capacity) {
  if (!Array.isArray(data?.summary)) {
    return null;
  }

  return (
    data.summary.find(
      (item) => Number(item.capacity) === Number(capacity)
    ) || null
  );
}

export default function HostelBookingPage() {
  const [checkIn, setCheckIn] = useState(
    () => localDate(1)
  );

  const [checkOut, setCheckOut] = useState(
    () => localDate(2)
  );

  const [capacity, setCapacity] = useState(2);
  const [roomCount, setRoomCount] = useState(1);

  const [refreshKey, setRefreshKey] = useState(0);

  const [availability, setAvailability] = useState(null);
  const [loading, setLoading] = useState(true);
  const [availabilityError, setAvailabilityError] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [bookingError, setBookingError] = useState("");
  const [reservation, setReservation] = useState(null);

  const bookingAttemptRef = useRef(null);
  const submittingRef = useRef(false);

  const datesValid =
    /^\d{4}-\d{2}-\d{2}$/.test(checkIn) &&
    /^\d{4}-\d{2}-\d{2}$/.test(checkOut) &&
    checkIn >= localDate() &&
    checkOut > checkIn;

  useEffect(() => {
    const controller = new AbortController();

    async function loadAvailability() {
      setLoading(true);
      setAvailability(null);
      setAvailabilityError("");

      if (!datesValid) {
        setAvailabilityError(
          "Kirish va chiqish sanalarini to'g'ri tanlang."
        );
        setLoading(false);
        return;
      }

      try {
        const data = await getHostelAvailability({
          checkIn,
          checkOut,
          signal: controller.signal,
        });

        if (controller.signal.aborted) {
          return;
        }

        if (
          !data ||
          !Array.isArray(data.summary) ||
          !Array.isArray(data.rooms)
        ) {
          throw new Error(
            "Server availability ma'lumotlarini noto'g'ri qaytardi."
          );
        }

        setAvailability(data);
      } catch (error) {
        if (!controller.signal.aborted) {
          setAvailabilityError(getErrorMessage(error));
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadAvailability();

    return () => controller.abort();
  }, [checkIn, checkOut, datesValid, refreshKey]);

  const selectedSummary = getSummary(
    availability,
    capacity
  );

  const availableRooms = Math.max(
    0,
    Number(selectedSummary?.available_rooms ?? 0)
  );

  const totalRooms = Math.max(
    0,
    Number(selectedSummary?.total_rooms ?? 0)
  );

  // Backend serializer: room_count max_value=20.
  const maxRooms = Math.min(20, availableRooms);

  const selectedRooms = Array.isArray(availability?.rooms)
    ? availability.rooms.filter(
        (room) => Number(room.capacity) === capacity
      )
    : [];

  // Availability yangilanganda avvalgi xona soni
  // yangi mavjudlikdan oshib ketmasin.
  useEffect(() => {
    if (!availability) return;

    setRoomCount((current) => {
      if (maxRooms < 1) return 1;
      return Math.min(Math.max(current, 1), maxRooms);
    });
  }, [availability, maxRooms]);

  function resetBookingAttempt() {
    bookingAttemptRef.current = null;
    setBookingError("");
  }

  function changeCheckIn(value) {
    if (submittingRef.current) return;

    setCheckIn(value);

    if (value && (!checkOut || checkOut <= value)) {
      setCheckOut(addDays(value, 1));
    }

    setRoomCount(1);
    setReservation(null);
    resetBookingAttempt();
  }

  function changeCheckOut(value) {
    if (submittingRef.current) return;

    setCheckOut(value);
    setRoomCount(1);
    setReservation(null);
    resetBookingAttempt();
  }

  function changeCapacity(value) {
    if (submittingRef.current) return;

    setCapacity(value);
    setRoomCount(1);
    setReservation(null);
    resetBookingAttempt();
  }

  function changeRoomCount(value) {
    if (submittingRef.current) return;

    if (!Number.isInteger(value)) return;

    setRoomCount(
      Math.max(1, Math.min(value, Math.max(1, maxRooms)))
    );

    setReservation(null);
    resetBookingAttempt();
  }

  function refreshAvailability() {
    if (submittingRef.current) return;

    setRoomCount(1);
    setRefreshKey((value) => value + 1);
  }

  async function handleBooking() {
    if (
      submittingRef.current ||
      loading ||
      !availability ||
      !datesValid ||
      availableRooms < 1 ||
      roomCount < 1 ||
      roomCount > maxRooms ||
      reservation
    ) {
      return;
    }

    const payload = {
      checkIn,
      checkOut,
      capacity,
      roomCount,
    };

    const fingerprint = JSON.stringify(payload);

    if (
      !bookingAttemptRef.current ||
      bookingAttemptRef.current.fingerprint !== fingerprint
    ) {
      if (!globalThis.crypto?.randomUUID) {
        setBookingError(
          "UUID yaratib bo'lmadi. Saytni HTTPS yoki localhost orqali oching."
        );
        return;
      }

      bookingAttemptRef.current = {
        fingerprint,
        key: globalThis.crypto.randomUUID(),
      };
    }

    const idempotencyKey = bookingAttemptRef.current.key;

    submittingRef.current = true;
    setSubmitting(true);
    setBookingError("");

    try {
      const result = await createHostelBooking(
        payload,
        idempotencyKey
      );

      if (!result || result.id == null) {
        throw new Error(
          "Server bron natijasini noto'g'ri qaytardi."
        );
      }

      setReservation(result);
      bookingAttemptRef.current = null;
    } catch (error) {
      setBookingError(getErrorMessage(error));

      // Takroriy urinishda ayni UUID ishlatiladi.
      // Bunda backend idempotency'ni kafolatlashi kerak.
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }

  function handleNewBooking() {
    if (submittingRef.current) return;

    setReservation(null);
    setRoomCount(1);
    resetBookingAttempt();

    // Sanalar o'zgarmasa ham availability qayta olinadi.
    setRefreshKey((value) => value + 1);
  }

  const canBook =
    !submitting &&
    !loading &&
    Boolean(availability) &&
    datesValid &&
    availableRooms > 0 &&
    roomCount >= 1 &&
    roomCount <= maxRooms;

  return (
    <main className="hostel-page">
      <div className="hostel-container">
        <header className="hostel-hero">
          <span className="hostel-eyebrow">
            FC BUKHARA · SPORT & LIFESTYLE
          </span>

          <div className="hostel-hero-heading">
            <BedDouble size={38} />
            <h1>YOTOQXONA</h1>
          </div>

          <p>
            O'zingizga mos xonani tanlang va kerakli
            sanalar uchun bron qiling.
          </p>

          <div className="hostel-hero-features">
            <span>
              <ShieldCheck size={17} />
              Xavfsiz bron
            </span>

            <span>
              <CalendarDays size={17} />
              Sana bo'yicha bandlik
            </span>

            <span>
              <BedDouble size={17} />
              2–4 kishilik xonalar
            </span>
          </div>
        </header>

        {reservation ? (
          <section className="hostel-success">
            <CheckCircle2 size={52} />

            <h2>Bron yaratildi!</h2>

            <p>
              Xonalar vaqtincha siz uchun band qilindi.
              To'lov tasdiqlangach bron yakunlanadi.
            </p>

            <div className="hostel-reservation-info">
              <div>
                <span>Bron raqami</span>
                <strong>#{reservation.id}</strong>
              </div>

              <div>
                <span>Holati</span>
                <strong>{reservation.status}</strong>
              </div>

              <div>
                <span>Kirish sanasi</span>
                <strong>{reservation.check_in}</strong>
              </div>

              <div>
                <span>Chiqish sanasi</span>
                <strong>{reservation.check_out}</strong>
              </div>

              <div>
                <span>Kecha soni</span>
                <strong>{reservation.nights}</strong>
              </div>

              <div>
                <span>Umumiy narx</span>
                <strong>
                  {formatMoney(reservation.total_price)}
                </strong>
              </div>

              <div>
                <span>To'lov muddati</span>
                <strong>
                  {formatDateTime(
                    reservation.payment_expires_at
                  )}
                </strong>
              </div>
            </div>

            <h3>Ajratilgan xonalar</h3>

            <div className="hostel-booked-rooms">
              {(reservation.bookings || []).map(
                (booking) => (
                  <div key={booking.id}>
                    <BedDouble size={20} />

                    <span>
                      {booking.room_name ||
                        `Xona ${booking.room_number}`}
                    </span>

                    <strong>
                      {booking.capacity} kishilik
                    </strong>
                  </div>
                )
              )}
            </div>

            <div className="hostel-payment-note">
              <Clock3 size={19} />

              <span>
                Bronning to'lov muddati yuqorida
                ko'rsatilgan. To'lov integratsiyasi
                alohida bosqichda ulanadi.
              </span>
            </div>

            <button
              type="button"
              className="hostel-secondary-button"
              onClick={handleNewBooking}
            >
              Yangi bron qilish
            </button>
          </section>
        ) : (
          <div className="hostel-layout">
            <section className="hostel-booking-panel">
              <div className="hostel-section-title">
                <CalendarDays size={23} />

                <h2>
                  1. Yashash sanalarini tanlang
                </h2>
              </div>

              <div className="hostel-date-grid">
                <label>
                  <span>Kirish sanasi</span>

                  <input
                    type="date"
                    min={localDate()}
                    value={checkIn}
                    disabled={submitting}
                    onChange={(event) =>
                      changeCheckIn(event.target.value)
                    }
                  />
                </label>

                <label>
                  <span>Chiqish sanasi</span>

                  <input
                    type="date"
                    min={addDays(checkIn, 1)}
                    value={checkOut}
                    disabled={submitting}
                    onChange={(event) =>
                      changeCheckOut(event.target.value)
                    }
                  />
                </label>
              </div>

              <div className="hostel-section-title">
                <Users size={23} />

                <h2>
                  2. Xona sig'imini tanlang
                </h2>
              </div>

              {loading && (
                <div
                  className="hostel-notice"
                  role="status"
                >
                  <RefreshCw
                    size={18}
                    className="hostel-spin"
                  />

                  Bo'sh xonalar tekshirilmoqda...
                </div>
              )}

              {availabilityError && (
                <div
                  className="hostel-error"
                  role="alert"
                >
                  {availabilityError}
                </div>
              )}

              <div className="hostel-capacity-grid">
                {CAPACITIES.map((item) => {
                  const summary = getSummary(
                    availability,
                    item
                  );

                  const free = Number(
                    summary?.available_rooms ?? 0
                  );

                  return (
                    <button
                      key={item}
                      type="button"
                      disabled={
                        loading ||
                        submitting ||
                        !availability
                      }
                      className={
                        "hostel-capacity-card" +
                        (capacity === item
                          ? " selected"
                          : "")
                      }
                      aria-pressed={capacity === item}
                      onClick={() =>
                        changeCapacity(item)
                      }
                    >
                      <BedDouble size={26} />

                      <strong>
                        {item} kishilik
                      </strong>

                      <span>
                        {loading || !availability
                          ? "Tekshirilmoqda"
                          : `${free} ta bo'sh`}
                      </span>
                    </button>
                  );
                })}
              </div>

              <div className="hostel-stat-grid">
                <div className="hostel-stat-card">
                  <span>Jami xonalar</span>

                  <strong>
                    {loading || !availability
                      ? "—"
                      : totalRooms}
                  </strong>
                </div>

                <div className="hostel-stat-card">
                  <span>Bo'sh xonalar</span>

                  <strong>
                    {loading || !availability
                      ? "—"
                      : availableRooms}
                  </strong>
                </div>
              </div>

              <div className="hostel-section-title">
                <BedDouble size={23} />

                <h2>
                  3. Nechta xona bron qilasiz?
                </h2>
              </div>

              <div className="hostel-quantity">
                <button
                  type="button"
                  disabled={
                    submitting ||
                    loading ||
                    roomCount <= 1
                  }
                  onClick={() =>
                    changeRoomCount(
                      Math.max(1, roomCount - 1)
                    )
                  }
                  aria-label="Xona sonini kamaytirish"
                >
                  <Minus size={19} />
                </button>

                <strong>{roomCount}</strong>

                <button
                  type="button"
                  disabled={
                    submitting ||
                    loading ||
                    !availability ||
                    roomCount >= maxRooms
                  }
                  onClick={() =>
                    changeRoomCount(
                      Math.min(
                        maxRooms,
                        roomCount + 1
                      )
                    )
                  }
                  aria-label="Xona sonini oshirish"
                >
                  <Plus size={19} />
                </button>

                <span>
                  Maksimum: {maxRooms} ta xona
                </span>
              </div>

              {availability &&
                availableRooms === 0 && (
                  <div className="hostel-notice">
                    Tanlangan sig'imdagi barcha
                    xonalar ushbu sanalarda band.
                    Boshqa sana yoki sig'imni tanlang.
                  </div>
                )}

              {bookingError && (
                <div
                  className="hostel-error"
                  role="alert"
                >
                  {bookingError}
                </div>
              )}

              <button
                type="button"
                className="hostel-submit-button"
                onClick={handleBooking}
                disabled={!canBook}
              >
                {submitting
                  ? "Bron yaratilmoqda..."
                  : "Bron qilish"}
              </button>

              <button
                type="button"
                className="hostel-secondary-button"
                disabled={submitting || loading}
                onClick={refreshAvailability}
              >
                <RefreshCw size={16} />
                {" "}Bo'sh xonalarni yangilash
              </button>

              <p className="hostel-disclaimer">
                Bron yuborilganda server
                xonalar mavjudligini qayta
                tekshiradi.
              </p>
            </section>

            <aside className="hostel-side-panel">
              <h3>Mavjud xonalar</h3>

              <p>
                Tanlangan sanalar uchun
                {" "}{capacity} kishilik bo'sh xonalar.
              </p>

              {loading ? (
                <div className="hostel-notice">
                  Yuklanmoqda...
                </div>
              ) : selectedRooms.length === 0 ? (
                <div className="hostel-notice">
                  Hozircha bo'sh xona mavjud emas.
                </div>
              ) : (
                <div className="hostel-room-list">
                  {selectedRooms.map((room) => (
                    <div
                      className="hostel-room-item"
                      key={room.id}
                    >
                      <div className="hostel-room-icon">
                        <BedDouble size={24} />
                      </div>

                      <div>
                        <strong>
                          {room.name ||
                            `Xona ${room.number}`}
                        </strong>

                        <span>
                          {room.capacity} kishilik
                        </span>

                        {room.daily_price != null && (
                          <small>
                            {formatMoney(
                              room.daily_price
                            )}
                            {" / kecha"}
                          </small>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="hostel-side-footer">
                <ShieldCheck size={20} />

                <span>
                  Bo'sh xonalar soni real
                  bronlar asosida hisoblanadi.
                </span>
              </div>
            </aside>
          </div>
        )}
      </div>
    </main>
  );
}
