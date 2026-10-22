
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Plus,
  Pencil,
  Trash2,
  ImageOff,
  Layers3,
} from "lucide-react";

import "./Category.css";

const API_URL = "/api/v1/dashboard/categories/";

export default function CategoryList() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadCategories() {
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
            `Kategoriyalarni yuklashda xatolik: HTTP ${response.status}`
          );
        }

        const data = await response.json();

        if (!controller.signal.aborted) {
          setCategories(
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

    loadCategories();

    return () => controller.abort();
  }, []);

  async function handleDelete(category) {
    const confirmed = window.confirm(
      `"${category.name}" kategoriyasini o‘chirmoqchimisiz?`
    );

    if (!confirmed) return;

    const token = sessionStorage.getItem("access_token");

    setDeletingId(category.id);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}${category.id}/`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        if (response.status === 409) {
          throw new Error(
            "Kategoriya boshqa ma’lumotlar bilan bog‘langan."
          );
        }

        throw new Error(
          `O‘chirishda xatolik: HTTP ${response.status}`
        );
      }

      setCategories((prev) =>
        prev.filter((item) => item.id !== category.id)
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="category-dashboard">
      <div className="dashboard-page-heading">
        <div>
          <h1>Kategoriyalar</h1>
          <p className="category-page-subtitle">
            FC BUKHARA xizmatlarini boshqarish
          </p>
        </div>

        <Link
          to="/dashboard/categories/create"
          className="dashboard-primary-btn"
        >
          <Plus size={18} />
          Kategoriya qo‘shish
        </Link>
      </div>

      {error && (
        <div className="category-error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <div className="dashboard-card">
          Kategoriyalar yuklanmoqda...
        </div>
      ) : categories.length === 0 && !error ? (
        <div className="category-empty">
          <Layers3 size={44} />
          <h2>Kategoriyalar mavjud emas</h2>
          <p>
            Futbol, boks, tennis va restoran
            kategoriyalarini qo‘shing.
          </p>
          <Link
            to="/dashboard/categories/create"
            className="dashboard-primary-btn"
          >
            <Plus size={18} />
            Birinchi kategoriyani qo‘shish
          </Link>
        </div>
      ) : (
        <div className="category-admin-grid">
          {categories.map((category) => (
            <article
              key={category.id}
              className="category-admin-card"
            >
              <div className="category-admin-image">
                {category.image ? (
                  <img
                    src={category.image}
                    alt={category.name}
                    loading="lazy"
                  />
                ) : (
                  <ImageOff size={36} />
                )}

                <span
                  className={`category-status ${
                    category.is_active ? "active" : "inactive"
                  }`}
                >
                  {category.is_active ? "Faol" : "Nofaol"}
                </span>
              </div>

              <div className="category-admin-body">
                <h2>{category.name}</h2>

                <p>{category.description || "Tavsif yo‘q"}</p>

                <div className="category-admin-meta">
                  <span>Slug: {category.slug}</span>
                  <span>Tartib: {category.sort_order}</span>
                </div>

                <div className="category-admin-actions">
                  <Link
                    to={`/dashboard/categories/${category.id}/edit`}
                    className="category-edit-btn"
                  >
                    <Pencil size={16} />
                    Tahrirlash
                  </Link>

                  <button
                    type="button"
                    className="category-delete-btn"
                    onClick={() => handleDelete(category)}
                    disabled={deletingId === category.id}
                  >
                    <Trash2 size={16} />
                    {deletingId === category.id
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
