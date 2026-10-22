import { saveTokens } from "../../utils/auth";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Auth.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [phone, setPhone] = useState("+998");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await fetch("/api/v1/auth/login/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          phone_number: phone.trim(),
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Telefon raqami yoki parol noto‘g‘ri."
        );
      }

      if (!data.access || !data.refresh) {
        throw new Error("Server tokenlarni qaytarmadi.");
      }

      saveTokens(data);

      window.dispatchEvent(new Event("auth-changed"));

      navigate("/profile", { replace: true });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Tizimga kirishda xatolik yuz berdi."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Tizimga kirish</h1>
        <p>FC BUKHARA shaxsiy kabinetingiz</p>

        {location.state?.message && (
          <div className="auth-success" role="status">
            {location.state.message}
          </div>
        )}

        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}

        <label htmlFor="login-phone">Telefon raqami</label>
        <input
          id="login-phone"
          type="tel"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          required
          pattern="\+998[0-9]{9}"
          placeholder="+998901234567"
          autoComplete="username"
        />

        <label htmlFor="login-password">Parol</label>
        <input
          id="login-password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
          autoComplete="current-password"
        />

        <button type="submit" disabled={loading}>
          {loading ? "Tekshirilmoqda..." : "Kirish"}
        </button>

        <p className="auth-footer">
          Akkauntingiz yo‘qmi?{" "}
          <Link to="/register">Ro‘yxatdan o‘tish</Link>
        </p>
      </form>
    </main>
  );
}
