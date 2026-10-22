
import { useCallback, useEffect, useState } from "react";
import { authFetch } from "../../utils/auth";
import "./FootballFieldsPage.css";

const API = "/api/v1/football/fields/";

const EMPTY_FORM = {
  name: "",
  field_type: "summer",
  description: "",
  hourly_price: "100000",
  capacity: "",
  length_m: "",
  width_m: "",
  has_lighting: true,
  has_changing_room: false,
  status: "active",
};

function money(value) {
  return new Intl.NumberFormat("uz-UZ").format(Number(value));
}

function parseError(data) {
  if (typeof data?.detail === "string") return data.detail;

  if (Array.isArray(data?.detail)) {
    return data.detail.join(" ");
  }

  return Object.entries(data || {})
    .map(([key, value]) => `${key}: ${[].concat(value).join(", ")}`)
    .join(" | ") || "So‘rov bajarilmadi.";
}

export default function FootballFieldsPage() {
  const [fields, setFields] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [uploadingId, setUploadingId] = useState(null);

  const loadFields = useCallback(async () => {
    setLoading(true);
    try {
      const response = await authFetch(API);

      if (!response.ok) {
        throw new Error("Stadionlarni yuklashda xatolik.");
      }

      const data = await response.json();
      setFields(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFields();
  }, [loadFields]);

  function update(name, value) {
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function openCreate() {
    setEditingId(null);
    setForm({ ...EMPTY_FORM });
    setError("");
    setNotice("");
    setShowForm(true);
  }

  function openEdit(field) {
    setEditingId(field.id);
    setForm({
      name: field.name || "",
      field_type: field.field_type || "summer",
      description: field.description || "",
      hourly_price: String(field.hourly_price),
      capacity: field.capacity ?? "",
      length_m: field.length_m ?? "",
      width_m: field.width_m ?? "",
      has_lighting: Boolean(field.has_lighting),
      has_changing_room: Boolean(field.has_changing_room),
      status: field.status || "active",
    });
    setError("");
    setNotice("");
    setShowForm(true);
  }

  async function saveField(event) {
    event.preventDefault();
    if (saving) return;

    setSaving(true);
    setError("");

    const payload = {
      ...form,
      hourly_price: String(form.hourly_price),
      capacity: form.capacity === "" ? null : Number(form.capacity),
      length_m: form.length_m === "" ? null : Number(form.length_m),
      width_m: form.width_m === "" ? null : Number(form.width_m),
    };

    try {
      const response = await authFetch(
        editingId ? `${API}${editingId}/` : API,
        {
          method: editingId ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) throw new Error(parseError(data));

      setShowForm(false);
      setNotice(
        editingId ? "Stadion yangilandi." : "Yangi stadion yaratildi."
      );
      await loadFields();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function archiveField(field) {
    if (!window.confirm(`${field.name} arxivlansinmi?`)) return;

    setError("");
    setNotice("");

    try {
      const response = await authFetch(
        `${API}${field.id}/archive/`,
        { method: "POST" }
      );

      const data = await response.json();

      if (!response.ok) throw new Error(parseError(data));

      setNotice(`${field.name} arxivlandi.`);
      await loadFields();
    } catch (err) {
      setError(err.message);
    }
  }

async function activateField(field) {
  if (
    !window.confirm(
      `${field.name} stadionini qayta faollashtirasizmi?`
    )
  ) {
    return;
  }

  setError("");
  setNotice("");

  try {
    const response = await authFetch(
      `${API}${field.id}/activate/`,
      {
        method: "POST",
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(parseError(data));
    }

    setNotice(
      `${field.name} muvaffaqiyatli faollashtirildi.`
    );

    await loadFields();
  } catch (err) {
    setError(err.message);
  }
}


  async function uploadImage(field, file) {
    if (!file) return;

    setUploadingId(field.id);
    setError("");
    setNotice("");

    try {
      const body = new FormData();
      body.append("image", file);

      const response = await authFetch(
        `${API}${field.id}/images/`,
        {
          method: "POST",
          body,
        }
      );

      const data = await response.json();

      if (!response.ok) throw new Error(parseError(data));

      setNotice("Rasm yuklandi.");
      await loadFields();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploadingId(null);
    }
  }

  async function deleteImage(field, imageId) {
    if (!window.confirm("Rasm o‘chirilsinmi?")) return;

    setError("");

    try {
      const response = await authFetch(
        `${API}${field.id}/images/${imageId}/`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        throw new Error("Rasmni o‘chirishda xatolik.");
      }

      await loadFields();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="ff-dashboard">
      <header className="ff-header">
        <div>
          <span className="ff-eyebrow">XUMO SPORT MAJMUASI</span>
          <h1>Stadionlar boshqaruvi</h1>
          <p>Maydonlar, narxlar, rasmlar va holatlarni boshqarish</p>
        </div>

        <button className="ff-primary" onClick={openCreate}>
          + Yangi stadion
        </button>
      </header>

      {error && <div className="ff-alert ff-error">{error}</div>}
      {notice && <div className="ff-alert ff-success">{notice}</div>}

      <div className="ff-summary">
        <div>
          <span>Jami stadionlar</span>
          <strong>{fields.length}</strong>
        </div>
        <div>
          <span>Faol</span>
          <strong>
            {fields.filter((f) => f.status === "active").length}
          </strong>
        </div>
        <div>
          <span>Arxivlangan</span>
          <strong>
            {fields.filter((f) => f.status === "archived").length}
          </strong>
        </div>
      </div>

      {showForm && (
        <section className="ff-form-card">
          <div className="ff-form-heading">
            <h2>
              {editingId ? "Stadionni tahrirlash" : "Yangi stadion"}
            </h2>
            <button onClick={() => setShowForm(false)}>✕</button>
          </div>

          <form onSubmit={saveField}>
            <div className="ff-form-grid">
              <label>
                Stadion nomi
                <input
                  required
                  maxLength={150}
                  value={form.name}
                  onChange={(e) => update("name", e.target.value)}
                />
              </label>

              <label>
                Stadion turi
                <select
                  value={form.field_type}
                  onChange={(e) => update("field_type", e.target.value)}
                >
                  <option value="summer">Yozgi</option>
                  <option value="winter">Qishki</option>
                  <option value="other">Boshqa</option>
                </select>
              </label>

              <label>
                Soatlik narx (so‘m)
                <input
                  type="number"
                  min="0"
                  step="1"
                  required
                  value={form.hourly_price}
                  onChange={(e) => update("hourly_price", e.target.value)}
                />
              </label>

              <label>
                Sig‘imi (kishi)
                <input
                  type="number"
                  min="0"
                  value={form.capacity}
                  onChange={(e) => update("capacity", e.target.value)}
                />
              </label>

              <label>
                Uzunligi (metr)
                <input
                  type="number"
                  min="0"
                  value={form.length_m}
                  onChange={(e) => update("length_m", e.target.value)}
                />
              </label>

              <label>
                Kengligi (metr)
                <input
                  type="number"
                  min="0"
                  value={form.width_m}
                  onChange={(e) => update("width_m", e.target.value)}
                />
              </label>

              <label>
                Holati
                <select
                  value={form.status}
                  onChange={(e) => update("status", e.target.value)}
                >
                  <option value="active">Faol</option>
                  <option value="maintenance">Ta’mirlashda</option>
                  <option value="archived">Arxivlangan</option>
                </select>
              </label>

              <div className="ff-checks">
                <label>
                  <input
                    type="checkbox"
                    checked={form.has_lighting}
                    onChange={(e) =>
                      update("has_lighting", e.target.checked)
                    }
                  />
                  Yoritish mavjud
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={form.has_changing_room}
                    onChange={(e) =>
                      update("has_changing_room", e.target.checked)
                    }
                  />
                  Kiyinish xonasi mavjud
                </label>
              </div>
            </div>

            <label className="ff-description">
              Tavsif
              <textarea
                rows={4}
                value={form.description}
                onChange={(e) => update("description", e.target.value)}
              />
            </label>

            <div className="ff-form-actions">
              <button
                type="button"
                className="ff-secondary"
                onClick={() => setShowForm(false)}
              >
                Bekor qilish
              </button>
              <button
                className="ff-primary"
                type="submit"
                disabled={saving}
              >
                {saving ? "Saqlanmoqda..." : "Saqlash"}
              </button>
            </div>
          </form>
        </section>
      )}

      {loading ? (
        <p>Stadionlar yuklanmoqda...</p>
      ) : (
        <div className="ff-cards">
          {fields.map((field) => (
            <article className="ff-card" key={field.id}>
              <div className="ff-card-image">
                {field.images?.[0]?.image ? (
                  <img src={field.images[0].image} alt={field.name} />
                ) : (
                  <span>⚽</span>
                )}
              </div>

              <div className="ff-card-body">
                <div className="ff-card-top">
                  <h3>{field.name}</h3>
                  <span className={`ff-status ${field.status}`}>
                    {field.status_display}
                  </span>
                </div>

                <p>
                  {field.field_type_display}
                  {field.capacity ? ` · ${field.capacity} kishi` : ""}
                </p>

                <strong className="ff-price">
                  {money(field.hourly_price)} so‘m / soat
                </strong>

                <div className="ff-image-list">
                  {(field.images || []).map((image) => (
                    <div key={image.id}>
                      <img src={image.image} alt="" />
                      <button
                        type="button"
                        onClick={() => deleteImage(field, image.id)}
                        title="Rasmni o‘chirish"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>

                <div className="ff-card-actions">
                  <button
                    className="ff-secondary"
                    onClick={() => openEdit(field)}
                  >
                    Tahrirlash
                  </button>

                  <label className="ff-upload">
                    {uploadingId === field.id
                      ? "Yuklanmoqda..."
                      : "+ Rasm"}
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      disabled={uploadingId === field.id}
                      onChange={async (e) => {
                        await uploadImage(field, e.target.files?.[0]);
                        e.target.value = "";
                      }}
                    />
                  </label>


                    {field.status === "archived" ? (
                      <button
                        type="button"
                        className="ff-activate"
                        onClick={() => activateField(field)}
                      >
                        Qayta faollashtirish
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="ff-danger"
                        onClick={() => archiveField(field)}
                      >
                        Arxivlash
                      </button>
                    )}

                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
