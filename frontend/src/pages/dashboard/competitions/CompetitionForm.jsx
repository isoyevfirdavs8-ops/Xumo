
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Save, UploadCloud } from "lucide-react";

import "./Competition.css";

const API_URL = "/api/v1/dashboard/competitions/";

const initialForm = {
  name: "",
  description: "",
  start_time: "",
  min_age: "7",
  max_age: "18",
  price: "",
  capacity: "",
  is_active: true,
};

function toLocalDateTime(value) {
  if (!value) return "";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "";

  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Tashkent",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);

  const get = (type) =>
    parts.find((part) => part.type === type)?.value || "";

  return (
    `${get("year")}-${get("month")}-${get("day")}` +
    `T${get("hour")}:${get("minute")}`
  );
}

function toServerDateTime(value) {
  // datetime-local qiymati FC BUKHARA uchun
  // Toshkent vaqti sifatida talqin qilinadi.
  return `${value}:00+05:00`;
}

function getErrorMessage(data, fallback) {
  if (!data || typeof data !== "object") return fallback;

  const messages = Object.entries(data).map(([field, value]) => {
    const detail = Array.isArray(value)
      ? value.join(", ")
      : typeof value === "string"
        ? value
        : JSON.stringify(value);

    return `${field}: ${detail}`;
  });

  return messages.length ? messages.join("\n") : fallback;
}

export default function CompetitionForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);

  const [form, setForm] = useState(initialForm);
  const [banner, setBanner] = useState(null);
  const [preview, setPreview] = useState("");
  const [loading, setLoading] = useState(isEditing);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [originalStartTime, setOriginalStartTime] = useState("");

  useEffect(() => {
    if (!isEditing) return;

    const controller = new AbortController();

    async function loadCompetition() {
      try {
        setLoading(true);

        const token = sessionStorage.getItem("access_token");
        if (!token) throw new Error("Avval tizimga kiring.");

        const response = await fetch(`${API_URL}${id}/`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Musobaqa ma’lumotlarini olib bo‘lmadi (HTTP ${response.status}).`);
        }

        const data = await response.json();

        if (controller.signal.aborted) return;

        setForm({
          name: data.name ?? "",
          description: data.description ?? "",
          start_time: toLocalDateTime(data.start_time),
          min_age: String(data.min_age ?? ""),
          max_age: String(data.max_age ?? ""),
          price: String(data.price ?? ""),
          capacity: String(data.capacity ?? ""),
          is_active: Boolean(data.is_active),
        });
        setOriginalStartTime(toLocalDateTime(data.start_time));

        setPreview(data.banner || "");
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
  }, [id, isEditing]);

  useEffect(() => {
    if (!banner) return;

    const url = URL.createObjectURL(banner);
    setPreview(url);

    return () => URL.revokeObjectURL(url);
  }, [banner]);

  function updateField(event) {
    const { name, value, type, checked } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function handleBannerChange(event) {
    const file = event.target.files?.[0];

    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setError("Banner hajmi 5 MB dan oshmasligi kerak.");
      event.target.value = "";
      return;
    }

    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setError("Faqat JPG, PNG yoki WEBP rasm yuklang.");
      event.target.value = "";
      return;
    }

    setError("");
    setBanner(file);
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (saving) return;

    setError("");

    if (Number(form.min_age) > Number(form.max_age)) {
      setError("Minimal yosh maksimal yoshdan katta bo‘lmasin.");
      return;
    }

    if (!form.start_time) {
      setError("Musobaqa boshlanish vaqtini kiriting.");
      return;
    }

    if (!isEditing && !banner) {
      setError("Musobaqa bannerini yuklang.");
      return;
    }

    const token = sessionStorage.getItem("access_token");

    if (!token) {
      setError("Avval tizimga kiring.");
      return;
    }

    const formData = new FormData();

    formData.append("name", form.name.trim());
    formData.append("description", form.description);
    if (!isEditing || form.start_time !== originalStartTime) {
      formData.append("start_time", toServerDateTime(form.start_time));
    }
    formData.append("min_age", form.min_age);
    formData.append("max_age", form.max_age);
    formData.append("price", form.price);
    formData.append("capacity", form.capacity);
    formData.append("is_active", String(form.is_active));

    if (banner) {
      formData.append("banner", banner);
    }

    try {
      setSaving(true);

      const response = await fetch(
        isEditing ? `${API_URL}${id}/` : API_URL,
        {
          method: isEditing ? "PATCH" : "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => null);

        throw new Error(
          getErrorMessage(
            data,
            `Saqlashda xatolik: HTTP ${response.status}`
          )
        );
      }

      navigate("/dashboard/competitions");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="dc-page">
        <p>Musobaqa ma’lumotlari yuklanmoqda...</p>
      </div>
    );
  }

  return (
    <div className="dc-page">
      <Link
        to="/dashboard/competitions"
        className="dc-back-link"
      >
        <ArrowLeft size={18} />
        Musobaqalarga qaytish
      </Link>

      <div className="dc-page-header">
        <div>
          <span className="dc-eyebrow">
            FC BUKHARA / DASHBOARD
          </span>

          <h1>
            {isEditing
              ? "Musobaqani tahrirlash"
              : "Yangi musobaqa"}
          </h1>

          <p>
            Musobaqa haqidagi ma’lumotlarni kiriting.
          </p>
        </div>
      </div>

      <form
        className="dc-form"
        onSubmit={handleSubmit}
      >
        {error && (
          <div className="dc-error" role="alert">
            {error}
          </div>
        )}

        <div className="dc-field">
          <label htmlFor="competition-name">
            Musobaqa nomi *
          </label>

          <input
            id="competition-name"
            name="name"
            value={form.name}
            onChange={updateField}
            minLength={3}
            maxLength={255}
            required
            placeholder="FC BUKHARA CUP 2026"
          />
        </div>

        <div className="dc-field">
          <label htmlFor="competition-description">
            Musobaqa tavsifi *
          </label>

          <textarea
            id="competition-description"
            name="description"
            value={form.description}
            onChange={updateField}
            rows={6}
            required
            placeholder="Musobaqa haqida batafsil..."
          />
        </div>

        <div className="dc-field">
          <label htmlFor="competition-banner">
            Musobaqa banneri
            {!isEditing && " *"}
          </label>

          <label
            htmlFor="competition-banner"
            className="dc-upload"
          >
            <UploadCloud size={28} />
            <span>Rasm tanlash (JPG, PNG, WEBP)</span>
            <small>Maksimal 5 MB</small>
          </label>

          <input
            id="competition-banner"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleBannerChange}
            required={!isEditing}
            className="dc-file-input"
          />

          {preview && (
            <img
              src={preview}
              alt="Musobaqa banneri"
              className="dc-banner-preview"
            />
          )}
        </div>

        <div className="dc-form-grid">
          <div className="dc-field">
            <label htmlFor="competition-time">
              Boshlanish vaqti *
            </label>

            <input
              id="competition-time"
              type="datetime-local"
              name="start_time"
              value={form.start_time}
              onChange={updateField}
              required
            />

            <small>Vaqt: Toshkent (UTC+5)</small>
          </div>

          <div className="dc-field">
            <label htmlFor="competition-price">
              Chipta narxi (so‘m) *
            </label>

            <input
              id="competition-price"
              type="number"
              name="price"
              min="0"
              step="0.01"
              value={form.price}
              onChange={updateField}
              required
            />
          </div>

          <div className="dc-field">
            <label htmlFor="competition-min-age">
              Minimal yosh *
            </label>

            <input
              id="competition-min-age"
              type="number"
              name="min_age"
              min="0"
              max="120"
              value={form.min_age}
              onChange={updateField}
              required
            />
          </div>

          <div className="dc-field">
            <label htmlFor="competition-max-age">
              Maksimal yosh *
            </label>

            <input
              id="competition-max-age"
              type="number"
              name="max_age"
              min="0"
              max="120"
              value={form.max_age}
              onChange={updateField}
              required
            />
          </div>

          <div className="dc-field">
            <label htmlFor="competition-capacity">
              Chiptalar sig‘imi *
            </label>

            <input
              id="competition-capacity"
              type="number"
              name="capacity"
              min="1"
              step="1"
              value={form.capacity}
              onChange={updateField}
              required
            />
          </div>
        </div>

        <label className="dc-checkbox">
          <input
            type="checkbox"
            name="is_active"
            checked={form.is_active}
            onChange={updateField}
          />

          <span>Musobaqa faol bo‘lsin</span>
        </label>

        <div className="dc-form-actions">
          <Link
            to="/dashboard/competitions"
            className="dc-cancel-button"
          >
            Bekor qilish
          </Link>

          <button
            type="submit"
            className="dc-primary-button"
            disabled={saving}
          >
            <Save size={18} />

            {saving
              ? "Saqlanmoqda..."
              : isEditing
                ? "O‘zgarishlarni saqlash"
                : "Musobaqa yaratish"}
          </button>
        </div>
      </form>
    </div>
  );
}
