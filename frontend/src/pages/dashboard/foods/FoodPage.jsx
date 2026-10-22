
import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2 } from "lucide-react";
import "../competitions/Competition.css";

const FOOD_API = "/api/v1/dashboard/foods/";
const SUB_API = "/api/v1/dashboard/subcategories/";

const emptyForm = {
  subcategory: "",
  name: "",
  description: "",
  price: "",
  stock: "0",
  sort_order: "0",
  is_active: true,
};

function headers() {
  return {
    Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
  };
}

function parseError(data) {
  if (!data || typeof data !== "object") return "So‘rov bajarilmadi.";
  return Object.entries(data)
    .map(([field, message]) =>
      `${field}: ${Array.isArray(message) ? message.join(", ") : message}`
    )
    .join("\n");
}

export default function FoodPage() {
  const [foods, setFoods] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [image, setImage] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");

    try {
      const [foodResponse, subResponse] = await Promise.all([
        fetch(FOOD_API, { headers: headers() }),
        fetch(SUB_API, { headers: headers() }),
      ]);

      if (!foodResponse.ok || !subResponse.ok) {
        throw new Error("Taomlar yoki subkategoriyalarni olib bo‘lmadi.");
      }

      const [foodData, subData] = await Promise.all([
        foodResponse.json(),
        subResponse.json(),
      ]);

      setFoods(Array.isArray(foodData) ? foodData : foodData.results || []);
      setSubcategories(Array.isArray(subData) ? subData : subData.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function reset() {
    setForm(emptyForm);
    setImage(null);
    setEditingId(null);
  }

  function edit(food) {
    setEditingId(food.id);
    setImage(null);
    setForm({
      subcategory: String(food.subcategory),
      name: food.name,
      description: food.description || "",
      price: String(food.price),
      stock: String(food.stock),
      sort_order: String(food.sort_order),
      is_active: food.is_active,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function change(event) {
    const { name, value, type, checked } = event.target;
    setForm((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
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
        editingId ? `${FOOD_API}${editingId}/` : FOOD_API,
        {
          method: editingId ? "PATCH" : "POST",
          headers: headers(),
          body,
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(parseError(data));
      }

      reset();
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function remove(food) {
    if (!window.confirm(`"${food.name}" taomini o‘chirasizmi?`)) return;

    try {
      const response = await fetch(`${FOOD_API}${food.id}/`, {
        method: "DELETE",
        headers: headers(),
      });

      if (!response.ok) {
        throw new Error(
          "Taomni o‘chirib bo‘lmadi. Uni nofaol holatga o‘tkazishingiz mumkin."
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
          <h1>Restoran taomlari</h1>
          <p>Taomlar, narxlar va ombor qoldig‘ini boshqarish</p>
        </div>
      </div>

      {error && <div className="dc-error" role="alert">{error}</div>}

      <form className="dc-form" onSubmit={save}>
        <h2>{editingId ? "Taomni tahrirlash" : "Yangi taom"}</h2>

        <div className="dc-form-grid">
          <div className="dc-field">
            <label>Subkategoriya *</label>
            <select
              name="subcategory"
              value={form.subcategory}
              onChange={change}
              required
            >
              <option value="">Tanlang</option>
              {subcategories.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          <div className="dc-field">
            <label>Taom nomi *</label>
            <input
              name="name"
              value={form.name}
              onChange={change}
              placeholder="Osh"
              required
            />
          </div>

          <div className="dc-field">
            <label>Narxi (so‘m) *</label>
            <input
              name="price"
              type="number"
              min="0"
              step="0.01"
              value={form.price}
              onChange={change}
              required
            />
          </div>

          <div className="dc-field">
            <label>Stock (dona) *</label>
            <input
              name="stock"
              type="number"
              min="0"
              step="1"
              value={form.stock}
              onChange={change}
              required
            />
          </div>

          <div className="dc-field">
            <label>Tartib raqami</label>
            <input
              name="sort_order"
              type="number"
              min="0"
              value={form.sort_order}
              onChange={change}
            />
          </div>
        </div>

        <div className="dc-field">
          <label>Tavsif</label>
          <textarea
            name="description"
            rows={4}
            value={form.description}
            onChange={change}
          />
        </div>

        <div className="dc-field">
          <label>Taom rasmi</label>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) =>
              setImage(event.target.files?.[0] || null)
            }
          />
        </div>

        <label className="dc-checkbox">
          <input
            name="is_active"
            type="checkbox"
            checked={form.is_active}
            onChange={change}
          />
          Taom faol
        </label>

        <div className="dc-form-actions">
          {editingId && (
            <button type="button" className="dc-cancel-button" onClick={reset}>
              Bekor qilish
            </button>
          )}
          <button type="submit" className="dc-primary-button" disabled={saving}>
            <Plus size={18} />
            {saving ? "Saqlanmoqda..." : editingId ? "Saqlash" : "Taom qo‘shish"}
          </button>
        </div>
      </form>

      <h2 style={{ marginTop: 32 }}>Taomlar ro‘yxati</h2>

      {loading ? (
        <p>Yuklanmoqda...</p>
      ) : (
        <div className="dc-list">
          {foods.map((food) => (
            <article className="dc-competition-card" key={food.id}>
              <div className="dc-card-image">
                {food.image && <img src={food.image} alt={food.name} />}
              </div>

              <div className="dc-card-body">
                <h3>{food.name}</h3>
                <p className="dc-description">{food.description}</p>

                <div className="dc-card-meta">
                  <span>{food.subcategory_name}</span>
                  <span>{Number(food.price).toLocaleString("uz-UZ")} so‘m</span>
                  <span>Stock: {food.stock}</span>
                  <span>{food.is_active ? "Faol" : "Nofaol"}</span>
                </div>

                <div className="dc-card-actions">
                  <button className="dc-edit-button" onClick={() => edit(food)}>
                    <Pencil size={16} /> Tahrirlash
                  </button>
                  <button className="dc-delete-button" onClick={() => remove(food)}>
                    <Trash2 size={16} /> O‘chirish
                  </button>
                </div>
              </div>
            </article>
          ))}

          {foods.length === 0 && <p>Taomlar mavjud emas.</p>}
        </div>
      )}
    </div>
  );
}
