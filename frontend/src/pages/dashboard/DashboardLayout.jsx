import { useCallback, useEffect, useState } from "react";
import {
  Navigate,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";

import DashboardSidebar from "./DashboardSidebar";
import {
  authFetch,
  getValidAccessToken,
  hasSession,
} from "../../utils/auth";

import "./Dashboard.css";

export default function DashboardLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [retryCount, setRetryCount] = useState(0);

  const retry = useCallback(() => {
    setStatus("loading");
    setError("");
    setRetryCount((count) => count + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    async function checkAdmin() {
      setStatus("loading");
      setError("");

      try {
        if (!hasSession()) {
          if (active) setStatus("unauthenticated");
          return;
        }

        const token = await getValidAccessToken();

        if (!active || controller.signal.aborted) return;

        if (!token) {
          if (!hasSession()) {
            setStatus("unauthenticated");
          } else {
            setError(
              "Sessiyani tekshirib bo‘lmadi. Internet aloqasini tekshirib, qayta urinib ko‘ring."
            );
            setStatus("error");
          }
          return;
        }

        const response = await authFetch(
          "/api/v1/auth/me/",
          {
            method: "GET",
            signal: controller.signal,
          }
        );

        if (!active || controller.signal.aborted) return;

        if (response.status === 401) {
          setStatus("unauthenticated");
          return;
        }

        if (response.status === 403) {
          setStatus("forbidden");
          return;
        }

        if (!response.ok) {
          throw new Error(
            `Foydalanuvchini tekshirishda xatolik: HTTP ${response.status}`
          );
        }

        const user = await response.json();

        if (!active || controller.signal.aborted) return;

        if (user.role !== "admin") {
          setStatus("forbidden");
          return;
        }

        setStatus("authorized");
      } catch (err) {
        if (
          !active ||
          controller.signal.aborted ||
          err.name === "AbortError"
        ) {
          return;
        }

        setError(
          err.message ||
            "Dashboard'ga ulanishda xatolik yuz berdi."
        );
        setStatus("error");
      }
    }

    checkAdmin();

    return () => {
      active = false;
      controller.abort();
    };
  }, [retryCount]);

  if (status === "loading") {
    return (
      <main className="dashboard-access-screen">
        <p>Admin huquqlari tekshirilmoqda...</p>
      </main>
    );
  }

  if (status === "unauthenticated") {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,
          message:
            "Davom etish uchun tizimga kiring.",
        }}
      />
    );
  }

  if (status === "forbidden") {
    return <Navigate to="/" replace />;
  }

  if (status === "error") {
    return (
      <main className="dashboard-access-screen">
        <h2>Dashboard'ga kirib bo‘lmadi</h2>

        <p role="alert">{error}</p>

        <div
          style={{
            display: "flex",
            gap: 12,
            justifyContent: "center",
            flexWrap: "wrap",
          }}
        >
          <button type="button" onClick={retry}>
            Qayta urinish
          </button>

          <button
            type="button"
            onClick={() => navigate("/")}
          >
            Bosh sahifaga qaytish
          </button>
        </div>
      </main>
    );
  }

  return (
    <div className="dashboard-layout">
      <DashboardSidebar />

      <div className="dashboard-main">
        <header className="dashboard-topbar">
          <div>
            <span className="dashboard-eyebrow">
              FC BUKHARA
            </span>

            <h2>Boshqaruv paneli</h2>
          </div>

          <span className="dashboard-admin-badge">
            Administrator
          </span>
        </header>

        <div className="dashboard-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}