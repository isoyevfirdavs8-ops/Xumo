
import { useCallback, useEffect, useState } from "react";
import { authFetch } from "../../utils/auth";
import "./TennisCourtsPage.css";

const API = "/api/v1/tennis/courts/";

const EMPTY_FORM = {
  name: "",
  description: "",
  monthly_price: "",
  status: "active",
};

function formatPrice(value) {
  return new Intl.NumberFormat("uz-UZ").format(Number(value));
}

function getError(data) {
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) return data.detail.join(" ");

  return Object.entries(data || {})
    .map(([key, value]) => `${key}: ${[].concat(value).join(", ")}`)
    .join(" | ") || "Xatolik yuz berdi.";
}

export default function TennisCourtsPage() {
  const [courts, setCourts] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadCourts = useCallback(async () => {
    setLoading(true);

    try {
      const response = await authFetch(API);
      if (!response.ok) {
        throw new Error(`Kortlar yuklanmadi (${response.status}).`);
      }

      const data = await response.json();
      setCourts(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCourts();
  }, [loadCourts]);

  function openCreate() {
    setEditingId(null);
    setForm({ ...EMPTY_FORM });
    setError("");
    setNotice("");
    setShowForm(true);
  }

  function openEdit(court) {
    setEditingId(court.id);
    setForm({
      name: court.name,
      description: court.description || "",
      monthly_price: String(court.monthly_price),
      status: court.status,
    });
    setError("");
    setNotice("");
    setShowForm(true);
  }

  async function saveCourt(event) {
    event.preventDefault();
    if (saving) return;

    setSaving(true);
    setError("");

    try {
      const response = await authFetch(
        editingId ? `${API}${editingId}/` : API,
        {
          method: editingId ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form),
        }
      );

      const data = await response.json();

      if (!response.ok) throw new Error(getError(data));

      setShowForm(false);
      setNotice(
        editingId
          ? "Tennis korti yangilandi."
          : "Yangi tennis korti yaratildi."
      );

      await loadCourts();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(court, action) {
    const question =
      action === "archive"
        ? `${court.name} arxivlansinmi?`
        : `${court.name} qayta faollashtirilsinmi?`;

    if (!window.confirm(question)) return;

    setBusyId(court.id);
    setError("");
    setNotice("");

    try {
      const response = await authFetch(
        `${API}${court.id}/${action}/`,
        { method: "POST" }
      );

      const data = await response.json();

      if (!response.ok) throw new Error(getError(data));

      setNotice(data.detail);
      await loadCourts();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  async function uploadImage(court, file) {
    if (!file) return;

    setBusyId(court.id);
    setError("");

    try {
      const formData = new FormData();
      formData.append("image", file);

      const response = await authFetch(
        `${API}${court.id}/images/`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) throw new Error(getError(data));

      setNotice("Rasm muvaffaqiyatli yuklandi.");
      await loadCourts();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  async function deleteImage(court, imageId) {
    if (!window.confirm("Rasm galereyadan o‘chirilsinmi?")) return;

    setBusyId(court.id);
    setError("");

    try {
      const response = await authFetch(
        `${API}${court.id}/images/${imageId}/`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        let data = {};
        try { data = await response.json(); } catch {}
        throw new Error(getError(data));
      }

      setNotice("Rasm o‘chirildi.");
      await loadCourts();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <main className="tennis-admin">
      <div className="tennis-admin-header">
        <div>
          <span className="tennis-admin-eyebrow">
            XUMO SPORT MAJMUASI
          </span>
          <h1>Tennis kortlari</h1>
          <p>Oylik narxlar, rasmlar va kortlarni boshqarish</p>
        </div>

        <button
          type="button"
          className="tennis-btn tennis-btn-primary"
          onClick={openCreate}
        >
          + Yangi kort
        </button>
      </div>

      {error && (
        <div className="tennis-alert tennis-alert-error" role="alert">
          {error}
        </div>
      )}

      {notice && (
        <div className="tennis-alert tennis-alert-success" role="status">
          {notice}
        </div>
      )}

      <div className="tennis-stats">
        <div>
          <span>Jami kortlar</span>
          <strong>{courts.length}</strong>
        </div>
        <div>
          <span>Faol</span>
          <strong>
            {courts.filter((c) => c.status === "active").length}
          </strong>
        </div>
        <div>
          <span>Arxivlangan</span>
          <strong>
            {courts.filter((c) => c.status === "archived").length}
          </strong>
        </div>
      </div>

      {showForm && (
        <section className="tennis-form-panel">
          <div className="tennis-form-title">
            <h2>{editingId ? "Kortni tahrirlash" : "Yangi kort"}</h2>
            <button type="button" onClick={() => setShowForm(false)}>
              ✕
            </button>
          </div>

          <form onSubmit={saveCourt}>
            <div className="tennis-form-grid">
              <label>
                Kort nomi
                <input
                  required
                  maxLength={150}
                  value={form.name}
                  onChange={(e) =>
                    setForm({ ...form, name: e.target.value })
                  }
                  placeholder="Tennis korti №1"
                />
              </label>

              <label>
                Oylik narx (so‘m)
                <input
                  type="number"
                  min="1"
                  step="0.01"
                  required
                  value={form.monthly_price}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      monthly_price: e.target.value,
                    })
                  }
                />
              </label>

              <label>
                Holati
                <select
                  value={form.status}
                  onChange={(e) =>
                    setForm({ ...form, status: e.target.value })
                  }
                >
                  <option value="active">Faol</option>
                  <option value="maintenance">Ta’mirlashda</option>
                  <option value="archived">Arxivlangan</option>
                </select>
              </label>
            </div>

            <label className="tennis-description">
              Kort haqida ma’lumot
              <textarea
                rows={4}
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
              />
            </label>

            <div className="tennis-form-actions">
              <button
                type="button"
                className="tennis-btn tennis-btn-secondary"
                onClick={() => setShowForm(false)}
              >
                Bekor qilish
              </button>
              <button
                type="submit"
                className="tennis-btn tennis-btn-primary"
                disabled={saving}
              >
                {saving ? "Saqlanmoqda..." : "Saqlash"}
              </button>
            </div>
          </form>
        </section>
      )}

      {loading ? (
        <p>Kortlar yuklanmoqda...</p>
      ) : courts.length === 0 ? (
        <div className="tennis-empty">
          Hozircha tennis kortlari yo‘q. Yangi kort yarating.
        </div>
      ) : (
        <div className="tennis-cards">
          {courts.map((court) => {
            const images = court.images || [];
            const primary =
              images.find((img) => img.is_primary) || images[0];

            return (
              <article className="tennis-card" key={court.id}>
                <div className="tennis-card-cover">
                  {primary ? (
                    <img src={primary.image} alt={court.name} />
                  ) : (
                    <span>🎾</span>
                  )}
                </div>

                <div className="tennis-card-content">
                  <div className="tennis-card-title">
                    <h3>{court.name}</h3>
                    <span className={`tennis-status ${court.status}`}>
                      {court.status_display || court.status}
                    </span>
                  </div>

                  <p>{court.description || "Tavsif kiritilmagan."}</p>

                  <div className="tennis-price">
                    {formatPrice(court.monthly_price)} so‘m
                    <small> / oy</small>
                  </div>

                  <div className="tennis-gallery">
                    {images.map((image) => (
                      <div key={image.id} className="tennis-thumbnail">
                        <img src={image.image} alt="" />
                        <button
                          type="button"
                          title="Rasmni o‘chirish"
                          disabled={busyId === court.id}
                          onClick={() => deleteImage(court, image.id)}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>

                  <div className="tennis-card-actions">
                    <button
                      type="button"
                      className="tennis-btn tennis-btn-secondary"
                      onClick={() => openEdit(court)}
                    >
                      Tahrirlash
                    </button>

                    <label className="tennis-btn tennis-btn-upload">
                      + Rasm
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        disabled={busyId === court.id}
                        onChange={async (e) => {
                          const file = e.target.files?.[0];
                          await uploadImage(court, file);
                          e.target.value = "";
                        }}
                      />
                    </label>

                    <button
                      type="button"
                      disabled={busyId === court.id}
                      className={`tennis-btn ${
                        court.status === "archived"
                          ? "tennis-btn-activate"
                          : "tennis-btn-danger"
                      }`}
                      onClick={() =>
                        changeStatus(
                          court,
                          court.status === "archived"
                            ? "activate"
                            : "archive"
                        )
                      }
                    >
                      {court.status === "archived"
                        ? "Qayta faollashtirish"
                        : "Arxivlash"}
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </main>
  );
}
