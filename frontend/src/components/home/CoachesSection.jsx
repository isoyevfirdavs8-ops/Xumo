
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  Award,
  ArrowUpRight,
  BriefcaseBusiness,
  UserRound,
} from "lucide-react";

import "./CoachesSection.css";

export default function CoachesSection() {
  const [coaches, setCoaches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadCoaches() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch("/api/v1/coaches/", {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(
            `Murabbiylarni yuklashda xatolik: HTTP ${response.status}`
          );
        }

        const data = await response.json();

        const items = Array.isArray(data)
          ? data
          : Array.isArray(data?.results)
            ? data.results
            : [];

        if (!controller.signal.aborted) {
          setCoaches(items);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : "Noma'lum xatolik yuz berdi."
          );
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

  return (
    <section
      className="home-coaches"
      id="coaches"
      aria-labelledby="home-coaches-heading"
    >
      <div className="home-coaches-container">

        {/* Section heading */}
        <div className="home-coaches-heading">
          <span className="home-coaches-eyebrow">
            XUMO · OUR TEAM
          </span>

          <h2 id="home-coaches-heading">
            BIZNING PROFESSIONAL
            <span> MURABBIYLARIMIZ</span>
          </h2>

          <p>
            Tajribali mutaxassislarimiz bilan sportdagi
            maqsadlaringizga erishing.
          </p>

          <div className="home-coaches-heading-line" />
        </div>

        {/* Loading */}
        {loading && (
          <div
            className="home-coaches-message"
            role="status"
          >
            Murabbiylar yuklanmoqda...
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div
            className="home-coaches-message"
            role="alert"
          >
            {error}
          </div>
        )}

        {/* Empty */}
        {!loading && !error && coaches.length === 0 && (
          <div className="home-coaches-empty">
            <UserRound size={36} />
            <p>Hozircha murabbiylar mavjud emas.</p>
          </div>
        )}

        {/* Coach cards */}
        {!loading && !error && coaches.length > 0 && (
          <div className="home-coaches-grid">
            {coaches.map((coach) => (
              <article
                key={coach.id}
                className="home-coach-card"
              >
                <div className="home-coach-image">
                  {coach.image ? (
                    <img
                      src={coach.image}
                      alt={coach.full_name}
                      loading="lazy"
                    />
                  ) : (
                    <UserRound
                      size={64}
                      className="home-coach-placeholder"
                    />
                  )}

                  <div className="home-coach-image-overlay" />

                  <span className="home-coach-category">
                    {coach.category_name}
                  </span>
                </div>

                <div className="home-coach-content">
                  <div className="home-coach-title-row">
                    <div>
                      <h3>{coach.full_name}</h3>

                      <p className="home-coach-specialization">
                        {coach.specialization}
                      </p>
                    </div>

                    <Award
                      size={23}
                      className="home-coach-award"
                    />
                  </div>

                  <div className="home-coach-experience">
                    <BriefcaseBusiness size={16} />

                    <span>
                      {coach.experience_years} yillik tajriba
                    </span>
                  </div>



                  <Link
                    to={`/coaches/${coach.id}`}
                    className="home-coach-detail-link"
                  >
                    Murabbiy haqida
                    <ArrowUpRight size={18} />
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
