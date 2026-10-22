
import { useEffect, useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  ArrowLeft,
  Save,
  UploadCloud,
} from "lucide-react";

import "./Coach.css";

const API_URL = "/api/v1/dashboard/coaches/";

const INITIAL_FORM = {
  category: "",
  full_name: "",
  specialization: "",
  experience_years: 0,
  bio: "",
  is_active: true,
  sort_order: 0,
};

export default function CoachForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [form, setForm] = useState(INITIAL_FORM);
  const [categories, setCategories] = useState([]);
  const [image, setImage] = useState(null);
  const [currentImage, setCurrentImage] = useState("");
  const [preview, setPreview] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadData() {
      try {
        const token = sessionStorage.getItem("access_token");

        const categoryResponse = await fetch(
          "/api/v1/dashboard/categories/",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: controller.signal,
          }
        );

        if (!categoryResponse.ok) {
          throw new Error(
            "Kategoriyalarni yuklab bo‘lmadi."
          );
        }

        const categoryData = await categoryResponse.json();

        if (!controller.signal.aborted) {
          setCategories(
            Array.isArray(categoryData)
              ? categoryData
              : categoryData.results || []
          );
        }

        if (isEdit) {
          const coachResponse = await fetch(
            `${API_URL}${id}/`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: controller.signal,
            }
          );

          if (!coachResponse.ok) {
            throw new Error(
              "Murabbiy ma’lumotlarini yuklab bo‘lmadi."
            );
          }

          const coach = await coachResponse.json();

          if (!controller.signal.aborted) {
            setForm({
              category: String(coach.category),
              full_name: coach.full_name || "",
              specialization: coach.specialization || "",
              experience_years: coach.experience_years ?? 0,
              bio: coach.bio || "",
              is_active: Boolean(coach.is_active),
              sort_order: coach.sort_order ?? 0,
            });

            setCurrentImage(coach.image || "");
          }
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

    loadData();

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

    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function handleImageChange(event) {
    const file = event.target.files?.[0];

    if (!file) return;

    if (
      !["image/jpeg", "image/png", "image/webp"].includes(
        file.type
      )
    ) {
      setError("Faqat JPG, PNG yoki WEBP rasm yuklang.");
      event.target.value = "";
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("Rasm hajmi 5 MB dan oshmasligi kerak.");
      event.target.value = "";
      return;
    }

    setImage(file);
    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!isEdit && !image) {
      setError("Murabbiy rasmi majburiy.");
      return;
    }

    const token = sessionStorage.getItem("access_token");

    if (!token) {
      navigate("/login");
      return;
    }

    const payload = new FormData();

    payload.append("category", form.category);
    payload.append("full_name", form.full_name.trim());
    payload.append(
      "specialization",
      form.specialization.trim()
    );
    payload.append(
      "experience_years",
      String(form.experience_years)
    );
    payload.append("bio", form.bio.trim());
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

      navigate("/dashboard/coaches");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="dashboard-card">
        Ma’lumotlar yuklanmoqda...
      </div>
    );
  }

  return (
    <div className="coach-dashboard">
      <div className="dashboard-page-heading">
        <div>
          <h1>
            {isEdit
              ? "Murabbiyni tahrirlash"
              : "Yangi murabbiy"}
          </h1>
          <p className="coach-page-subtitle">
            Murabbiy ma’lumotlarini kiriting
          </p>
        </div>

        <Link
          to="/dashboard/coaches"
          className="coach-back-btn"
        >
          <ArrowLeft size={18} />
          Orqaga
        </Link>
      </div>

      <form
        className="dashboard-card coach-form"
        onSubmit={handleSubmit}
      >
        {error && (
          <div className="coach-error" role="alert">
            {error}
          </div>
        )}

        <div className="coach-form-grid">
          <div className="coach-form-field">
            <label htmlFor="coach-name">
              To‘liq ism *
            </label>
            <input
              id="coach-name"
              name="full_name"
              value={form.full_name}
              onChange={handleChange}
              placeholder="Masalan: Ali Valiyev"
              required
              maxLength={160}
            />
          </div>

          <div className="coach-form-field">
            <label htmlFor="coach-category">
              Kategoriya *
            </label>
            <select
              id="coach-category"
              name="category"
              value={form.category}
              onChange={handleChange}
              required
            >
              <option value="">Kategoriyani tanlang</option>

              {categories
                .filter(
                  (category) =>
                    category.is_active ||
                    String(category.id) === form.category
                )
                .map((category) => (
                  <option
                    key={category.id}
                    value={category.id}
                  >
                    {category.name}
                  </option>
                ))}
            </select>
          </div>
        </div>

        <div className="coach-form-grid">
          <div className="coach-form-field">
            <label htmlFor="coach-specialization">
              Mutaxassisligi *
            </label>
            <input
              id="coach-specialization"
              name="specialization"
              value={form.specialization}
              onChange={handleChange}
              placeholder="Masalan: Futbol bosh murabbiyi"
              required
              maxLength={160}
            />
          </div>

          <div className="coach-form-field">
            <label htmlFor="coach-experience">
              Ish tajribasi (yil)
            </label>
            <input
              id="coach-experience"
              type="number"
              name="experience_years"
              min="0"
              max="65535"
              value={form.experience_years}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="coach-form-field">
          <label htmlFor="coach-bio">
            Murabbiy haqida
          </label>
          <textarea
            id="coach-bio"
            name="bio"
            rows={5}
            value={form.bio}
            onChange={handleChange}
            placeholder="Murabbiyning yutuqlari, tajribasi..."
          />
        </div>

        <div className="coach-form-field">
          <label htmlFor="coach-image">
            Murabbiy rasmi {!isEdit && "*"}
          </label>

          <label
            htmlFor="coach-image"
            className="coach-upload-box"
          >
            <UploadCloud size={32} />
            <strong>Rasm tanlash</strong>
            <span>JPG, PNG yoki WEBP — maksimal 5 MB</span>
          </label>

          <input
            id="coach-image"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleImageChange}
            required={!isEdit}
          />

          {(preview || currentImage) && (
            <img
              src={preview || currentImage}
              alt="Murabbiy rasmi"
              className="coach-image-preview"
            />
          )}
        </div>

        <div className="coach-form-grid">
          <div className="coach-form-field">
            <label htmlFor="coach-order">
              Tartib raqami
            </label>
            <input
              id="coach-order"
              type="number"
              name="sort_order"
              min="0"
              value={form.sort_order}
              onChange={handleChange}
            />
          </div>

          <div className="coach-active-field">
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

        <div className="coach-form-footer">
          <Link
            to="/dashboard/coaches"
            className="coach-back-btn"
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
