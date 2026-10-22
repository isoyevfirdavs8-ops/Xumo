
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Pencil, Trash2, Images } from "lucide-react";

export default function BannerList() {
  const [banners, setBanners] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  const loadBanners = useCallback(async (signal) => {
    const token = sessionStorage.getItem("access_token");

    const response = await fetch("/api/v1/dashboard/banners/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      signal,
    });

    if (!response.ok) {
      throw new Error(`Bannerlarni olishda xatolik: HTTP ${response.status}`);
    }

    const data = await response.json();
    return Array.isArray(data) ? data : data.results || [];
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchBanners() {
      try {
        setBanners(await loadBanners(controller.signal));
      } catch (err) {
        if (err.name !== "AbortError") setError(err.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    fetchBanners();
    return () => controller.abort();
  }, [loadBanners]);

  async function handleDelete(banner) {
    if (!window.confirm(`"${banner.title}" bannerini o‘chirasizmi?`)) {
      return;
    }

    const token = sessionStorage.getItem("access_token");
    setDeletingId(banner.id);
    setError("");

    try {
      const response = await fetch(
        `/api/v1/dashboard/banners/${banner.id}/`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`O‘chirishda xatolik: HTTP ${response.status}`);
      }

      setBanners((prev) => prev.filter((item) => item.id !== banner.id));
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div>
      <div className="dashboard-page-heading">
        <h1>Bannerlar</h1>

        <Link
          to="/dashboard/banners/create"
          className="dashboard-primary-btn"
        >
          <Plus size={18} />
          Banner qo‘shish
        </Link>
      </div>

      {error && <p role="alert" className="banner-form-error">{error}</p>}

      <div className="dashboard-card">
        {loading && <p>Yuklanmoqda...</p>}

        {!loading && banners.length === 0 && !error && (
          <div style={{ textAlign: "center", padding: 40 }}>
            <Images size={42} color="#c79b4b" />
            <h3>Hozircha bannerlar yo‘q</h3>
            <p>Yuqoridagi tugma orqali birinchi bannerni qo‘shing.</p>
          </div>
        )}

        {!loading && banners.length > 0 && (
          <div style={{ display: "grid", gap: 16 }}>
            {banners.map((banner) => (
              <div
                key={banner.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 20,
                  flexWrap: "wrap",
                  border: "1px solid #e7eaf0",
                  padding: 15,
                  borderRadius: 12,
                }}
              >
                {banner.image && (
                  <img
                    src={banner.image}
                    alt={banner.title}
                    style={{
                      width: 160,
                      height: 90,
                      objectFit: "cover",
                      borderRadius: 9,
                    }}
                  />
                )}

                <div style={{ flex: 1, minWidth: 180 }}>
                  <h3>{banner.title}</h3>
                  <p>{banner.subtitle}</p>
                  <small>
                    {banner.is_active ? "Faol" : "Nofaol"}
                    {" · "}Tartib: {banner.sort_order}
                  </small>
                </div>

                <div style={{ display: "flex", gap: 8 }}>
                  <Link
                    to={`/dashboard/banners/${banner.id}/edit`}
                    className="dashboard-primary-btn"
                  >
                    <Pencil size={17} />
                    Tahrirlash
                  </Link>

                  <button
                    type="button"
                    onClick={() => handleDelete(banner)}
                    disabled={deletingId === banner.id}
                    style={{
                      border: "1px solid #fecaca",
                      background: "#fff1f2",
                      color: "#b42318",
                      borderRadius: 9,
                      padding: "10px 14px",
                      cursor: "pointer",
                    }}
                  >
                    <Trash2 size={17} />
                    {deletingId === banner.id ? "O‘chirilmoqda" : "O‘chirish"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
