
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Save, UploadCloud } from "lucide-react";

import "./Category.css";

const API_URL = "/api/v1/dashboard/categories/";

const INITIAL_FORM = {
  name: "",
  slug: "",
  description: "",
  is_active: true,
  sort_order: 0,
};

function makeSlug(value) {
  return value
    .toLowerCase()
    .trim()
    .replace(/['‘’`]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export default function CategoryForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [form, setForm] = useState(INITIAL_FORM);
  const [image, setImage] = useState(null);
  const [currentImage, setCurrentImage] = useState("");
  const [preview, setPreview] = useState("");
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isEdit) return;

    const controller = new AbortController();

    async function loadCategory() {
      try {
        const token = sessionStorage.getItem("access_token");

        const response = await fetch(`${API_URL}${id}/`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(
            `Kategoriya yuklanmadi: HTTP ${response.status}`
          );
        }

        const data = await response.json();

        if (!controller.signal.aborted) {
          setForm({
            name: data.name || "",
            slug: data.slug || "",
            description: data.description || "",
            is_active: Boolean(data.is_active),
            sort_order: data.sort_order ?? 0,
          });

          setCurrentImage(data.image || "");
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
  }, [id, isEdit]);

  useEffect(() => {
    if (!image) {
      setPreview("");
      return;
    }

    const objectUrl = URL.createObjectURL(image);
    setPreview(objectUrl);

    return () => URL.revokeObjectURL(objectUrl);
  }, [image]);

  function handleChange(event) {
    const { name, value, type, checked } = event.target;

    setForm((prev) => {
      const updated = {
        ...prev,
        [name]: type === "checkbox" ? checked : value,
      };

      if (name === "name" && !isEdit) {
        updated.slug = makeSlug(value);
      }

      return updated;
    });
  }

  function handleImageChange(event) {
    const file = event.target.files?.[0];

    if (!file) {
      setImage(null);
      return;
    }

    const allowedTypes = [
      "image/jpeg",
      "image/png",
      "image/webp",
    ];

    if (!allowedTypes.includes(file.type)) {
      setError("Faqat JPG, PNG yoki WEBP rasm yuklang.");
      event.target.value = "";
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("Rasm hajmi 5 MB dan oshmasligi kerak.");
      event.target.value = "";
      return;
    }

    setError("");
    setImage(file);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!isEdit && !image) {
      setError("Kategoriya rasmi majburiy.");
      return;
    }

    const token = sessionStorage.getItem("access_token");

    if (!token) {
      navigate("/login");
      return;
    }

    const payload = new FormData();

    payload.append("name", form.name.trim());
    payload.append("slug", form.slug.trim());
    payload.append("description", form.description.trim());
    payload.append("is_active", String(form.is_active));
    payload.append("sort_order", String(form.sort_order));

    if (image) {
      payload.append("image", image);
    }

    setSaving(true);

    try {
      const response = await fetch(
        isEdit ? `${API_URL}${id}/` : API_URL,
        {
          method: isEdit ? "PATCH" : "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: payload,
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => null);

        const message = data
          ? Object.entries(data)
              .map(([field, errors]) => {
                const text = Array.isArray(errors)
                  ? errors.join(", ")
                  : String(errors);

                return `${field}: ${text}`;
              })
              .join("\n")
          : `HTTP ${response.status}`;

        throw new Error(message);
      }

      navigate("/dashboard/categories");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="dashboard-card">Yuklanmoqda...</div>;
  }

  return (
    <div className="category-dashboard">
      <div className="dashboard-page-heading">
        <h1>
          {isEdit
            ? "Kategoriyani tahrirlash"
            : "Yangi kategoriya"}
        </h1>

        <Link
          to="/dashboard/categories"
          className="category-back-btn"
        >
          <ArrowLeft size={18} />
          Orqaga
        </Link>
      </div>

      <form
        className="dashboard-card category-form"
        onSubmit={handleSubmit}
      >
        {error && (
          <div className="category-error" role="alert">
            {error}
          </div>
        )}

        <div className="category-form-grid">
          <div className="category-form-field">
            <label htmlFor="category-name">
              Kategoriya nomi *
            </label>

            <input
              id="category-name"
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="Masalan: Futbol"
              maxLength={120}
              required
            />
          </div>

          <div className="category-form-field">
            <label htmlFor="category-slug">
              Slug *
            </label>

            <input
              id="category-slug"
              name="slug"
              value={form.slug}
              onChange={handleChange}
              placeholder="football"
              maxLength={140}
              required
            />
          </div>
        </div>

        <div className="category-form-field">
          <label htmlFor="category-description">
            Tavsif
          </label>

          <textarea
            id="category-description"
            name="description"
            rows={4}
            value={form.description}
            onChange={handleChange}
            placeholder="Kategoriya haqida qisqacha ma’lumot..."
          />
        </div>

        <div className="category-form-field">
          <label htmlFor="category-image">
            Kategoriya rasmi {!isEdit && "*"}
          </label>

          <label
            htmlFor="category-image"
            className="category-upload-box"
          >
            <UploadCloud size={30} />

            <strong>Rasm tanlash</strong>

            <span>JPG, PNG yoki WEBP — maksimal 5 MB</span>
          </label>

          <input
            id="category-image"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleImageChange}
            required={!isEdit}
            className="category-file-input"
          />

          {(preview || currentImage) && (
            <img
              src={preview || currentImage}
              alt="Kategoriya rasmi"
              className="category-image-preview"
            />
          )}
        </div>

        <div className="category-form-grid">
          <div className="category-form-field">
            <label htmlFor="category-order">
              Tartib raqami
            </label>

            <input
              id="category-order"
              type="number"
              name="sort_order"
              min="0"
              value={form.sort_order}
              onChange={handleChange}
            />
          </div>

          <div className="category-active-field">
            <label>
              <input
                type="checkbox"
                name="is_active"
                checked={form.is_active}
                onChange={handleChange}
              />
              Saytda ko‘rsatilsin
            </label>
          </div>
        </div>

        <div className="category-form-footer">
          <Link
            to="/dashboard/categories"
            className="category-back-btn"
          >
            Bekor qilish
          </Link>

          <button
            type="submit"
            className="dashboard-primary-btn"
            disabled={saving}
          >
            <Save size={18} />
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
        </div>
      </form>
    </div>
  );
}
