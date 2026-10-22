import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  ArrowLeft, BadgeCheck, CheckCircle2, CircleAlert, LayoutDashboard,
  LoaderCircle, Mail, Pencil, Phone, Save, ShieldCheck, UserRound, X,
} from "lucide-react";
import { authFetch, getValidAccessToken, hasSession } from "../../utils/auth";
import "./ProfilePage.css";

const PROFILE_URL = "/api/v1/auth/me/";

function initials(name) {
  const parts = (name || "").trim().split(/\s+/).filter(Boolean);
  return parts.length ? parts.slice(0, 2).map((part) => part[0].toUpperCase()).join("") : "U";
}

function roleLabel(role) {
  const labels = { admin: "Administrator", manager: "Menejer", coach: "Murabbiy", user: "Foydalanuvchi", client: "Foydalanuvchi", student: "Foydalanuvchi" };
  return labels[role] || role || "Foydalanuvchi";
}

function extractError(data) {
  if (!data || typeof data !== "object") return "Ma'lumotlarni saqlab bo'lmadi.";
  if (typeof data.detail === "string") return data.detail;
  const field = Object.values(data).find((value) => Array.isArray(value) || typeof value === "string");
  return Array.isArray(field) ? field.join(" ") : field || "Ma'lumotlarni saqlab bo'lmadi.";
}

export default function ProfilePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [form, setForm] = useState({ full_name: "", email: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [success, setSuccess] = useState("");
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const redirectToLogin = useCallback(() => {
    navigate("/login", {
      replace: true,
      state: { from: location.pathname, message: "Sessiya tugagan. Qaytadan tizimga kiring." },
    });
  }, [navigate, location.pathname]);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    async function load() {
      setLoading(true);
      setError("");
      try {
        if (!hasSession()) { redirectToLogin(); return; }
        const token = await getValidAccessToken();
        if (!active || controller.signal.aborted) return;
        if (!token) {
          if (!hasSession()) redirectToLogin();
          else setError("Sessiyani yangilab bo'lmadi. Internetni tekshiring.");
          return;
        }
        const response = await authFetch(PROFILE_URL, { method: "GET", signal: controller.signal });
        if (!active || controller.signal.aborted) return;
        if (response.status === 401) { redirectToLogin(); return; }
        if (!response.ok) throw new Error(`Profilni yuklashda xatolik (HTTP ${response.status}).`);
        const data = await response.json();
        if (!active || controller.signal.aborted) return;
        setUser(data);
        setForm({ full_name: data.full_name || "", email: data.email || "" });
      } catch (err) {
        if (active && !controller.signal.aborted && err.name !== "AbortError") {
          setError(err.message || "Profil ma'lumotlarini yuklab bo'lmadi.");
        }
      } finally {
        if (active && !controller.signal.aborted) setLoading(false);
      }
    }
    load();
    return () => { active = false; controller.abort(); };
  }, [retryCount, redirectToLogin]);

  function startEditing() {
    setForm({ full_name: user.full_name || "", email: user.email || "" });
    setSaveError("");
    setSuccess("");
    setEditing(true);
  }

  function cancelEditing() {
    if (saving) return;
    setEditing(false);
    setSaveError("");
  }

  async function saveProfile(event) {
    event.preventDefault();
    if (saving) return;
    const fullName = form.full_name.trim();
    const email = form.email.trim();
    if (!fullName) { setSaveError("Ism-familiya kiritilishi shart."); return; }
    if (fullName.length > 150) { setSaveError("Ism-familiya juda uzun."); return; }
    setSaving(true);
    setSaveError("");
    setSuccess("");
    try {
      if (!hasSession()) { redirectToLogin(); return; }
      const token = await getValidAccessToken();
      if (!token) {
        if (!hasSession()) redirectToLogin();
        else setSaveError("Sessiyani yangilab bo'lmadi. Qayta urinib ko'ring.");
        return;
      }
      const response = await authFetch(PROFILE_URL, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: fullName, email }),
      });
      if (response.status === 401) { redirectToLogin(); return; }
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        setSaveError(response.status === 405
          ? "Backendda profilni tahrirlash (PATCH) hali yoqilmagan."
          : extractError(data));
        return;
      }
      // PATCH response may contain only writable fields; preserve read-only profile data.
      setUser((previous) => ({ ...previous, full_name: fullName, email, ...(data || {}) }));
      setEditing(false);
      setSuccess("Shaxsiy ma'lumotlar muvaffaqiyatli saqlandi.");
    } catch {
      setSaveError("Server bilan bog'lanib bo'lmadi. Qayta urinib ko'ring.");
    } finally {
      setSaving(false);
    }
  }

  const isAdmin = user?.role === "admin";

  return (
    <main className="xp-page">
      <div className="xp-container">
        <div className="xp-breadcrumb"><Link to="/"><ArrowLeft size={16} /> Bosh sahifa</Link><span>/</span><span>Shaxsiy kabinet</span></div>
        <div className="xp-heading"><div><span className="xp-eyebrow">XUMO SPORT MAJMUASI</span><h1>Shaxsiy kabinet</h1><p>Profilingiz va shaxsiy ma'lumotlaringizni boshqaring.</p></div></div>

        {loading ? (
          <div className="xp-state" role="status"><LoaderCircle className="xp-spin" size={30} /><p>Profil yuklanmoqda...</p></div>
        ) : error ? (
          <div className="xp-state xp-state-error" role="alert"><CircleAlert size={30} /><p>{error}</p><button type="button" className="xp-btn xp-btn-primary" onClick={() => setRetryCount((n) => n + 1)}>Qayta urinish</button></div>
        ) : user ? (
          <div className="xp-layout">
            <aside className="xp-sidebar">
              <div className="xp-person"><div className="xp-avatar" aria-hidden="true">{initials(user.full_name)}</div><h2>{user.full_name || "Foydalanuvchi"}</h2><span className="xp-role"><ShieldCheck size={14} /> {roleLabel(user.role)}</span></div>
              <div className="xp-sidebar-divider" />
              <nav className="xp-nav" aria-label="Profil navigatsiyasi"><a className="xp-nav-active" href="#profile-details"><UserRound size={19} /> Shaxsiy ma'lumotlar</a>{isAdmin && <Link to="/dashboard"><LayoutDashboard size={19} /> Admin dashboard</Link>}</nav>
              <div className="xp-sidebar-note"><ShieldCheck size={20} /><span>Profilingizga faqat sizning hisobingiz orqali kirish mumkin.</span></div>
            </aside>

            <section className="xp-content" id="profile-details" aria-label="Shaxsiy ma'lumotlar">
              <div className="xp-card">
                <div className="xp-card-top"><div><span className="xp-section-tag">PROFIL</span><h2>Shaxsiy ma'lumotlar</h2><p>Hisobingiz bilan bog'liq asosiy ma'lumotlar.</p></div>{!editing && <button type="button" className="xp-btn xp-btn-outline" onClick={startEditing}><Pencil size={17} /> Tahrirlash</button>}</div>
                {success && <div className="xp-notice xp-notice-success" role="status"><CheckCircle2 size={18} /> {success}</div>}
                {editing ? (
                  <form className="xp-form" onSubmit={saveProfile}>
                    <div className="xp-fields"><label className="xp-field"><span>Ism-familiya</span><input type="text" autoComplete="name" maxLength={150} required value={form.full_name} onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} /></label><label className="xp-field"><span>Email manzil</span><input type="email" autoComplete="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} placeholder="email@example.com" /></label></div>
                    {saveError && <div className="xp-notice xp-notice-error" role="alert"><CircleAlert size={18} /> {saveError}</div>}
                    <div className="xp-actions"><button type="button" className="xp-btn xp-btn-outline" onClick={cancelEditing} disabled={saving}><X size={17} /> Bekor qilish</button><button type="submit" className="xp-btn xp-btn-primary" disabled={saving}>{saving ? <LoaderCircle size={17} className="xp-spin" /> : <Save size={17} />}{saving ? "Saqlanmoqda..." : "Saqlash"}</button></div>
                  </form>
                ) : (
                  <div className="xp-fields xp-display-fields"><div className="xp-info"><div className="xp-info-icon"><UserRound size={20} /></div><div><span>Ism-familiya</span><strong>{user.full_name || "Kiritilmagan"}</strong></div></div><div className="xp-info"><div className="xp-info-icon"><Mail size={20} /></div><div><span>Email</span><strong>{user.email || "Kiritilmagan"}</strong></div></div><div className="xp-info"><div className="xp-info-icon"><Phone size={20} /></div><div><span>Telefon raqami</span><strong>{user.phone_number || "Kiritilmagan"}</strong></div></div><div className="xp-info"><div className="xp-info-icon"><ShieldCheck size={20} /></div><div><span>Hisob turi</span><strong>{roleLabel(user.role)}</strong></div></div></div>
                )}
              </div>

            </section>
          </div>
        ) : null}
      </div>
    </main>
  );
}