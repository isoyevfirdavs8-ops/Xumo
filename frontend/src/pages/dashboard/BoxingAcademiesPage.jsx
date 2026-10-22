
import { useCallback, useEffect, useState } from "react";
import {
  Plus,
  Pencil,
  Archive,
  RotateCcw,
  ImagePlus,
  Trash2,
  Star,
  X,
  Dumbbell,
} from "lucide-react";

import { authFetch } from "../../utils/auth";
import "./BoxingAcademiesPage.css";

const API = "/api/v1/boxing/academies/";

const EMPTY_FORM = {
  name: "",
  description: "",
  monthly_price: "",
  status: "active",
};

const STATUS_LABELS = {
  active: "Faol",
  maintenance: "Ta'mirlashda",
  archived: "Arxivlangan",
};

function formatPrice(value) {
  return new Intl.NumberFormat("uz-UZ").format(Number(value));
}

function getError(data) {
  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (Array.isArray(data?.detail)) {
    return data.detail.join(", ");
  }

  return (
    Object.entries(data || {})
      .map(([key, value]) => {
        const message = Array.isArray(value)
          ? value.join(", ")
          : typeof value === "object" && value !== null
            ? JSON.stringify(value)
            : String(value);

        return `${key}: ${message}`;
      })
      .join(" | ") || "Xatolik yuz berdi."
  );
}

async function parseResponse(response) {
  if (response.status === 204) return null;

  const text = await response.text();

  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    throw new Error(
      `Server JSON o'rniga boshqa javob qaytardi (${response.status}).`
    );
  }
}

export default function BoxingAcademiesPage() {
  const [academies, setAcademies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState(null);

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });

  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadAcademies = useCallback(async () => {
    setLoading(true);

    try {
      const response = await authFetch(API);
      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(getError(data));
      }

      setAcademies(
        Array.isArray(data) ? data : data?.results || []
      );
    } catch (err) {
      setError(err.message || "Akademiyalar yuklanmadi.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAcademies();
  }, [loadAcademies]);

  function openCreate() {
    setEditingId(null);
    setForm({ ...EMPTY_FORM });
    setError("");
    setNotice("");
    setShowForm(true);
  }

  function openEdit(academy) {
    setEditingId(academy.id);

    setForm({
      name: academy.name,
      description: academy.description || "",
      monthly_price: String(academy.monthly_price),
      status: academy.status,
    });

    setError("");
    setNotice("");
    setShowForm(true);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  function closeForm() {
    if (saving) return;
    setShowForm(false);
    setEditingId(null);
    setForm({ ...EMPTY_FORM });
  }

  async function saveAcademy(event) {
    event.preventDefault();

    if (saving) return;

    setSaving(true);
    setError("");
    setNotice("");

    try {
      const response = await authFetch(
        editingId ? `${API}${editingId}/` : API,
        {
          method: editingId ? "PATCH" : "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: form.name.trim(),
            description: form.description.trim(),
            monthly_price: form.monthly_price,
            status: form.status,
          }),
        }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(getError(data));
      }

      setShowForm(false);
      setEditingId(null);
      setForm({ ...EMPTY_FORM });

      setNotice(
        editingId
          ? "Boks akademiyasi yangilandi."
          : "Boks akademiyasi yaratildi."
      );

      await loadAcademies();
    } catch (err) {
      setError(err.message || "Saqlashda xatolik.");
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(academy, action) {
    const question =
      action === "archive"
        ? `"${academy.name}" arxivlansinmi?`
        : `"${academy.name}" qayta faollashtirilsinmi?`;

    if (!window.confirm(question)) return;

    setBusyId(academy.id);
    setError("");
    setNotice("");

    try {
      const response = await authFetch(
        `${API}${academy.id}/${action}/`,
        { method: "POST" }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(getError(data));
      }

      setNotice(
        data?.detail || "Akademiya holati yangilandi."
      );

      await loadAcademies();
    } catch (err) {
      setError(err.message || "Holatni o'zgartirib bo'lmadi.");
    } finally {
      setBusyId(null);
    }
  }

  async function uploadImage(academy, file) {
    if (!file || busyId !== null) return;

    if (file.size > 5 * 1024 * 1024) {
      setError("Rasm hajmi 5 MB dan oshmasligi kerak.");
      return;
    }

    setBusyId(academy.id);
    setError("");
    setNotice("");

    try {
      const formData = new FormData();
      formData.append("image", file);

      const response = await authFetch(
        `${API}${academy.id}/images/`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(getError(data));
      }

      setNotice("Rasm muvaffaqiyatli yuklandi.");
      await loadAcademies();
    } catch (err) {
      setError(err.message || "Rasm yuklanmadi.");
    } finally {
      setBusyId(null);
    }
  }

  async function deleteImage(academy, imageId) {
    if (busyId !== null) return;

    if (!window.confirm("Rasm galereyadan o'chirilsinmi?")) {
      return;
    }

    setBusyId(academy.id);
    setError("");
    setNotice("");

    try {
      const response = await authFetch(
        `${API}${academy.id}/images/${imageId}/`,
        { method: "DELETE" }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(getError(data));
      }

      setNotice("Rasm galereyadan o'chirildi.");
      await loadAcademies();
    } catch (err) {
      setError(err.message || "Rasmni o'chirib bo'lmadi.");
    } finally {
      setBusyId(null);
    }
  }

  async function setPrimaryImage(academy, imageId) {
    if (busyId !== null) return;

    setBusyId(academy.id);
    setError("");
    setNotice("");

    try {
      const response = await authFetch(
        `${API}${academy.id}/images/${imageId}/primary/`,
        { method: "POST" }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(getError(data));
      }

      setNotice("Asosiy rasm yangilandi.");
      await loadAcademies();
    } catch (err) {
      setError(err.message || "Asosiy rasm o'zgarmadi.");
    } finally {
      setBusyId(null);
    }
  }

  const activeCount = academies.filter(
    (academy) => academy.status === "active"
  ).length;

  const archivedCount = academies.filter(
    (academy) => academy.status === "archived"
  ).length;

  return (
    <main className="boxing-admin">
      <header className="boxing-admin-header">
        <div>
          <span className="boxing-eyebrow">
            XUMO SPORT MAJMUASI
          </span>
          <h1>Boks akademiyalari</h1>
          <p>
            Akademiyalar, oylik narxlar va rasmlarni
            boshqarish
          </p>
        </div>

        <button
          type="button"
          className="boxing-btn boxing-btn-primary"
          onClick={openCreate}
        >
          <Plus size={17} />
          Yangi akademiya
        </button>
      </header>

      {error && (
        <div className="boxing-alert boxing-alert-error" role="alert">
          {error}
        </div>
      )}

      {notice && (
        <div className="boxing-alert boxing-alert-success" role="status">
          {notice}
        </div>
      )}

      <div className="boxing-stats">
        <div className="boxing-stat">
          <span>Jami akademiyalar</span>
          <strong>{academies.length}</strong>
        </div>

        <div className="boxing-stat">
          <span>Faol</span>
          <strong>{activeCount}</strong>
        </div>

        <div className="boxing-stat">
          <span>Arxivlangan</span>
          <strong>{archivedCount}</strong>
        </div>
      </div>

      {showForm && (
        <section className="boxing-form-panel">
          <div className="boxing-form-heading">
            <h2>
              {editingId
                ? "Akademiyani tahrirlash"
                : "Yangi akademiya"}
            </h2>

            <button
              type="button"
              className="boxing-icon-button"
              onClick={closeForm}
              aria-label="Formani yopish"
            >
              <X size={20} />
            </button>
          </div>

          <form onSubmit={saveAcademy}>
            <div className="boxing-form-grid">
              <label>
                Akademiya nomi
                <input
                  required
                  maxLength={150}
                  value={form.name}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      name: event.target.value,
                    })
                  }
                  placeholder="XUMO Boks Akademiyasi"
                />
              </label>

              <label>
                Oylik narx (so'm)
                <input
                  type="number"
                  required
                  min="0.01"
                  step="0.01"
                  value={form.monthly_price}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      monthly_price: event.target.value,
                    })
                  }
                  placeholder="300000"
                />
              </label>

              <label>
                Holati
                <select
                  value={form.status}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      status: event.target.value,
                    })
                  }
                >
                  <option value="active">Faol</option>
                  <option value="maintenance">
                    Ta'mirlashda
                  </option>
                  <option value="archived">
                    Arxivlangan
                  </option>
                </select>
              </label>
            </div>

            <label className="boxing-description-label">
              Akademiya haqida
              <textarea
                rows={4}
                value={form.description}
                onChange={(event) =>
                  setForm({
                    ...form,
                    description: event.target.value,
                  })
                }
                placeholder="Boks mashg'ulotlari haqida..."
              />
            </label>

            <div className="boxing-form-actions">
              <button
                type="button"
                className="boxing-btn boxing-btn-secondary"
                onClick={closeForm}
              >
                Bekor qilish
              </button>

              <button
                type="submit"
                className="boxing-btn boxing-btn-primary"
                disabled={saving}
              >
                {saving ? "Saqlanmoqda..." : "Saqlash"}
              </button>
            </div>
          </form>
        </section>
      )}

      {loading ? (
        <div className="boxing-empty">
          Akademiyalar yuklanmoqda...
        </div>
      ) : academies.length === 0 ? (
        <div className="boxing-empty">
          <Dumbbell size={40} />
          <h3>Hozircha akademiyalar mavjud emas</h3>
          <p>Yangi boks akademiyasini yarating.</p>
        </div>
      ) : (
        <div className="boxing-cards">
          {academies.map((academy) => {
            const images = academy.images || [];
            const primary =
              images.find((image) => image.is_primary) ||
              images[0];

            const isBusy = busyId !== null;

            return (
              <article
                key={academy.id}
                className="boxing-card"
              >
                <div className="boxing-card-cover">
                  {primary ? (
                    <img
                      src={primary.image}
                      alt={academy.name}
                    />
                  ) : (
                    <div className="boxing-cover-placeholder">
                      <Dumbbell size={56} />
                    </div>
                  )}

                  <span
                    className={`boxing-status ${academy.status}`}
                  >
                    {STATUS_LABELS[academy.status] ||
                      academy.status}
                  </span>
                </div>

                <div className="boxing-card-body">
                  <h3>{academy.name}</h3>

                  <p className="boxing-card-description">
                    {academy.description ||
                      "Tavsif kiritilmagan."}
                  </p>

                  <div className="boxing-card-price">
                    {formatPrice(academy.monthly_price)}
                    <small> so'm / oy</small>
                  </div>

                  <div className="boxing-gallery">
                    {images.map((image) => (
                      <div
                        key={image.id}
                        className="boxing-gallery-item"
                      >
                        <img
                          src={image.image}
                          alt={`${academy.name} rasmi`}
                        />

                        {image.is_primary && (
                          <span
                            className="boxing-primary-badge"
                            title="Asosiy rasm"
                          >
                            <Star size={12} fill="currentColor" />
                          </span>
                        )}

                        <div className="boxing-gallery-actions">
                          {!image.is_primary && (
                            <button
                              type="button"
                              title="Asosiy rasm qilish"
                              disabled={isBusy}
                              onClick={() =>
                                setPrimaryImage(
                                  academy,
                                  image.id
                                )
                              }
                            >
                              <Star size={14} />
                            </button>
                          )}

                          <button
                            type="button"
                            title="Rasmni o'chirish"
                            disabled={isBusy}
                            onClick={() =>
                              deleteImage(
                                academy,
                                image.id
                              )
                            }
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="boxing-card-actions">
                    <button
                      type="button"
                      className="boxing-btn boxing-btn-secondary"
                      onClick={() => openEdit(academy)}
                    >
                      <Pencil size={15} />
                      Tahrirlash
                    </button>

                    <label className="boxing-btn boxing-btn-upload">
                      <ImagePlus size={15} />
                      Rasm qo'shish

                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        disabled={isBusy}
                        onChange={async (event) => {
                          const file = event.target.files?.[0];
                          await uploadImage(academy, file);
                          event.target.value = "";
                        }}
                      />
                    </label>

                    {academy.status === "archived" ? (
                      <button
                        type="button"
                        className="boxing-btn boxing-btn-activate"
                        disabled={isBusy}
                        onClick={() =>
                          changeStatus(academy, "activate")
                        }
                      >
                        <RotateCcw size={15} />
                        Qayta faollashtirish
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="boxing-btn boxing-btn-danger"
                        disabled={isBusy}
                        onClick={() =>
                          changeStatus(academy, "archive")
                        }
                      >
                        <Archive size={15} />
                        Arxivlash
                      </button>
                    )}
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
