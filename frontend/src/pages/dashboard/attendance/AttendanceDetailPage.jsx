import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  getAttendanceStudent,
  getAttendanceHistory,
} from "../../../services/attendanceApi";

import "./attendance.css";

export default function AttendanceDetailPage() {
  const { sport, id } = useParams();

  const [student, setStudent] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const [studentData, historyData] = await Promise.all([
          getAttendanceStudent(sport, id),
          getAttendanceHistory(sport, id),
        ]);

        if (cancelled) return;

        setStudent(studentData);
        setHistory(
          Array.isArray(historyData)
            ? historyData
            : historyData.results || []
        );
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [sport, id]);

  const presentCount = history.filter(
    (item) => item.status === "present"
  ).length;

  const absentCount = history.filter(
    (item) => item.status === "absent"
  ).length;

  const total = presentCount + absentCount;

  const percentage = total
    ? Math.round((presentCount / total) * 100)
    : 0;

  if (loading) {
    return <main className="attendance-page">Yuklanmoqda...</main>;
  }

  if (error) {
    return (
      <main className="attendance-page">
        <div className="attendance-alert error">{error}</div>
      </main>
    );
  }

  return (
    <main className="attendance-page">
      <Link
        to={`/dashboard/attendance/${sport}`}
        className="attendance-back"
      >
        ← Davomat ro'yxatiga qaytish
      </Link>

      <div className="attendance-header">
        <div>
          <p className="attendance-eyebrow">O'QUVCHI PROFILI</p>
          <h1>{student?.student_name}</h1>
          <p>{student?.phone_number}</p>
          <p>
            {student?.academy_name || student?.court_name}
          </p>
        </div>
      </div>

      <div className="attendance-stats">
        <div className="attendance-stat-card">
          <span>Kelgan</span>
          <strong>{presentCount}</strong>
        </div>

        <div className="attendance-stat-card">
          <span>Kelmagan</span>
          <strong>{absentCount}</strong>
        </div>

        <div className="attendance-stat-card">
          <span>Davomat foizi</span>
          <strong>{percentage}%</strong>
        </div>
      </div>

      <section className="attendance-history">
        <h2>Davomat tarixi</h2>

        {history.length === 0 ? (
          <p>Hozircha davomat belgilanmagan.</p>
        ) : (
          <div className="attendance-history-list">
            {history.map((item) => (
              <div className="attendance-history-item" key={item.id}>
                <span>{item.date}</span>
                <strong
                  className={
                    item.status === "present"
                      ? "status-present"
                      : "status-absent"
                  }
                >
                  {item.status === "present"
                    ? "✓ Kelgan"
                    : "✕ Kelmagan"}
                </strong>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}