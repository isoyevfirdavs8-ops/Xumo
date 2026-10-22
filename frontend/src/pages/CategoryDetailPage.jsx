
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

export default function CategoryDetailPage() {
  const { slug } = useParams();

  const [category, setCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadCategory() {
      setLoading(true);
      setError("");

      try {
        const response = await fetch(
          `/api/v1/categories/${encodeURIComponent(slug)}/`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(
            response.status === 404
              ? "Kategoriya topilmadi."
              : `Ma’lumot yuklanmadi: HTTP ${response.status}`
          );
        }

        const data = await response.json();

        if (!controller.signal.aborted) {
          setCategory(data);
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

    loadCategory();

    return () => controller.abort();
  }, [slug]);

  return (
    <main
      style={{
        minHeight: "75vh",
        background: "#08172c",
        color: "#fff",
        padding: "60px 24px",
      }}
    >
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <Link to="/" style={{ color: "#d7aa5a" }}>
          ← Bosh sahifaga qaytish
        </Link>

        {loading && <p>Yuklanmoqda...</p>}

        {error && <p role="alert">{error}</p>}

        {!loading && !error && category && (
          <article style={{ marginTop: 35 }}>
            <h1 style={{ fontSize: "clamp(32px, 5vw, 58px)" }}>
              {category.name}
            </h1>

            {category.image && (
              <img
                src={category.image}
                alt={category.name}
                style={{
                  width: "100%",
                  maxHeight: 480,
                  objectFit: "cover",
                  borderRadius: 16,
                }}
              />
            )}

            <p style={{ fontSize: 18, lineHeight: 1.8 }}>
              {category.description}
            </p>
          </article>
        )}
      </div>
    </main>
  );
}
