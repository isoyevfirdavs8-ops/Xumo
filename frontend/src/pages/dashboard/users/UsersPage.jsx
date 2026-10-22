import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Users, UserRound, ShieldCheck, CheckCircle2, XCircle, ChevronLeft, ChevronRight, RefreshCw, X, Phone, Mail, CalendarDays, AlertCircle } from "lucide-react";
import { authFetch } from "../../../utils/auth";
import "./UsersPage.css";

const API = "/api/v1/dashboard/users/";
const fmtDate = (value) => value ? new Intl.DateTimeFormat("uz-UZ", { year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(value)) : "—";
const roleText = (role) => ({ admin: "Administrator", manager: "Menejer", coach: "Murabbiy", student: "Foydalanuvchi", user: "Foydalanuvchi", client: "Foydalanuvchi" }[role] || role || "—");
const initials = (name) => (name || "U").trim().split(/\s+/).slice(0, 2).map((part) => part[0]?.toUpperCase() || "").join("");

export default function UsersPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [role, setRole] = useState("");
  const [active, setActive] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ count: 0, results: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [selected, setSelected] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    const timeout = setTimeout(() => setDebouncedSearch(search.trim()), 350);
    return () => clearTimeout(timeout);
  }, [search]);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = new URLSearchParams({ page: String(page), page_size: "20" });
        if (debouncedSearch) params.set("search", debouncedSearch);
        if (role) params.set("role", role);
        if (active) params.set("is_active", active);
        const response = await authFetch(`${API}?${params}`, { signal: controller.signal });
        if (response.status === 401) { navigate("/login", { replace: true }); return; }
        if (response.status === 403) throw new Error("Foydalanuvchilar ro'yxatini ko'rish uchun admin huquqi talab qilinadi.");
        if (!response.ok) throw new Error(`Ma'lumotlarni olishda xatolik (HTTP ${response.status}).`);
        const payload = await response.json();
        if (!controller.signal.aborted) setData({ count: payload.count ?? 0, results: Array.isArray(payload.results) ? payload.results : [] });
      } catch (err) {
        if (!controller.signal.aborted && err.name !== "AbortError") setError(err.message || "Ma'lumotlarni yuklab bo'lmadi.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    load();
    return () => controller.abort();
  }, [debouncedSearch, role, active, page, refresh, navigate]);

  async function showDetails(id) {
    setSelected(null);
    setDetailError("");
    setDetailLoading(true);
    try {
      const response = await authFetch(`${API}${id}/`);
      if (response.status === 401) { navigate("/login", { replace: true }); return; }
      if (!response.ok) throw new Error(`Foydalanuvchini yuklab bo'lmadi (HTTP ${response.status}).`);
      setSelected(await response.json());
    } catch (err) {
      setDetailError(err.message || "Xatolik yuz berdi.");
    } finally {
      setDetailLoading(false);
    }
  }

  const totalPages = Math.max(1, Math.ceil(data.count / 20));
  const clearFilters = () => { setSearch(""); setRole(""); setActive(""); setPage(1); };
  return (
    <main className="xu-users">
      <div className="xu-users__heading">
        <div>
          <div className="xu-users__eyebrow">DASHBOARD / FOYDALANUVCHILAR</div>
          <h1>Foydalanuvchilar</h1>
          <p>Ro'yxatdan o'tgan foydalanuvchilarni kuzatish va qidirish.</p>
        </div>
        <button type="button" className="xu-users__refresh" onClick={() => setRefresh((n) => n + 1)} disabled={loading}><RefreshCw size={17} /> Yangilash</button>
      </div>
      <div className="xu-users__stats">
        <div className="xu-users__stat"><span><Users size={20} /></span><div><small>Jami foydalanuvchilar (joriy filtr)</small><strong>{data.count.toLocaleString("uz-UZ")}</strong></div></div>
        <div className="xu-users__stat"><span><UserRound size={20} /></span><div><small>Ushbu sahifada</small><strong>{data.results.length}</strong></div></div>
        <div className="xu-users__stat"><span><ShieldCheck size={20} /></span><div><small>Ko'rish huquqi</small><strong>Admin</strong></div></div>
      </div>
      <section className="xu-users__panel">
        <div className="xu-users__filters">
          <label className="xu-users__search"><Search size={19} /><input aria-label="Foydalanuvchi qidirish" placeholder="Ism, telefon yoki email bo'yicha qidirish..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} /></label>
          <select aria-label="Rol bo'yicha filter" value={role} onChange={(e) => { setRole(e.target.value); setPage(1); }}><option value="">Barcha rollar</option><option value="admin">Admin</option><option value="manager">Menejer</option><option value="coach">Murabbiy</option><option value="student">Student</option><option value="user">User</option><option value="client">Client</option></select>
          <select aria-label="Faollik bo'yicha filter" value={active} onChange={(e) => { setActive(e.target.value); setPage(1); }}><option value="">Barcha holatlar</option><option value="true">Faol</option><option value="false">Nofaol</option></select>
          <button type="button" className="xu-users__clear" onClick={clearFilters}>Tozalash</button>
        </div>
        {error && <div className="xu-users__error" role="alert"><AlertCircle size={18} /> {error}</div>}
        <div className="xu-users__table-wrap">
          <table className="xu-users__table">
            <thead><tr><th>FOYDALANUVCHI</th><th>TELEFON</th><th>ROL</th><th>HOLAT</th><th>RO'YXATDAN O'TGAN</th><th></th></tr></thead>
            <tbody>
              {loading ? <tr><td colSpan={6} className="xu-users__empty">Yuklanmoqda...</td></tr> : data.results.length === 0 ? <tr><td colSpan={6} className="xu-users__empty">Foydalanuvchi topilmadi.</td></tr> : data.results.map((user) => (
                <tr key={user.id}>
                  <td><div className="xu-users__person"><span className="xu-users__avatar">{initials(user.full_name)}</span><div><strong>{user.full_name || "Ism kiritilmagan"}</strong><small>{user.email || "Email kiritilmagan"}</small></div></div></td>
                  <td>{user.phone_number || "—"}</td><td><span className="xu-users__role">{roleText(user.role)}</span></td>
                  <td><span className={`xu-users__status ${user.is_active ? "is-active" : "is-inactive"}`}>{user.is_active ? <CheckCircle2 size={14} /> : <XCircle size={14} />}{user.is_active ? "Faol" : "Nofaol"}</span></td>
                  <td>{fmtDate(user.date_joined)}</td><td><button className="xu-users__detail-btn" type="button" onClick={() => showDetails(user.id)}>Batafsil</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="xu-users__pagination"><span>{data.count} ta natija · {page}/{totalPages} sahifa</span><div><button type="button" aria-label="Oldingi sahifa" disabled={page <= 1 || loading} onClick={() => setPage((p) => p - 1)}><ChevronLeft size={18} /></button><button type="button" aria-label="Keyingi sahifa" disabled={page >= totalPages || loading} onClick={() => setPage((p) => p + 1)}><ChevronRight size={18} /></button></div></div>
      </section>
      {(selected || detailLoading || detailError) && <div className="xu-users__overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) { setSelected(null); setDetailError(""); } }}><section className="xu-users__modal" role="dialog" aria-modal="true" aria-label="Foydalanuvchi ma'lumotlari"><div className="xu-users__modal-top"><h2>Foydalanuvchi ma'lumotlari</h2><button aria-label="Yopish" type="button" onClick={() => { setSelected(null); setDetailError(""); }}><X size={20} /></button></div>{detailLoading ? <p>Yuklanmoqda...</p> : detailError ? <p className="xu-users__error">{detailError}</p> : selected && <><div className="xu-users__modal-user"><span className="xu-users__avatar">{initials(selected.full_name)}</span><div><strong>{selected.full_name || "Ism kiritilmagan"}</strong><small>#{selected.id} · {roleText(selected.role)}</small></div></div><div className="xu-users__info"><div><Phone size={17} /><span>Telefon</span><strong>{selected.phone_number || "—"}</strong></div><div><Mail size={17} /><span>Email</span><strong>{selected.email || "—"}</strong></div><div><CheckCircle2 size={17} /><span>Telefon tasdiqlangan</span><strong>{selected.is_phone_verified ? "Ha" : "Yo'q"}</strong></div><div><ShieldCheck size={17} /><span>Hisob holati</span><strong>{selected.is_active ? "Faol" : "Nofaol"}</strong></div><div><CalendarDays size={17} /><span>Ro'yxatdan o'tgan</span><strong>{fmtDate(selected.date_joined)}</strong></div></div></>}</section></div>}
    </main>
  );
}