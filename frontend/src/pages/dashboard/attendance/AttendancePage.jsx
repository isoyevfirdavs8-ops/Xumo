import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  CalendarDays,
  Check,
  X,
  RefreshCw,
  Users,
} from "lucide-react";

import {
  getAttendanceStudents,
  markAttendance,
} from "../../../services/attendanceApi";

import "./attendance.css";

function getLocalDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

export default function AttendancePage() {
  const { sport } = useParams();

  const [selectedDate, setSelectedDate] = useState(getLocalDate());
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const sportConfig = {
  boxing: {
    title: "Boks davomati",
    locationLabel: "Akademiya",
  },
  tennis: {
    title: "Tennis davomati",
    locationLabel: "Kort",
  },
  football: {
    title: "Football Academy davomati",
    locationLabel: "Akademiya",
  },
};

const validSport = Object.hasOwn(sportConfig, sport);
const title = sportConfig[sport]?.title ?? "Davomat";

  const month = `${selectedDate.slice(0, 7)}-01`;

  async function loadStudents() {
    if (!validSport) return;

    setLoading(true);
    setError("");

    try {
      const data = await getAttendanceStudents(sport, month);

      setStudents(
        Array.isArray(data) ? data : data.results || []
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStudents();
  }, [sport, month]);

  async function handleMark(student, status) {
    setSavingId(student.id);
    setError("");
    setSuccess("");

    try {
      await markAttendance({
        sport,
        subscription_id: student.id,
        date: selectedDate,
        status,
      });

      setSuccess(
        `${student.student_name}: ${
          status === "present" ? "Kelgan" : "Kelmagan"
        } deb belgilandi.`
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingId(null);
    }
  }

  if (!validSport) {
    return <div className="attendance-page">Sport turi topilmadi.</div>;
  }

  return (
    <main className="attendance-page">
      <div className="attendance-header">
        <div>
          <p className="attendance-eyebrow">FC BUKHARA · DASHBOARD</p>
          <h1>{title}</h1>
          <p>Oylik bron qilgan o'quvchilar davomatini boshqarish</p>
        </div>

        <Link to="/dashboard/users" className="attendance-back">
          Foydalanuvchilarga qaytish
        </Link>
      </div>

      <div className="attendance-toolbar">
        <label>
          <CalendarDays size={18} />
          <span>Sana</span>
          <input
            type="date"
            value={selectedDate}
            max={getLocalDate()}
            onChange={(event) => setSelectedDate(event.target.value)}
          />
        </label>

        <button
          type="button"
          onClick={loadStudents}
          disabled={loading}
          className="attendance-refresh"
        >
          <RefreshCw size={17} />
          Yangilash
        </button>
      </div>

      {error && <div className="attendance-alert error">{error}</div>}
      {success && <div className="attendance-alert success">{success}</div>}

      <div className="attendance-summary">
        <Users size={20} />
        <span>
          O'quvchilar soni: <strong>{students.length}</strong>
        </span>
      </div>

      <div className="attendance-table-wrapper">
        {loading ? (
          <p className="attendance-empty">Ma'lumotlar yuklanmoqda...</p>
        ) : students.length === 0 ? (
          <p className="attendance-empty">
            Tanlangan oy uchun to'langan bronlar topilmadi.
          </p>
        ) : (
          <table className="attendance-table">
            <thead>
              <tr>
                <th>O'quvchi</th>
                <th>Telefon</th>
                <th>{sportConfig[sport].locationLabel}</th>
                <th>Davomat</th>
                <th>Batafsil</th>
              </tr>
            </thead>

            <tbody>
              {students.map((student) => (
                <tr key={student.id}>
                  <td className="student-name">{student.student_name}</td>
                  <td>{student.phone_number}</td>
                  <td>
                    {sport === "tennis"
                      ? student.court_name
                      : student.academy_name}
                  </td>
                  <td>
                    <div className="attendance-actions">
                      <button
                        type="button"
                        className="attendance-present"
                        disabled={savingId === student.id}
                        onClick={() => handleMark(student, "present")}
                      >
                        <Check size={16} />
                        Kelgan
                      </button>

                      <button
                        type="button"
                        className="attendance-absent"
                        disabled={savingId === student.id}
                        onClick={() => handleMark(student, "absent")}
                      >
                        <X size={16} />
                        Kelmagan
                      </button>
                    </div>
                  </td>

                  <td>
                    <Link
                      to={`/dashboard/attendance/${sport}/${student.id}`}
                      className="attendance-detail-link"
                    >
                      Ko'rish →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}