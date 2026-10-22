
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Pencil, Trash2 } from "lucide-react";
import "../competitions/Competition.css";

const API = "/api/v1/dashboard/subcategories/";
const CATEGORY_API = "/api/v1/dashboard/categories/";

function authHeaders() {
  return {
    Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
  };
}

function errorText(data, fallback) {
  if (!data || typeof data !== "object") return fallback;
  return Object.entries(data)
    .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`)
    .join("\n") || fallback;
}

export default function SubCategoryPage() {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({
    category: "",
    name: "",
    slug: "",
    description: "",
    sort_order: 0,
    is_active: true,
  });
  const [image, setImage] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");

    try {
      const [subResponse, catResponse] = await Promise.all([
        fetch(API, { headers: authHeaders() }),
        fetch(CATEGORY_API, { headers: authHeaders() }),
      ]);

      if (!subResponse.ok || !catResponse.ok) {
        throw new Error("Ma’lumotlarni yuklashda xatolik.");
      }

      const [subData, catData] = await Promise.all([
        subResponse.json(),
        catResponse.json(),
      ]);

      setItems(Array.isArray(subData) ? subData : subData.results || []);
      setCategories(Array.isArray(catData) ? catData : catData.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function resetForm() {
    setEditingId(null);
    setImage(null);
    setForm({
      category: "",
      name: "",
      slug: "",
      description: "",
      sort_order: 0,
      is_active: true,
    });
  }

  function edit(item) {
    setEditingId(item.id);
    setImage(null);
    setForm({
      category: String(item.category),
      name: item.name,
      slug: item.slug,
      description: item.description || "",
      sort_order: item.sort_order,
      is_active: item.is_active,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function save(event) {
    event.preventDefault();
    if (saving) return;

    setSaving(true);
    setError("");

    const body = new FormData();
    Object.entries(form).forEach(([key, value]) => {
      body.append(key, String(value));
    });
    if (image) body.append("image", image);

    try {
      const response = await fetch(
        editingId ? `${API}${editingId}/` : API,
        {
          method: editingId ? "PATCH" : "POST",
          headers: authHeaders(),
          body,
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(errorText(data, "Saqlashda xatolik."));
      }

      resetForm();
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function remove(item) {
    if (!window.confirm(`"${item.name}" o‘chirilsinmi?`)) return;

    try {
      const response = await fetch(`${API}${item.id}/`, {
        method: "DELETE",
        headers: authHeaders(),
      });

      if (!response.ok) {
        throw new Error(
          "Subkategoriyani o‘chirib bo‘lmadi. Unga taomlar bog‘langan bo‘lishi mumkin."
        );
      }

      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="dc-page">
      <div className="dc-page-header">
        <div>
          <span className="dc-eyebrow">FC BUKHARA / DASHBOARD</span>
          <h1>Subkategoriyalar</h1>
          <p>Restoran menyusi bo‘limlarini boshqarish</p>
        </div>
        <Link className="dc-primary-button" to="/dashboard/foods">
          Taomlarga o‘tish
        </Link>
      </div>

      {error && <div className="dc-error">{error}</div>}

      <form className="dc-form" onSubmit={save}>
        <h2>{editingId ? "Subkategoriyani tahrirlash" : "Yangi subkategoriya"}</h2>

        <div className="dc-form-grid">
          <div className="dc-field">
            <label>Kategoriya *</label>
            <select
              required
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            >
              <option value="">Kategoriya tanlang</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          <div className="dc-field">
            <label>Nomi *</label>
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Milliy taomlar"
            />
          </div>

          <div className="dc-field">
            <label>Slug *</label>
            <input
              required
              value={form.slug}
              onChange={(e) => setForm({ ...form, slug: e.target.value })}
              placeholder="milliy-taomlar"
            />
          </div>

          <div className="dc-field">
            <label>Tartib raqami</label>
            <input
              type="number"
              min="0"
              value={form.sort_order}
              onChange={(e) => setForm({ ...form, sort_order: e.target.value })}
            />
          </div>
        </div>

        <div className="dc-field">
          <label>Tavsif</label>
          <textarea
            rows={3}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>

        <div className="dc-field">
          <label>Rasm</label>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setImage(e.target.files?.[0] || null)}
          />
        </div>

        <label className="dc-checkbox">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
          />
          Faol
        </label>

        <div className="dc-form-actions">
          {editingId && (
            <button type="button" className="dc-cancel-button" onClick={resetForm}>
              Bekor qilish
            </button>
          )}
          <button className="dc-primary-button" disabled={saving}>
            <Plus size={17} />
            {saving ? "Saqlanmoqda..." : editingId ? "Saqlash" : "Yaratish"}
          </button>
        </div>
      </form>

      <h2 style={{ marginTop: 32 }}>Subkategoriyalar ro‘yxati</h2>

      {loading ? (
        <p>Yuklanmoqda...</p>
      ) : (
        <div className="dc-list">
          {items.map((item) => (
            <article className="dc-competition-card" key={item.id}>
              <div className="dc-card-image">
                {item.image && <img src={item.image} alt={item.name} />}
              </div>
              <div className="dc-card-body">
                <h3>{item.name}</h3>
                <p className="dc-description">{item.description}</p>
                <p>Slug: {item.slug}</p>
                <p>{item.is_active ? "Faol" : "Nofaol"}</p>
                <div className="dc-card-actions">
                  <button className="dc-edit-button" onClick={() => edit(item)}>
                    <Pencil size={16} /> Tahrirlash
                  </button>
                  <button className="dc-delete-button" onClick={() => remove(item)}>
                    <Trash2 size={16} /> O‘chirish
                  </button>
                </div>
              </div>
            </article>
          ))}
          {items.length === 0 && <p>Subkategoriyalar mavjud emas.</p>}
        </div>
      )}
    </div>
  );
}
