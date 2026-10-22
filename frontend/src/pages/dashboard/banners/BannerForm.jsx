
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Save, ImagePlus } from "lucide-react";

const INITIAL_FORM = {
  title: "",
  subtitle: "",
  button_text: "",
  button_url: "",
  is_active: true,
  sort_order: 0,
};

export default function BannerForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [form, setForm] = useState(INITIAL_FORM);
  const [image, setImage] = useState(null);
  const [mobileImage, setMobileImage] = useState(null);
  const [currentImage, setCurrentImage] = useState("");
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isEdit) return;

    const controller = new AbortController();
    const token = sessionStorage.getItem("access_token");

    async function loadBanner() {
      try {
        const response = await fetch(
          `/api/v1/dashboard/banners/${id}/`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: controller.signal,
          }
        );

        if (!response.ok) {
          throw new Error(`Banner topilmadi: HTTP ${response.status}`);
        }

        const data = await response.json();

        setForm({
          title: data.title || "",
          subtitle: data.subtitle || "",
          button_text: data.button_text || "",
          button_url: data.button_url || "",
          is_active: Boolean(data.is_active),
          sort_order: data.sort_order ?? 0,
        });

        setCurrentImage(data.image || "");
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    loadBanner();

    return () => controller.abort();
  }, [id, isEdit]);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;

    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (!isEdit && !image) {
      setError("Desktop banner rasmi majburiy.");
      return;
    }

    const token = sessionStorage.getItem("access_token");

    if (!token) {
      navigate("/login");
      return;
    }

    const payload = new FormData();

    payload.append("title", form.title);
    payload.append("subtitle", form.subtitle);
    payload.append("button_text", form.button_text);
    payload.append("button_url", form.button_url);
    payload.append("is_active", String(form.is_active));
    payload.append("sort_order", String(form.sort_order));

    if (image) payload.append("image", image);
    if (mobileImage) payload.append("mobile_image", mobileImage);

    setSaving(true);

    try {
      const url = isEdit
        ? `/api/v1/dashboard/banners/${id}/`
        : "/api/v1/dashboard/banners/";

      const response = await fetch(url, {
        method: isEdit ? "PATCH" : "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: payload,
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(
          JSON.stringify(data) || `HTTP ${response.status}`
        );
      }

      navigate("/dashboard/banners");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="dashboard-card">Yuklanmoqda...</div>;
  }

  return (
    <div>
      <div className="dashboard-page-heading">
        <h1>{isEdit ? "Bannerni tahrirlash" : "Yangi banner"}</h1>

        <Link to="/dashboard/banners" className="dashboard-primary-btn">
          <ArrowLeft size={18} />
          Orqaga
        </Link>
      </div>

      <form className="dashboard-card banner-form" onSubmit={handleSubmit}>
        {error && <p role="alert" className="banner-form-error">{error}</p>}

        <label htmlFor="banner-title">Sarlavha</label>
        <input
          id="banner-title"
          name="title"
          value={form.title}
          onChange={handleChange}
          maxLength={200}
          required
        />

        <label htmlFor="banner-subtitle">Tavsif</label>
        <textarea
          id="banner-subtitle"
          name="subtitle"
          value={form.subtitle}
          onChange={handleChange}
          rows={4}
        />

        <label htmlFor="banner-button-text">Tugma matni</label>
        <input
          id="banner-button-text"
          name="button_text"
          value={form.button_text}
          onChange={handleChange}
          maxLength={100}
          placeholder="Bron qilish"
        />

        <label htmlFor="banner-button-url">Tugma manzili</label>
        <input
          id="banner-button-url"
          name="button_url"
          value={form.button_url}
          onChange={handleChange}
          placeholder="/booking"
        />

        <label htmlFor="banner-image">
          <ImagePlus size={17} /> Desktop rasmi
        </label>
        <input
          id="banner-image"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          required={!isEdit}
          onChange={(e) => setImage(e.target.files?.[0] || null)}
        />

        {currentImage && (
          <img
            src={currentImage}
            alt="Joriy banner"
            style={{
              width: "100%",
              maxWidth: 500,
              borderRadius: 12,
            }}
          />
        )}

        <label htmlFor="banner-mobile-image">Mobil rasmi (ixtiyoriy)</label>
        <input
          id="banner-mobile-image"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={(e) => setMobileImage(e.target.files?.[0] || null)}
        />

        <label htmlFor="banner-order">Tartib raqami</label>
        <input
          id="banner-order"
          type="number"
          name="sort_order"
          min="0"
          value={form.sort_order}
          onChange={handleChange}
        />

        <label className="banner-checkbox">
          <input
            type="checkbox"
            name="is_active"
            checked={form.is_active}
            onChange={handleChange}
          />
          Saytda ko‘rsatilsin
        </label>

        <button
          type="submit"
          className="dashboard-primary-btn"
          disabled={saving}
        >
          <Save size={18} />
          {saving ? "Saqlanmoqda..." : "Saqlash"}
        </button>
      </form>
    </div>
  );
}
