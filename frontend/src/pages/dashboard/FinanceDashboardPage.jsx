
import { useEffect, useState } from "react";
import {
  Wallet,
  CalendarDays,
  Receipt,
  RotateCcw,
  RefreshCw,
} from "lucide-react";
import { authFetch } from "../../utils/auth";
import "./FinanceDashboardPage.css";

const API = "/api/v1/finance/revenue/";

const LABELS = {
  football: "Futbol",
  tennis: "Tennis",
  boxing: "Boks",
  restaurant: "Restoran",
  tournament: "Musobaqalar",
};

function formatMoney(value) {
  return (
    new Intl.NumberFormat("uz-UZ", {
      maximumFractionDigits: 2,
    }).format(Number(value || 0)) + " so'm"
  );
}

function localDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function firstDayOfMonth() {
  const now = new Date();
  return localDate(
    new Date(now.getFullYear(), now.getMonth(), 1)
  );
}

export default function FinanceDashboardPage() {
  const [start, setStart] = useState(firstDayOfMonth);
  const [end, setEnd] = useState(() => localDate(new Date()));
  const [filters, setFilters] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadRevenue(nextFilters) {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams();

      if (nextFilters.start) {
        params.set("start", nextFilters.start);
      }
      if (nextFilters.end) {
        params.set("end", nextFilters.end);
      }

      const response = await authFetch(
        `${API}?${params.toString()}`
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string"
            ? result.detail
            : "Statistikani yuklab bo'lmadi."
        );
      }

      setData(result);
    } catch (err) {
      setError(err.message || "Server bilan aloqa yo'q.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const initial = {
      start: firstDayOfMonth(),
      end: localDate(new Date()),
    };
    setFilters(initial);
    loadRevenue(initial);
  }, []);

  function applyFilters(event) {
    event.preventDefault();

    if (start && end && start > end) {
      setError("Sana oralig'i noto'g'ri.");
      return;
    }

    const next = { start, end };
    setFilters(next);
    loadRevenue(next);
  }

  const categories = data?.categories || [];
  const total = Number(data?.total_revenue || 0);

  return (
    <main className="finance-dashboard">
      <header className="finance-heading">
        <div>
          <span>XUMO SPORT MAJMUASI</span>
          <h1>Moliyaviy statistika</h1>
          <p>
            Tasdiqlangan tushumlar va yo'nalishlar
            bo'yicha moliyaviy nazorat
          </p>
        </div>

        <button
          type="button"
          onClick={() => loadRevenue(
            filters || { start, end }
          )}
          disabled={loading}
          className="finance-refresh"
        >
          <RefreshCw size={17} />
          Yangilash
        </button>
      </header>

      <form
        className="finance-filters"
        onSubmit={applyFilters}
      >
        <label>
          Boshlanish sanasi
          <input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>

        <label>
          Tugash sanasi
          <input
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>

        <button type="submit" disabled={loading}>
          Ko'rsatish
        </button>

        <button
          type="button"
          className="finance-clear"
          onClick={() => {
            setStart("");
            setEnd("");
            setFilters({ start: "", end: "" });
            loadRevenue({ start: "", end: "" });
          }}
        >
          Barcha davr
        </button>
      </form>

      {error && (
        <div className="finance-error" role="alert">
          {error}
        </div>
      )}

      {loading && (
        <p className="finance-loading">
          Statistika yuklanmoqda...
        </p>
      )}

      {data && (
        <>
          <section className="finance-kpis">
            <div className="finance-kpi featured">
              <Wallet size={23} />
              <span>Umumiy haqiqiy tushum</span>
              <strong>
                {formatMoney(data.total_revenue)}
              </strong>
              <small>
                Moliyaviy reyestr bo'yicha
              </small>
            </div>

            <div className="finance-kpi">
              <Receipt size={23} />
              <span>To'lov yozuvlari</span>
              <strong>{data.payment_count}</strong>
              <small>Reyestrdagi to'lovlar</small>
            </div>

            <div className="finance-kpi">
              <RotateCcw size={23} />
              <span>Qaytarish yozuvlari</span>
              <strong>{data.refund_count}</strong>
              <small>Refund operatsiyalari</small>
            </div>

            <div className="finance-kpi">
              <CalendarDays size={23} />
              <span>O'rtacha tushum</span>
              <strong>
                {formatMoney(
                  data.payment_count
                    ? total / data.payment_count
                    : 0
                )}
              </strong>
              <small>
                Qaytarishlar chegirilgan o'rtacha
              </small>
            </div>
          </section>

          <section className="finance-panel">
            <div className="finance-panel-heading">
              <h2>Yo'nalishlar bo'yicha tushum</h2>
              <p>Moliyaviy reyestr asosida</p>
            </div>

            <div className="finance-bars">
              {categories.map((item) => {
                const amount = Number(item.revenue);
                const positiveTotal = categories.reduce(
                  (sum, category) =>
                    sum + Math.max(
                      0,
                      Number(category.revenue)
                    ),
                  0
                );
                const percent = positiveTotal > 0
                  ? (Math.max(0, amount) / positiveTotal) * 100
                  : 0;

                return (
                  <div
                    className="finance-bar-row"
                    key={item.key}
                  >
                    <div className="finance-bar-label">
                      <strong>{item.name}</strong>
                      <span>
                        {formatMoney(item.revenue)}
                      </span>
                    </div>
                    <div className="finance-bar-track">
                      <div
                        className={`finance-bar-fill ${item.key}`}
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="finance-panel">
            <div className="finance-panel-heading">
              <h2>Mavjud modellar bo'yicha nazorat</h2>
              <p>
                Quyidagi summalar haqiqiy tushumga
                avtomatik qo'shilmaydi.
              </p>
            </div>

            <div className="finance-source-grid">
              {Object.entries(
                data.source_overview || {}
              ).map(([key, item]) => (
                <article
                  className="finance-source-card"
                  key={key}
                >
                  <h3>{LABELS[key] || key}</h3>
                  <strong>
                    {formatMoney(item.amount)}
                  </strong>
                  <p>{item.count} ta yozuv</p>
                  <small>{item.description}</small>
                </article>
              ))}
            </div>
          </section>
        </>
      )}
    </main>
  );
}
