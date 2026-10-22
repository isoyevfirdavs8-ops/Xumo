
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  CalendarDays,
  Plus,
  Pencil,
  Trash2,
  Ticket,
  Users,
  RefreshCw,
} from "lucide-react";

import "./Competition.css";

const API_URL = "/api/v1/dashboard/competitions/";

function formatPrice(value) {
  return `${Number(value).toLocaleString("uz-UZ")} so‘m`;
}

function formatDate(value) {
  if (!value) return "—";

  return new Date(value).toLocaleString("uz-UZ", {
    timeZone: "Asia/Tashkent",
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function CompetitionList() {
  const [competitions, setCompetitions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  const loadCompetitions = useCallback(async (signal) => {
    try {
      setLoading(true);
      setError("");

      const token = sessionStorage.getItem("access_token");

      if (!token) {
        throw new Error("Avval tizimga kiring.");
      }

      const response = await fetch(API_URL, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal,
      });

      if (!response.ok) {
        throw new Error(
          `Musobaqalarni olishda xatolik: HTTP ${response.status}`
        );
      }

      const data = await response.json();

      if (!signal?.aborted) {
        setCompetitions(
          Array.isArray(data)
            ? data
            : Array.isArray(data?.results)
              ? data.results
              : []
        );
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message);
      }
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadCompetitions(controller.signal);

    return () => controller.abort();
  }, [loadCompetitions]);

  async function handleDelete(competition) {
    const confirmed = window.confirm(
      `"${competition.name}" musobaqasini o‘chirmoqchimisiz?\n\n` +
      "Agar chiptalar sotilgan bo‘lsa, uni o‘chirish o‘rniga " +
      "nofaol holatga o‘tkazing."
    );

    if (!confirmed) return;

    const token = sessionStorage.getItem("access_token");

    if (!token) {
      setError("Avval tizimga kiring.");
      return;
    }

    try {
      setDeletingId(competition.id);
      setError("");

      const response = await fetch(
        `${API_URL}${competition.id}/`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          response.status === 409
            ? "Bu musobaqaga buyurtmalar bog‘langan. Uni nofaol qiling."
            : `O‘chirishda xatolik: HTTP ${response.status}`
        );
      }

      setCompetitions((previous) =>
        previous.filter((item) => item.id !== competition.id)
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  }

  const activeCount = competitions.filter(
    (item) => item.is_active
  ).length;

  return (
    <div className="dc-page">
      <div className="dc-page-header">
        <div>
          <span className="dc-eyebrow">
            FC BUKHARA / DASHBOARD
          </span>
          <h1>Musobaqalar</h1>
          <p>
            Musobaqalar, bannerlar va chipta narxlarini
            boshqaring.
          </p>
        </div>

        <Link
          to="/dashboard/competitions/create"
          className="dc-primary-button"
        >
          <Plus size={19} />
          Yangi musobaqa
        </Link>
      </div>

      <div className="dc-stats">
        <div className="dc-stat">
          <span>Jami musobaqalar</span>
          <strong>{competitions.length}</strong>
        </div>

        <div className="dc-stat">
          <span>Faol musobaqalar</span>
          <strong>{activeCount}</strong>
        </div>
      </div>

      <div className="dc-toolbar">
        <h2>Musobaqalar ro‘yxati</h2>

        <button
          type="button"
          className="dc-icon-button"
          onClick={() => loadCompetitions()}
          disabled={loading}
          title="Yangilash"
        >
          <RefreshCw size={18} />
        </button>
      </div>

      {error && (
        <div className="dc-error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <div className="dc-empty">
          Musobaqalar yuklanmoqda...
        </div>
      ) : competitions.length === 0 ? (
        <div className="dc-empty">
          Hozircha musobaqalar mavjud emas.
        </div>
      ) : (
        <div className="dc-list">
          {competitions.map((competition) => (
            <article
              className="dc-competition-card"
              key={competition.id}
            >
              <div className="dc-card-image">
                {competition.banner ? (
                  <img
                    src={competition.banner}
                    alt={competition.name}
                  />
                ) : (
                  <Ticket size={48} />
                )}
              </div>

              <div className="dc-card-body">
                <div className="dc-card-heading">
                  <h3>{competition.name}</h3>

                  <span
                    className={
                      competition.is_active
                        ? "dc-status dc-status-active"
                        : "dc-status dc-status-inactive"
                    }
                  >
                    {competition.is_active
                      ? "Faol"
                      : "Nofaol"}
                  </span>
                </div>

                <p className="dc-description">
                  {competition.description}
                </p>

                <div className="dc-card-meta">
                  <span>
                    <CalendarDays size={16} />
                    {formatDate(competition.start_time)}
                  </span>

                  <span>
                    <Users size={16} />
                    {competition.min_age}–
                    {competition.max_age} yosh
                  </span>

                  <span>
                    <Ticket size={16} />
                    {formatPrice(competition.price)}
                  </span>

                  <span>
                    Sig‘im: {competition.capacity} ta
                  </span>
                </div>

                <div className="dc-card-actions">
                  <Link
                    to={`/dashboard/competitions/${competition.id}/edit`}
                    className="dc-edit-button"
                  >
                    <Pencil size={16} />
                    Tahrirlash
                  </Link>

                  <button
                    type="button"
                    className="dc-delete-button"
                    disabled={deletingId === competition.id}
                    onClick={() => handleDelete(competition)}
                  >
                    <Trash2 size={16} />
                    {deletingId === competition.id
                      ? "O‘chirilmoqda..."
                      : "O‘chirish"}
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
