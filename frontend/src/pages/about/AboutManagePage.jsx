import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { authFetch } from '../../utils/auth';
import './AboutPage.css';

const API = '/api/v1/site/about/';
const EMPTY = { title: '', content: '', position: 0 };

function errorText(data) {
  if (typeof data?.detail === 'string') return data.detail;
  const first = data && typeof data === 'object' ? Object.values(data)[0] : null;
  return Array.isArray(first) ? first.join(' ') : (typeof first === 'string' ? first : 'Soʻrov bajarilmadi.');
}

export default function AboutManagePage() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(API);
      if (!res.ok) throw new Error('Maʼlumotlarni yuklashda xatolik.');
      const data = await res.json();
      setItems(Array.isArray(data) ? data : data.results || []);
      setError('');
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const url = editingId === null ? API : `${API}${editingId}/`;
      const res = await authFetch(url, {
        method: editingId === null ? 'POST' : 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(errorText(data));
      setEditingId(null);
      setForm(EMPTY);
      await load();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  function edit(item) {
    setEditingId(item.id);
    setForm({ title: item.title, content: item.content, position: item.position });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function remove(item) {
    if (!window.confirm(`“${item.title}” oʻchirilsinmi?`)) return;
    setBusy(true);
    try {
      const res = await authFetch(`${API}${item.id}/`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Oʻchirish amalga oshmadi.');
      await load();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return (
    <main className="about-page">
      <div className="about-wrap">
        <span className="about-eyebrow">ADMIN BOSHQARUVI</span>
        <h1>Biz haqimizda — tahrirlash</h1>
        <p className="about-lead">Boʻlimlar roʻyxatda «Tartib raqami» boʻyicha koʻrsatiladi.</p>
        <form className="about-form" onSubmit={submit}>
          <label>Sarlavha<input required maxLength={200} value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /></label>
          <label>Matn<textarea required rows={6} value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} /></label>
          <label>Tartib raqami<input type="number" min="0" required value={form.position} onChange={e => setForm({ ...form, position: Number(e.target.value) })} /></label>
          <div className="about-actions">
            <button disabled={busy} type="submit">{editingId === null ? 'Qoʻshish' : 'Saqlash'}</button>
            {editingId !== null && <button type="button" className="about-secondary" onClick={() => { setEditingId(null); setForm(EMPTY); }}>Bekor qilish</button>}
            <Link to="/about">Sahifani koʻrish</Link>
          </div>
        </form>
        {error && <p role="alert" className="about-error">{error}</p>}
        {loading ? <p>Yuklanmoqda...</p> : (
          <ol className="about-list">
            {items.map(item => <li className="about-item" key={item.id}>
              <h2>{item.title}</h2>
              <p className="about-content">{item.content}</p>
              <p className="about-muted">Tartib: {item.position}</p>
              <div className="about-actions">
                <button type="button" disabled={busy} onClick={() => edit(item)}>Tahrirlash</button>
                <button type="button" disabled={busy} className="about-danger" onClick={() => remove(item)}>Oʻchirish</button>
              </div>
            </li>)}
          </ol>
        )}
      </div>
    </main>
  );
}