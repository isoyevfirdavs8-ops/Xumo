import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Auth.css";

export default function RegisterPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    phone_number: "+998",
    password: "",
    confirm_password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    setForm({
      ...form,
      [event.target.name]: event.target.value,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (form.password !== form.confirm_password) {
      setError("Parollar bir xil emas.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/api/v1/auth/register/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          full_name: form.full_name,
          phone_number: form.phone_number,
          password: form.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const message =
          Object.values(data).flat().join(" ") ||
          "Ro‘yxatdan o‘tishda xatolik.";

        throw new Error(message);
      }

      navigate("/login", {
        state: {
          message: "Ro‘yxatdan muvaffaqiyatli o‘tdingiz. Endi tizimga kiring.",
        },
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Ro‘yxatdan o‘tish</h1>
        <p>FC BUKHARA oilasiga qo‘shiling</p>

        {error && <div className="auth-error" role="alert">{error}</div>}

        <label>Ism va familiya</label>
        <input
          name="full_name"
          value={form.full_name}
          onChange={handleChange}
          required
          maxLength={200}
          placeholder="Ism Familiya"
        />

        <label>Telefon raqami</label>
        <input
          name="phone_number"
          type="tel"
          value={form.phone_number}
          onChange={handleChange}
          required
          pattern="\+998[0-9]{9}"
          placeholder="+998901234567"
        />

        <label>Parol</label>
        <input
          name="password"
          type="password"
          value={form.password}
          onChange={handleChange}
          required
          minLength={8}
          autoComplete="new-password"
        />

        <label>Parolni tasdiqlang</label>
        <input
          name="confirm_password"
          type="password"
          value={form.confirm_password}
          onChange={handleChange}
          required
          minLength={8}
          autoComplete="new-password"
        />

        <button type="submit" disabled={loading}>
          {loading ? "Yuborilmoqda..." : "Ro‘yxatdan o‘tish"}
        </button>

        <p className="auth-footer">
          Akkauntingiz bormi? <Link to="/login">Kirish</Link>
        </p>
      </form>
    </div>
  );
}