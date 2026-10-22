
import { useEffect, useRef, useState } from "react";
import { authFetch } from "../utils/auth";
import "./BoxingPage.css";

const API = "/api/v1/boxing";

function initialMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(
    now.getMonth() + 1
  ).padStart(2, "0")}`;
}

function formatPrice(value) {
  return new Intl.NumberFormat("uz-UZ").format(
    Number(value)
  );
}

function getError(data) {
  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (!data || typeof data !== "object") {
    return "Xatolik yuz berdi.";
  }

  return (
    Object.entries(data)
      .map(([key, value]) =>
        `${key}: ${
          Array.isArray(value)
            ? value.join(", ")
            : String(value)
        }`
      )
      .join(" | ") || "Xatolik yuz berdi."
  );
}

async function parseResponse(response) {
  const text = await response.text();

  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    throw new Error(
      `Server noto'g'ri javob qaytardi (${response.status}).`
    );
  }
}

export default function BoxingPage() {
  const [academies, setAcademies] = useState([]);
  const [selected, setSelected] = useState(null);
  const [month, setMonth] = useState(initialMonth());

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);

  const [subscription, setSubscription] = useState(null);
  const [payment, setPayment] = useState(null);

  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const bookingRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await fetch(`${API}/academies/`);
        const data = await parseResponse(response);

        if (!response.ok) {
          throw new Error(getError(data));
        }

        if (!cancelled) {
          const items = Array.isArray(data)
            ? data
            : data?.results || [];

          setAcademies(
            items.filter((item) => item.status === "active")
          );
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (selected && bookingRef.current) {
      bookingRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }, [selected]);

  function selectAcademy(academy) {
    setSelected(academy);
    setSubscription(null);
    setPayment(null);
    setError("");
    setNotice("");

    if (selected?.id === academy.id) {
      bookingRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }

  function changeMonth(value) {
    setMonth(value);
    setSubscription(null);
    setPayment(null);
    setError("");
    setNotice("");
  }

  async function createSubscription() {
    if (!selected || !month || submitting) return;

    if (month < initialMonth()) {
      setError("O'tgan oy uchun obuna yaratib bo'lmaydi.");
      return;
    }

    setSubmitting(true);
    setError("");
    setNotice("");
    setPayment(null);

    try {
      const response = await authFetch(
        `${API}/subscriptions/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            academy_id: selected.id,
            month: `${month}-01`,
          }),
        }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(getError(data));
      }

      setSubscription(data);
      setNotice(
        data.status === "paid"
          ? "Bu oy uchun obunangiz allaqachon to'langan."
          : "Oylik obuna tayyor. To'lov usulini tanlang."
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function startPayment(provider) {
    if (
      !subscription?.id ||
      subscription.status === "paid" ||
      paymentLoading
    ) return;

    setPaymentLoading(true);
    setError("");
    setNotice("");

    try {
      const response = await authFetch(
        `${API}/payments/demo/start/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            subscription_id: subscription.id,
            provider,
          }),
        }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(getError(data));
      }

      setPayment(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setPaymentLoading(false);
    }
  }

  async function completePayment(success) {
    if (!payment?.id || paymentLoading) return;

    setPaymentLoading(true);
    setError("");
    setNotice("");

    try {
      const response = await authFetch(
        `${API}/payments/demo/${payment.id}/complete/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ success }),
        }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(getError(data));
      }

      setPayment(data);

      if (data.status === "succeeded") {
        setSubscription((previous) => ({
          ...previous,
          status: "paid",
        }));
        setNotice("Demo to'lov muvaffaqiyatli tasdiqlandi.");
      } else {
        setNotice("Demo to'lov rad etildi.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setPaymentLoading(false);
    }
  }

  return (
    <main className="boxing-public">
      <section className="boxing-public-hero">
        <span>XUMO SPORT MAJMUASI</span>
        <h1>Boks akademiyasi</h1>
        <p>
          Professional boks mashg'ulotlariga oylik obuna
          bo'ling. Mashg'ulot kuni va vaqtini murabbiy
          bilan kelishasiz.
        </p>
      </section>

      {error && (
        <div className="boxing-public-error" role="alert">
          {error}
        </div>
      )}

      {notice && (
        <div className="boxing-public-notice" role="status">
          {notice}
        </div>
      )}

      {loading ? (
        <p>Akademiyalar yuklanmoqda...</p>
      ) : academies.length === 0 ? (
        <p>Hozircha faol boks akademiyasi mavjud emas.</p>
      ) : (
        <div className="boxing-public-grid">
          {academies.map((academy) => {
            const image =
              academy.images?.find(
                (item) => item.is_primary
              ) || academy.images?.[0];

            const isSelected = selected?.id === academy.id;

            return (
              <article
                key={academy.id}
                className={`boxing-public-card ${
                  isSelected ? "selected" : ""
                }`}
              >
                <div className="boxing-public-image-wrap">
                  {image ? (
                    <img
                      src={image.image}
                      alt={academy.name}
                      className="boxing-public-image"
                    />
                  ) : (
                    <div className="boxing-public-placeholder">
                      🥊
                    </div>
                  )}
                </div>

                <div className="boxing-public-content">
                  <h2>{academy.name}</h2>
                  <p>
                    {academy.description ||
                      "Professional boks mashg'ulotlari"}
                  </p>

                  <div className="boxing-public-price">
                    {formatPrice(academy.monthly_price)}
                    <small> so'm / oy</small>
                  </div>

                  <button
                    type="button"
                    onClick={() => selectAcademy(academy)}
                  >
                    {isSelected
                      ? "Tanlangan ✓"
                      : "Shu akademiyani tanlash"}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {selected && (
        <section
          ref={bookingRef}
          className="boxing-booking-box"
        >
          <h2>Oylik obuna</h2>

          <p>
            Tanlangan akademiya: <b>{selected.name}</b>
          </p>

          <label htmlFor="boxing-month">
            Qaysi oyga yozilmoqchisiz?
          </label>

          <input
            id="boxing-month"
            type="month"
            min={initialMonth()}
            value={month}
            onChange={(event) =>
              changeMonth(event.target.value)
            }
          />

          <div className="boxing-booking-total">
            <span>Oylik to'lov</span>
            <strong>
              {formatPrice(selected.monthly_price)} so'm
            </strong>
          </div>

          <p className="boxing-booking-note">
            Mashg'ulot kunlari va soatlari murabbiy
            bilan kelishiladi. Bir oyga bir nechta
            o'quvchi yozilishi mumkin.
          </p>

          <button
            type="button"
            className="boxing-main-button"
            disabled={submitting || paymentLoading || !month}
            onClick={createSubscription}
          >
            {submitting
              ? "Yaratilmoqda..."
              : "Oylik obuna yaratish"}
          </button>

          {subscription && (
            <div className="boxing-subscription-result">
              <h3>Obuna ma'lumotlari</h3>
              <p>Obuna ID: #{subscription.id}</p>
              <p>Oy: {subscription.month}</p>
              <p>
                Summa:{" "}
                {formatPrice(subscription.price_snapshot)} so'm
              </p>
              <p>
                Holati:{" "}
                <b>
                  {subscription.status === "paid"
                    ? "To'langan"
                    : "To'lov kutilmoqda"}
                </b>
              </p>
            </div>
          )}

          {subscription &&
            subscription.status === "pending_payment" && (
              <div className="boxing-payment-panel">
                <h3>To'lov usulini tanlang</h3>
                <p>
                  Test rejimi — haqiqiy pul yechilmaydi.
                </p>

                {!payment && (
                  <div className="boxing-payment-buttons">
                    <button
                      type="button"
                      disabled={paymentLoading}
                      onClick={() => startPayment("click")}
                    >
                      Click — demo
                    </button>

                    <button
                      type="button"
                      disabled={paymentLoading}
                      onClick={() => startPayment("payme")}
                    >
                      Payme — demo
                    </button>
                  </div>
                )}

                {payment?.status === "pending" && (
                  <div className="boxing-payment-confirm">
                    <h4>
                      {payment.provider === "click"
                        ? "Click"
                        : "Payme"}{" "}
                      demo to'lovi
                    </h4>

                    <p>
                      Summa:{" "}
                      {formatPrice(payment.amount)} so'm
                    </p>

                    <button
                      type="button"
                      disabled={paymentLoading}
                      onClick={() => completePayment(true)}
                    >
                      Test to'lovini tasdiqlash
                    </button>

                    <button
                      type="button"
                      disabled={paymentLoading}
                      onClick={() => completePayment(false)}
                    >
                      Test to'lovini rad etish
                    </button>
                  </div>
                )}

                {payment?.status === "failed" && (
                  <button
                    type="button"
                    onClick={() => setPayment(null)}
                  >
                    Qayta urinish
                  </button>
                )}
              </div>
            )}

          {subscription?.status === "paid" && (
            <div className="boxing-payment-success">
              <h3>To'lov muvaffaqiyatli!</h3>
              <p>
                Siz tanlagan oy uchun boks akademiyasiga
                yozildingiz.
              </p>
              <strong>
                DEMO TO'LOV — haqiqiy pul yechilmadi
              </strong>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
