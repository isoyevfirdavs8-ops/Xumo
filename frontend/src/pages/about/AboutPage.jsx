import { useEffect, useState } from 'react';
import './AboutPage.css';

const API = '/api/v1/site/about/';

export default function AboutPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(API, { signal: controller.signal });
        if (!response.ok) throw new Error('Maʼlumotlarni yuklab boʼlmadi.');
        const data = await response.json();
        setItems(Array.isArray(data) ? data : data.results || []);
      } catch (err) {
        if (err.name !== 'AbortError') setError(err.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    load();
    return () => controller.abort();
  }, []);

  return (
    <main className="about-page">
      <div className="about-wrap">
        <span className="about-eyebrow">XUMO SPORT MAJMUASI</span>
        <h1>Biz haqimizda</h1>
        <p className="about-lead">Sport majmuamiz haqida batafsil maʼlumot.</p>
        {loading && <p role="status">Yuklanmoqda...</p>}
        {error && <p role="alert" className="about-error">{error}</p>}
        {!loading && !error && items.length === 0 && <p>Hozircha maʼlumot kiritilmagan.</p>}
        <ol className="about-list">
          {items.map((item) => (
            <li className="about-item" key={item.id}>
              <h2>{item.title}</h2>
              <p className="about-content">{item.content}</p>
            </li>
          ))}
        </ol>
      </div>
    </main>
  );
}