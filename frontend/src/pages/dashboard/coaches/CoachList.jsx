
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Plus,
  Pencil,
  Trash2,
  UserRound,
  BriefcaseBusiness,
} from "lucide-react";

import "./Coach.css";

const API_URL = "/api/v1/dashboard/coaches/";

export default function CoachList() {
  const [coaches, setCoaches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadCoaches() {
      try {
        const token = sessionStorage.getItem("access_token");

        const response = await fetch(API_URL, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(
            `Murabbiylarni yuklashda xatolik: HTTP ${response.status}`
          );
        }

        const data = await response.json();

        if (!controller.signal.aborted) {
          setCoaches(
            Array.isArray(data) ? data : data.results || []
          );
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadCoaches();

    return () => controller.abort();
  }, []);

  async function handleDelete(coach) {
    const confirmed = window.confirm(
      `"${coach.full_name}" murabbiyini o‘chirmoqchimisiz?`
    );

    if (!confirmed) return;

    setDeletingId(coach.id);
    setError("");

    try {
      const token = sessionStorage.getItem("access_token");

      const response = await fetch(
        `${API_URL}${coach.id}/`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          `Murabbiyni o‘chirishda xatolik: HTTP ${response.status}`
        );
      }

      setCoaches((prev) =>
        prev.filter((item) => item.id !== coach.id)
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="coach-dashboard">
      <div className="dashboard-page-heading">
        <div>
          <h1>Murabbiylar</h1>
          <p className="coach-page-subtitle">
            FC BUKHARA professional murabbiylarini boshqarish
          </p>
        </div>

        <Link
          to="/dashboard/coaches/create"
          className="dashboard-primary-btn"
        >
          <Plus size={18} />
          Murabbiy qo‘shish
        </Link>
      </div>

      {error && (
        <div className="coach-error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <div className="dashboard-card">
          Murabbiylar yuklanmoqda...
        </div>
      ) : coaches.length === 0 && !error ? (
        <div className="coach-empty">
          <UserRound size={44} />
          <h2>Hozircha murabbiylar yo‘q</h2>
          <p>Birinchi murabbiyni qo‘shing.</p>
        </div>
      ) : (
        <div className="coach-admin-grid">
          {coaches.map((coach) => (
            <article
              key={coach.id}
              className="coach-admin-card"
            >
              <div className="coach-admin-image">
                {coach.image ? (
                  <img
                    src={coach.image}
                    alt={coach.full_name}
                    loading="lazy"
                  />
                ) : (
                  <UserRound size={48} />
                )}

                <span
                  className={`coach-status ${
                    coach.is_active ? "active" : "inactive"
                  }`}
                >
                  {coach.is_active ? "Faol" : "Nofaol"}
                </span>
              </div>

              <div className="coach-admin-body">
                <span className="coach-category-label">
                  {coach.category_name}
                </span>

                <h2>{coach.full_name}</h2>

                <p className="coach-specialization">
                  {coach.specialization}
                </p>

                <div className="coach-experience">
                  <BriefcaseBusiness size={16} />
                  {coach.experience_years} yillik tajriba
                </div>

                <p className="coach-bio">
                  {coach.bio || "Biografiya kiritilmagan."}
                </p>

                <div className="coach-admin-actions">
                  <Link
                    to={`/dashboard/coaches/${coach.id}/edit`}
                    className="coach-edit-btn"
                  >
                    <Pencil size={16} />
                    Tahrirlash
                  </Link>

                  <button
                    type="button"
                    className="coach-delete-btn"
                    onClick={() => handleDelete(coach)}
                    disabled={deletingId === coach.id}
                  >
                    <Trash2 size={16} />
                    {deletingId === coach.id
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
