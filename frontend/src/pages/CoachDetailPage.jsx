
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Award,
  BriefcaseBusiness,
  UserRound,
} from "lucide-react";

export default function CoachDetailPage() {
  const { id } = useParams();

  const [coach, setCoach] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadCoach() {
      setLoading(true);
      setError("");
      setCoach(null);

      try {
        const response = await fetch(
          `/api/v1/coaches/${encodeURIComponent(id)}/`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(
            response.status === 404
              ? "Murabbiy topilmadi."
              : `Ma’lumot yuklanmadi: HTTP ${response.status}`
          );
        }

        const data = await response.json();

        if (!controller.signal.aborted) {
          setCoach(data);
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

    loadCoach();

    return () => controller.abort();
  }, [id]);

  return (
    <main
      style={{
        minHeight: "80vh",
        background: "#08172c",
        color: "#fff",
        padding: "65px 24px",
      }}
    >
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <Link
          to="/#coaches"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            color: "#d7aa5a",
            textDecoration: "none",
          }}
        >
          <ArrowLeft size={18} />
          Murabbiylarga qaytish
        </Link>

        {loading && <p>Yuklanmoqda...</p>}

        {error && <p role="alert">{error}</p>}

        {!loading && !error && coach && (
          <article
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(min(100%, 280px), 1fr))",
              gap: 36,
              marginTop: 40,
            }}
          >
            <div>
              {coach.image ? (
                <img
                  src={coach.image}
                  alt={coach.full_name}
                  style={{
                    width: "100%",
                    maxHeight: 520,
                    objectFit: "cover",
                    borderRadius: 16,
                  }}
                />
              ) : (
                <UserRound size={90} color="#d7aa5a" />
              )}
            </div>

            <div>
              <p
                style={{
                  color: "#d7aa5a",
                  fontWeight: 700,
                }}
              >
                {coach.category_name}
              </p>

              <h1
                style={{
                  fontSize: "clamp(30px, 4vw, 52px)",
                  lineHeight: 1.2,
                }}
              >
                {coach.full_name}
              </h1>

              <h2
                style={{
                  color: "#d7aa5a",
                  fontSize: 20,
                  marginTop: 18,
                }}
              >
                {coach.specialization}
              </h2>

              <p
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  marginTop: 25,
                  color: "#c1cede",
                }}
              >
                <BriefcaseBusiness size={19} />
                {coach.experience_years} yillik tajriba
              </p>

              <div
                style={{
                  height: 1,
                  background: "rgba(255,255,255,0.15)",
                  margin: "28px 0",
                }}
              />

              <h3
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                }}
              >
                <Award size={20} color="#d7aa5a" />
                Murabbiy haqida
              </h3>

              <p
                style={{
                  color: "#b7c3d3",
                  lineHeight: 1.9,
                  whiteSpace: "pre-line",
                }}
              >
                {coach.bio || "Ma’lumot kiritilmagan."}
              </p>
            </div>
          </article>
        )}
      </div>
    </main>
  );
}
