
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  CalendarDays,
  UsersRound,
  Ticket,
  ArrowLeft,
} from "lucide-react";

import "./Competitions.css";

export default function CompetitionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [competition, setCompetition] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadCompetition() {
      setLoading(true);
      setError("");
      setCompetition(null);

      try {
        const response = await fetch(
          `/api/v1/competitions/${encodeURIComponent(id)}/`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(
            response.status === 404
              ? "Musobaqa topilmadi."
              : "Musobaqa ma’lumotlarini yuklab bo‘lmadi."
          );
        }

        const data = await response.json();

        if (!controller.signal.aborted) {
          setCompetition(data);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadCompetition();

    return () => controller.abort();
  }, [id]);

  function handleBuyTicket() {
    const token = sessionStorage.getItem("access_token");

    const destination = `/competitions/${id}/checkout`;

    if (!token) {
      navigate(`/login?next=${encodeURIComponent(destination)}`);
      return;
    }

    navigate(destination);
  }

  if (loading) {
    return (
      <main className="competition-detail">
        <p>Musobaqa yuklanmoqda...</p>
      </main>
    );
  }

  if (error || !competition) {
    return (
      <main className="competition-detail">
        <p role="alert">{error || "Musobaqa topilmadi."}</p>
        <Link to="/competitions">Musobaqalarga qaytish</Link>
      </main>
    );
  }

  return (
    <main className="competition-detail">
      <div className="competitions-container">
        <Link
          to="/competitions"
          className="competition-back"
        >
          <ArrowLeft size={18} />
          Musobaqalarga qaytish
        </Link>

        <div className="competition-detail-banner">
          {competition.banner && (
            <img
              src={competition.banner}
              alt={competition.name}
            />
          )}

          <div className="competition-detail-overlay">
            <span>FC BUKHARA · COMPETITION</span>
            <h1>{competition.name}</h1>
          </div>
        </div>

        <div className="competition-detail-content">
          <div className="competition-detail-info">
            <h2>Musobaqa haqida</h2>

            <p>{competition.description}</p>

            <div className="competition-facts">
              <div>
                <CalendarDays />
                <span>
                  {new Date(
                    competition.start_time
                  ).toLocaleString("uz-UZ", {
                    dateStyle: "long",
                    timeStyle: "short",
                    timeZone: "Asia/Tashkent",
                  })}
                </span>
              </div>

              <div>
                <UsersRound />
                <span>
                  {competition.min_age}–
                  {competition.max_age} yosh
                </span>
              </div>
            </div>
          </div>

          <aside className="competition-ticket-panel">
            <span>CHIPTA NARXI</span>

            <strong>
              {Number(competition.price).toLocaleString(
                "uz-UZ"
              )}{" "}
              so‘m
            </strong>

            <button
              type="button"
              onClick={handleBuyTicket}
            >
              <Ticket size={20} />
              Chipta sotib olish
            </button>

            <small>
              Chipta xarid qilish uchun login talab etiladi.
            </small>
          </aside>
        </div>
      </div>
    </main>
  );
}
