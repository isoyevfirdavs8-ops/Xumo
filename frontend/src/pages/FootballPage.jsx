import FootballAcademySection from "../components/football/FootballAcademySection";
import { useEffect, useState } from "react";
import { authFetch } from "../utils/auth";
import "./FootballPage.css";

const API = "/api/v1/football";

function formatMoney(value) {
  return new Intl.NumberFormat("uz-UZ").format(Number(value));
}

export default function FootballPage() {
  const [fields, setFields] = useState([]);
  const [selectedField, setSelectedField] = useState(null);
  const [selectedDate, setSelectedDate] = useState(() => {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Tashkent",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).formatToParts(new Date());

    const get = (type) =>
      parts.find((part) => part.type === type)?.value;

    return `${get("year")}-${get("month")}-${get("day")}`;
  });

  const [slots, setSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [loading, setLoading] = useState(false);
  const [booking, setBooking] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadFields() {
      try {
        const response = await fetch(`${API}/fields/`);
        if (!response.ok) throw new Error("Stadionlar yuklanmadi.");

        const data = await response.json();
        const items = Array.isArray(data) ? data : data.results || [];

        if (!cancelled) {
          setFields(items);
          setSelectedField(items[0] || null);
        }
      } catch (error) {
        if (!cancelled) setMessage(error.message);
      }
    }

    loadFields();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!selectedField) return;

    const controller = new AbortController();

    async function loadSlots() {
      setLoading(true);
      setSlots([]);
      setSelectedSlot(null);
      setMessage("");

      try {
        const params = new URLSearchParams({
          field_id: String(selectedField.id),
          date: selectedDate,
        });

        const response = await fetch(
          `${API}/availability/?${params}`,
          { signal: controller.signal }
        );

        if (!response.ok) throw new Error("Vaqtlar yuklanmadi.");

        const data = await response.json();
        setSlots(data.slots || []);
      } catch (error) {
        if (error.name !== "AbortError") {
          setMessage(error.message);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    loadSlots();
    return () => controller.abort();
  }, [selectedField, selectedDate]);

  async function handleBooking() {
    if (!selectedField || !selectedSlot || booking) return;

    setBooking(true);
    setMessage("");

    try {
      const response = await authFetch(`${API}/bookings/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          field_id: selectedField.id,
          start_at: selectedSlot.start,
          end_at: selectedSlot.end,
        }),
      });

      if (response.status === 401) {
        setMessage("Bron qilish uchun tizimga kiring.");
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          Array.isArray(data.detail)
            ? data.detail.join(" ")
            : data.detail || "Bron yaratishda xatolik."
        );
      }

      setMessage(
        `Bron №${data.id} yaratildi. To‘lov uchun 10 daqiqa berildi.`
      );

      setSelectedSlot(null);

      const params = new URLSearchParams({
        field_id: String(selectedField.id),
        date: selectedDate,
      });

      const availabilityResponse = await fetch(
        `${API}/availability/?${params}`
      );

      if (availabilityResponse.ok) {
        const updated = await availabilityResponse.json();
        setSlots(updated.slots || []);
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBooking(false);
    }
  }

  return (
    <main className="football-page">
      <div className="football-container">
        <div className="football-heading">
          <span> XUMO SPORT MAJMUASI </span>
          <h1>Futbol maydonlari</h1>
          <p>Maydonni, sanani va bo‘sh vaqtni tanlang.</p>
        </div>

        <div className="football-fields">
          {fields.map((field) => (
            <button
              key={field.id}
              type="button"
              className={`football-field-card ${
                selectedField?.id === field.id ? "selected" : ""
              }`}
              onClick={() => setSelectedField(field)}
            >
              {field.images?.[0]?.image ? (
                <img
                  src={field.images[0].image}
                  alt={field.name}
                />
              ) : (
                <div className="football-field-placeholder">
                  ⚽
                </div>
              )}

              <div className="football-field-content">
                <strong>{field.name}</strong>
                <span>
                  {field.field_type === "winter"
                    ? "Qishki maydon"
                    : "Yozgi maydon"}
                </span>
                <b>{formatMoney(field.hourly_price)} so‘m / soat</b>
              </div>
            </button>
          ))}
        </div>

        {selectedField && (
          <section className="football-booking-panel">
            <div className="football-panel-top">
              <div>
                <h2>{selectedField.name}</h2>
                <p>16:00–20:00 oralig‘ida bron yopiq.</p>
              </div>

              <label>
                Sana
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                />
              </label>
            </div>

            {loading ? (
              <p>Vaqtlar yuklanmoqda...</p>
            ) : (
              <div className="football-slots">
                {slots.map((slot) => {
                  const start = new Date(slot.start);
                  const label = start.toLocaleTimeString("uz-UZ", {
                    timeZone: "Asia/Tashkent",
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false,
                  });

                  const selected =
                    selectedSlot?.start === slot.start;

                  return (
                    <button
                      key={slot.start}
                      type="button"
                      disabled={slot.status !== "available"}
                      className={`football-slot ${slot.status} ${
                        selected ? "selected" : ""
                      }`}
                      onClick={() => setSelectedSlot(slot)}
                    >
                      <strong>{label}</strong>
                      <span>
                        {slot.status === "available"
                          ? "Bo‘sh"
                          : slot.status === "booked"
                          ? "Band"
                          : slot.status === "closed"
                          ? "Yopiq"
                          : "O‘tgan"}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}

            <div className="football-booking-bottom">
              <div>
                <span>Bron narxi</span>
                <strong>
                  {formatMoney(selectedField.hourly_price)} so‘m
                </strong>
              </div>

              <button
                type="button"
                disabled={!selectedSlot || booking}
                onClick={handleBooking}
              >
                {booking ? "Bron qilinmoqda..." : "Bron qilish"}
              </button>
            </div>


          {message && (
            <p className="football-message" role="status">
              {message}
            </p>
          )}
        </section>
      )}

      {/* Futbol akademiyasi — bron qilishdan keyin */}
      <FootballAcademySection />

    </div>
  </main>
);
}

