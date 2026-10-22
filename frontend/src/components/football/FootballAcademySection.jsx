
import { useEffect, useState } from "react";
import { Goal } from "lucide-react";
import { useNavigate } from "react-router-dom";
import "./FootballAcademySection.css";

const API_URL = "/api/v1/football/academies/";

export default function FootballAcademySection() {
  const navigate = useNavigate();

  const [academies, setAcademies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadAcademies() {
      try {
        const response = await fetch(API_URL, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(
            "Futbol akademiyalarini yuklashda xatolik."
          );
        }

        const data = await response.json();

        setAcademies(
          Array.isArray(data)
            ? data
            : Array.isArray(data.results)
              ? data.results
              : []
        );
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

    loadAcademies();

    return () => controller.abort();
  }, []);

  const formatPrice = (price) =>
    new Intl.NumberFormat("uz-UZ", {
      maximumFractionDigits: 0,
    }).format(Number(price));

  return (
    <section
      className="football-academy-section"
      id="football-academies"
    >
      <div className="football-academy-hero">
        <span>XUMO SPORT MAJMUASI</span>
        <h2>Futbol akademiyasi</h2>
        <p>
          Professional futbol mashg'ulotlariga oylik
          obuna bo'ling. O'zingizga mos akademiyani
          tanlang va mashg'ulotlarni boshlang.
        </p>
      </div>

      {loading && (
        <p className="football-academy-message">
          Akademiyalar yuklanmoqda...
        </p>
      )}

      {error && (
        <p className="football-academy-error" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && academies.length === 0 && (
        <p className="football-academy-message">
          Hozircha faol futbol akademiyalari mavjud emas.
        </p>
      )}

      <div className="football-academy-grid">
        {academies.map((academy) => {
          const primaryImage =
            academy.images?.find(
              (image) => image.is_primary
            ) || academy.images?.[0];

          return (
            <article
              className="football-academy-card"
              key={academy.id}
            >
              <div className="football-academy-cover">
                {primaryImage?.image ? (
                  <img
                    src={primaryImage.image}
                    alt={academy.name}
                    loading="lazy"
                  />
                ) : (
                  <div className="football-academy-placeholder">
                    <Goal size={58} strokeWidth={1.7} />
                  </div>
                )}
              </div>

              <div className="football-academy-body">
                <h3>{academy.name}</h3>

                <p>
                  {academy.description ||
                    "Professional futbol mashg'ulotlari."}
                </p>

                <div className="football-academy-price">
                  {formatPrice(academy.monthly_price)}
                  <small> so'm / oy</small>
                </div>

                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      `/football/academies/${academy.id}`
                    )
                  }
                >
                  Shu akademiyani tanlash
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
