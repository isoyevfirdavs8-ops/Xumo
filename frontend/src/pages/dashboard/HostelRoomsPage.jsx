
import { useEffect, useState } from "react";
import {
  createHostelRoom,
  deleteHostelRoomImage,
  getHostelRooms,
  setPrimaryHostelRoomImage,
  updateHostelRoom,
  uploadHostelRoomImage,
} from "../../services/hostelApi";
import "./HostelRoomsPage.css";

const initialForm = {
  number: "",
  name: "",
  description: "",
  capacity: 3,
  daily_price: "",
  status: "active",
};

const capacities = [
  { value: 2, label: "2 kishilik" },
  { value: 3, label: "3 kishilik" },
  { value: 4, label: "4 kishilik" },
];

function normalizeList(data) {
  return Array.isArray(data)
    ? data
    : Array.isArray(data?.results)
      ? data.results
      : [];
}

function formatPrice(price) {
  return new Intl.NumberFormat("uz-UZ").format(Number(price || 0));
}

export default function HostelRoomsPage() {
  const [rooms, setRooms] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyImageId, setBusyImageId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadRooms() {
    setLoading(true);
    try {
      const data = await getHostelRooms();
      setRooms(normalizeList(data));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRooms();
  }, []);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function resetForm() {
    setForm(initialForm);
    setEditingId(null);
  }

  function startEdit(room) {
    setEditingId(room.id);
    setForm({
      number: room.number,
      name: room.name,
      description: room.description || "",
      capacity: room.capacity,
      daily_price: room.daily_price,
      status: room.status,
    });
    setError("");
    setMessage("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (saving) return;

    setSaving(true);
    setError("");
    setMessage("");

    const payload = {
      ...form,
      capacity: Number(form.capacity),
      daily_price: String(form.daily_price),
    };

    try {
      if (editingId) {
        await updateHostelRoom(editingId, payload);
        setMessage("Xona muvaffaqiyatli yangilandi.");
      } else {
        await createHostelRoom(payload);
        setMessage("Yangi xona yaratildi.");
      }

      resetForm();
      await loadRooms();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleArchive(room) {
    if (!window.confirm(`${room.number}-xonani arxivlaysizmi?`)) {
      return;
    }

    setError("");
    try {
      await updateHostelRoom(room.id, { status: "archived" });
      setMessage("Xona arxivlandi.");
      await loadRooms();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleUpload(roomId, file) {
    if (!file) return;

    setBusyImageId(roomId);
    setError("");

    try {
      await uploadHostelRoomImage(roomId, file);
      setMessage("Rasm yuklandi.");
      await loadRooms();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyImageId(null);
    }
  }

  async function handleDeleteImage(roomId, imageId) {
    if (!window.confirm("Rasmni o'chirasizmi?")) return;

    setBusyImageId(roomId);
    setError("");

    try {
      await deleteHostelRoomImage(roomId, imageId);
      setMessage("Rasm o'chirildi.");
      await loadRooms();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyImageId(null);
    }
  }

  async function handlePrimary(roomId, imageId) {
    setBusyImageId(roomId);
    setError("");

    try {
      await setPrimaryHostelRoomImage(roomId, imageId);
      setMessage("Asosiy rasm belgilandi.");
      await loadRooms();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyImageId(null);
    }
  }

  return (
    <main className="hostel-dashboard">
      <header className="hostel-dashboard-header">
        <div>
          <span>XUMO SPORT MAJMUASI</span>
          <h1>Yotoqxona xonalari</h1>
          <p>Xonalar, narxlar va rasmlarni boshqarish.</p>
        </div>
        <strong>{rooms.length} ta xona</strong>
      </header>

      {error && <p className="hostel-alert error" role="alert">{error}</p>}
      {message && <p className="hostel-alert success" role="status">{message}</p>}

      <section className="hostel-dashboard-form">
        <h2>{editingId ? "Xonani tahrirlash" : "Yangi xona yaratish"}</h2>

        <form onSubmit={handleSubmit}>
          <div className="hostel-form-grid">
            <label>
              Xona raqami
              <input
                required
                maxLength={20}
                value={form.number}
                onChange={(e) => update("number", e.target.value)}
                placeholder="101"
              />
            </label>

            <label>
              Xona nomi
              <input
                required
                maxLength={150}
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                placeholder="3 kishilik standart xona"
              />
            </label>

            <label>
              Sig'imi
              <select
                value={form.capacity}
                onChange={(e) => update("capacity", Number(e.target.value))}
              >
                {capacities.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Kunlik narx (so'm)
              <input
                required
                type="number"
                min="1"
                step="0.01"
                value={form.daily_price}
                onChange={(e) => update("daily_price", e.target.value)}
              />
            </label>

            <label>
              Holati
              <select
                value={form.status}
                onChange={(e) => update("status", e.target.value)}
              >
                <option value="active">Faol</option>
                <option value="maintenance">Ta'mirlashda</option>
                <option value="archived">Arxivlangan</option>
              </select>
            </label>
          </div>

          <label className="hostel-description-label">
            Tavsif
            <textarea
              rows={3}
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
            />
          </label>

          <div className="hostel-form-actions">
            <button type="submit" disabled={saving}>
              {saving
                ? "Saqlanmoqda..."
                : editingId
                  ? "O'zgarishlarni saqlash"
                  : "Xona yaratish"}
            </button>
            {editingId && (
              <button type="button" className="secondary" onClick={resetForm}>
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="hostel-dashboard-list">
        <h2>Yaratilgan xonalar</h2>

        {loading ? (
          <p>Xonalar yuklanmoqda...</p>
        ) : rooms.length === 0 ? (
          <p>Hozircha xona yaratilmagan.</p>
        ) : (
          <div className="hostel-room-grid">
            {rooms.map((room) => (
              <article key={room.id} className="hostel-room-card">
                <div className="hostel-room-image">
                  {room.images?.[0]?.image ? (
                    <img src={room.images[0].image} alt={room.name} />
                  ) : (
                    <span>🛏️</span>
                  )}
                </div>

                <div className="hostel-room-content">
                  <div className="hostel-room-title">
                    <h3>{room.name}</h3>
                    <span>{room.number}</span>
                  </div>

                  <p>{room.capacity} kishilik xona</p>
                  <strong>{formatPrice(room.daily_price)} so'm / kun</strong>
                  <p>Holati: {room.status}</p>

                  <div className="hostel-room-actions">
                    <button type="button" onClick={() => startEdit(room)}>
                      Tahrirlash
                    </button>
                    {room.status !== "archived" && (
                      <button
                        type="button"
                        className="danger"
                        onClick={() => handleArchive(room)}
                      >
                        Arxivlash
                      </button>
                    )}
                  </div>

                  <div className="hostel-image-manager">
                    <label>
                      Rasm yuklash
                      <input
                        type="file"
                        accept="image/*"
                        disabled={busyImageId === room.id}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          handleUpload(room.id, file);
                          e.target.value = "";
                        }}
                      />
                    </label>

                    {room.images?.map((image) => (
                      <div key={image.id} className="hostel-image-row">
                        <img src={image.image} alt="" />
                        <span>{image.is_primary ? "Asosiy" : "Rasm"}</span>

                        {!image.is_primary && (
                          <button
                            type="button"
                            disabled={busyImageId === room.id}
                            onClick={() => handlePrimary(room.id, image.id)}
                          >
                            Asosiy
                          </button>
                        )}

                        <button
                          type="button"
                          className="danger"
                          disabled={busyImageId === room.id}
                          onClick={() => handleDeleteImage(room.id, image.id)}
                        >
                          O'chirish
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
