
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, Layers3 } from "lucide-react";

import "./CategoriesSection.css";


function getCategoryUrl(category) {
  const slug = String(category.slug || "")
    .trim()
    .toLowerCase();

  const name = String(category.name || "")
    .trim()
    .toLowerCase();

  const isRestaurant =
    ["restaurant", "restarant", "restorant"].includes(slug) ||
    ["restaurant", "restarant", "restorant"].includes(name);

  if (isRestaurant) {
    return "/restaurant";
  }

  const isHostel =
    ["hostel", "hotel", "yotoqxona", "yotoq-xona"].includes(slug) ||
    ["hostel", "hotel", "yotoqxona", "yotoq-xona"].includes(name);

  if (isHostel) {
    return "/hostel";
  }

  return `/categories/${encodeURIComponent(category.slug)}`;
}


export default function CategoriesSection() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadCategories() {
      try {
        const response = await fetch("/api/v1/categories/", {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(
            `Kategoriyalar yuklanmadi: HTTP ${response.status}`
          );
        }

        const data = await response.json();

        const items = Array.isArray(data)
          ? data
          : Array.isArray(data.results)
            ? data.results
            : [];

        if (!controller.signal.aborted) {
          setCategories(
            items.filter((item) => item.is_active)
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

    loadCategories();

    return () => controller.abort();
  }, []);

  return (
    <section
      className="home-categories"
      id="categories"
      aria-labelledby="categories-heading"
    >
      <div className="home-categories-container">
        <div className="home-categories-heading">
          <span className="home-categories-eyebrow">
            XUMO · SPORT & LIFESTYLE
          </span>

          <h2 id="categories-heading">
            BIZNING <span>XIZMATLARIMIZ</span>
          </h2>

          <p>
            Sport, sog‘lom turmush va mazmunli hordiq uchun
            yaratilgan zamonaviy imkoniyatlar.
          </p>
        </div>

        {loading && (
          <p className="home-categories-message">
            Kategoriyalar yuklanmoqda...
          </p>
        )}

        {!loading && error && (
          <p
            className="home-categories-message"
            role="alert"
          >
            {error}
          </p>
        )}

        {!loading && !error && categories.length === 0 && (
          <div className="home-categories-empty">
            <Layers3 size={36} />
            <p>Hozircha kategoriyalar mavjud emas.</p>
          </div>
        )}

        {!loading && !error && categories.length > 0 && (
          <div className="home-categories-grid">
            {categories.map((category) => (
              <article
                key={category.id}
                className="home-category-card"
              >
                <div className="home-category-image">
                  {category.image ? (
                    <img
                      src={category.image}
                      alt={category.name}
                      loading="lazy"
                    />
                  ) : (
                    <Layers3 size={40} />
                  )}

                  <div className="home-category-image-overlay" />
                </div>

                <div className="home-category-content">
                  <span className="home-category-label">
                    FC BUKHARA
                  </span>

                  <h3>{category.name}</h3>

                  <p>
                    {category.description ||
                      "Zamonaviy sport va dam olish imkoniyatlari."}
                  </p>

                  <Link
                    to={getCategoryUrl(category)}
                    className="home-category-link"
                  >
                    Batafsil
                    <ArrowUpRight size={19} />
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
