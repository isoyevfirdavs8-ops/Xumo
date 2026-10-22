
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CalendarDays, Ticket } from "lucide-react";

import "./Competitions.css";

export default function CompetitionsPage() {
  const [competitions, setCompetitions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadCompetitions() {
      try {
        const response = await fetch("/api/v1/competitions/", {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("Musobaqalarni yuklab bo‘lmadi.");
        }

        const data = await response.json();

        if (!controller.signal.aborted) {
          setCompetitions(
            Array.isArray(data)
              ? data
              : Array.isArray(data?.results)
                ? data.results
                : []
          );
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

    loadCompetitions();

    return () => controller.abort();
  }, []);

  return (
    <main className="competitions-page">
      <div className="competitions-container">
        <div className="competitions-heading">
          <span>FC BUKHARA · EVENTS</span>
          <h1>YAQINLASHAYOTGAN MUSOBAQALAR</h1>
          <p>
            Eng qiziqarli sport musobaqalari va turnirlar
            bilan tanishing.
          </p>
        </div>

        {loading && <p>Musobaqalar yuklanmoqda...</p>}

        {error && <p role="alert">{error}</p>}

        {!loading && !error && competitions.length === 0 && (
          <p>Hozircha yaqinlashayotgan musobaqalar mavjud emas.</p>
        )}

        <div className="competitions-grid">
          {competitions.map((competition) => (
            <article
              key={competition.id}
              className="competition-card"
            >
              <Link to={`/competitions/${competition.id}`}>
                {competition.banner && (
                  <img
                    src={competition.banner}
                    alt={competition.name}
                    className="competition-card-image"
                  />
                )}
              </Link>

              <div className="competition-card-body">
                <div className="competition-date">
                  <CalendarDays size={17} />
                  {new Date(
                    competition.start_time
                  ).toLocaleString("uz-UZ", {
                    dateStyle: "medium",
                    timeStyle: "short",
                    timeZone: "Asia/Tashkent",
                  })}
                </div>

                <h2>{competition.name}</h2>

                <p className="competition-description">
                  {competition.description}
                </p>

                <div className="competition-price">
                  <Ticket size={18} />
                  {Number(competition.price).toLocaleString(
                    "uz-UZ"
                  )}{" "}
                  so‘m
                </div>

                <Link
                  className="competition-button"
                  to={`/competitions/${competition.id}`}
                >
                  Batafsil ko‘rish →
                </Link>
              </div>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
