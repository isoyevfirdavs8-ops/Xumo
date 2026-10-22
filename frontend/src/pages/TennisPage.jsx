import { useEffect, useRef, useState } from "react";
import { authFetch } from "../utils/auth";
import "./TennisPage.css";

const COURTS_API = "/api/v1/tennis/courts/";
const SUBSCRIPTIONS_API = "/api/v1/tennis/subscriptions/";
const DEMO_START_API = "/api/v1/tennis/payments/demo/start/";

function currentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function formatPrice(value) {
  return new Intl.NumberFormat("uz-UZ").format(Number(value || 0));
}

function errorText(data, fallback = "So‘rov bajarilmadi.") {
  if (typeof data?.detail === "string") return data.detail;
  if (typeof data === "string") return data;
  if (data && typeof data === "object") {
    const message = Object.entries(data)
      .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(", ") : String(errors)}`)
      .join(" | ");
    if (message) return message;
  }
  return fallback;
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  let data = null;
  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    const text = await response.text();
    data = text ? { detail: text.slice(0, 250) } : {};
  }
  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Obuna uchun tizimga kiring (login qiling).");
    }
    throw new Error(errorText(data, `HTTP ${response.status}`));
  }
  return data;
}

export default function TennisPage() {
  const [courts, setCourts] = useState([]);
  const [selectedCourt, setSelectedCourt] = useState(null);
  const [month, setMonth] = useState(currentMonth);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [payment, setPayment] = useState(null);
  const bookingRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    async function loadCourts() {
      try {
        const response = await fetch(COURTS_API, { signal: controller.signal });
        const data = await parseResponse(response);
        setCourts(Array.isArray(data) ? data : data.results || []);
      } catch (err) {
        if (err.name !== "AbortError") setError(err.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    loadCourts();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (selectedCourt && bookingRef.current) {
      bookingRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [selectedCourt]);

  function selectCourt(court) {
    setSelectedCourt(court);
    setResult(null);
    setPayment(null);
    setError("");
    // Already selected: effect won't rerun, so scroll explicitly.
    if (selectedCourt?.id === court.id) {
      bookingRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function changeMonth(value) {
    setMonth(value);
    setResult(null);
    setPayment(null);
    setError("");
  }

  async function createSubscription() {
    if (!selectedCourt || !month || submitting || paymentLoading) return;
    setSubmitting(true);
    setError("");
    setResult(null);
    setPayment(null);
    try {
      const response = await authFetch(SUBSCRIPTIONS_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ court_id: selectedCourt.id, month: `${month}-01` }),
      });
      const data = await parseResponse(response);
      const subscription = data.subscription || data;
      if (!subscription?.id) throw new Error("Server obuna ID sini qaytarmadi.");
      setResult(subscription);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function startDemoPayment(provider) {
    if (!result?.id || result.status === "paid" || paymentLoading) return;
    setPaymentLoading(true);
    setError("");
    try {
      const response = await authFetch(DEMO_START_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subscription_id: result.id, provider }),
      });
      setPayment(await parseResponse(response));
    } catch (err) {
      setError(err.message);
    } finally {
      setPaymentLoading(false);
    }
  }

  async function finishDemoPayment(success) {
    if (!payment?.id || payment.status !== "pending" || paymentLoading) return;
    setPaymentLoading(true);
    setError("");
    try {
      const response = await authFetch(
        `/api/v1/tennis/payments/demo/${payment.id}/complete/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ success }),
        }
      );
      const data = await parseResponse(response);
      setPayment(data);
      if (data.status === "succeeded") {
        setResult((previous) => previous ? { ...previous, status: "paid" } : previous);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setPaymentLoading(false);
    }
  }

  return (
    <main className="tennis-page">
      <div className="tennis-hero">
        <span>XUMO SPORT MAJMUASI</span>
        <h1>Tennis akademiyasi</h1>
        <p>
          Tennis kortini tanlang va oylik mashg‘ulotlarga yoziling.
          Mashg‘ulot kuni va vaqtini murabbiy bilan kelishib olasiz.
        </p>
      </div>

      {error && <div className="tennis-page-error" role="alert">{error}</div>}

      {loading ? (
        <p>Kortlar yuklanmoqda...</p>
      ) : courts.length === 0 ? (
        <p>Hozircha faol tennis kortlari mavjud emas.</p>
      ) : (
        <div className="tennis-public-grid">
          {courts.map((court) => {
            const image = court.images?.find((img) => img.is_primary) || court.images?.[0];
            const selected = selectedCourt?.id === court.id;
            return (
              <article
                key={court.id}
                className={`tennis-public-card ${selected ? "selected" : ""}`}
              >
                {image ? (
                  <img src={image.image} alt={court.name} className="tennis-public-image" />
                ) : (
                  <div className="tennis-public-placeholder">🎾</div>
                )}
                <div className="tennis-public-content">
                  <h2>{court.name}</h2>
                  <p>{court.description || "Tennis akademiyasi mashg‘ulotlari"}</p>
                  <div className="tennis-public-price">
                    {formatPrice(court.monthly_price)}<small> so‘m / oy</small>
                  </div>
                  <button type="button" onClick={() => selectCourt(court)}>
                    {selected ? "Tanlangan ✓ — obunaga o‘tish" : "Shu kortni tanlash"}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {selectedCourt && (
        <section ref={bookingRef} className="tennis-booking-box" style={{ scrollMarginTop: 110 }}>
          <h2>Oylik obuna</h2>
          <p>Tanlangan kort: <b>{selectedCourt.name}</b></p>
          <label htmlFor="tennis-month">Qaysi oyga yozilmoqchisiz?</label>
          <input
            id="tennis-month"
            type="month"
            min={currentMonth()}
            value={month}
            onChange={(event) => changeMonth(event.target.value)}
          />
          <div className="tennis-booking-total">
            To‘lov summasi:
            <strong>{formatPrice(selectedCourt.monthly_price)} so‘m</strong>
          </div>
          <p className="tennis-booking-note">
            Mashg‘ulot kunlari va soatlari murabbiy bilan kelishiladi.
            Bir oyga bir nechta o‘quvchi yozilishi mumkin.
          </p>
          <button
            type="button"
            onClick={createSubscription}
            disabled={submitting || paymentLoading || !month || result?.status === "paid"}
          >
            {submitting ? "Yuborilmoqda..." : result?.status === "paid" ? "Obuna to‘langan" : "Oylik obuna yaratish"}
          </button>

          {result && (
            <div className="tennis-booking-result">
              <strong>Oylik obuna ma’lumotlari</strong>
              <p>Obuna ID: #{result.id}</p>
              <p>Holati: {result.status === "paid" ? "To‘langan" : "To‘lov kutilmoqda"}</p>
              <p>Obuna summasi: {formatPrice(result.price_snapshot)} so‘m</p>
            </div>
          )}

          {result && result.status !== "paid" && (
            <div className="tennis-payment-section">
              <h3>To‘lov usulini tanlang</h3>
              <p>Bu demo rejim: haqiqiy pul yechilmaydi.</p>
              {!payment && (
                <div className="tennis-payment-methods">
                  <button type="button" disabled={paymentLoading} onClick={() => startDemoPayment("click")}>
                    Click orqali test to‘lov
                  </button>
                  <button type="button" disabled={paymentLoading} onClick={() => startDemoPayment("payme")}>
                    Payme orqali test to‘lov
                  </button>
                </div>
              )}
              {payment?.status === "pending" && (
                <div className="tennis-payment-confirm">
                  <h4>{payment.provider === "click" ? "Click" : "Payme"} — demo to‘lov</h4>
                  <p>Summa: {formatPrice(payment.amount)} so‘m</p>
                  <button type="button" disabled={paymentLoading} onClick={() => finishDemoPayment(true)}>
                    Test to‘lovini tasdiqlash
                  </button>
                  <button type="button" disabled={paymentLoading} onClick={() => finishDemoPayment(false)}>
                    Test to‘lovini rad etish
                  </button>
                </div>
              )}
              {payment?.status === "failed" && (
                <div>
                  <p>Test to‘lovi muvaffaqiyatsiz yakunlandi.</p>
                  <button type="button" disabled={paymentLoading} onClick={() => setPayment(null)}>
                    Qayta urinish
                  </button>
                </div>
              )}
            </div>
          )}

          {result?.status === "paid" && (
            <div className="tennis-payment-success" role="status">
              <h3>To‘lov muvaffaqiyatli!</h3>
              <p>Siz tanlagan oy uchun tennis akademiyasiga yozildingiz.</p>
              <p>Mashg‘ulot kunlari va vaqtini murabbiy bilan kelishib olasiz.</p>
              <strong>TEST TO‘LOVI — haqiqiy pul yechilmadi</strong>
            </div>
          )}
        </section>
      )}
    </main>
  );
}