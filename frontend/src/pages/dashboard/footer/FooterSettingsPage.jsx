
import { useEffect, useState } from "react";

import {
  Save,
  Phone,
  Mail,
  MapPin,
  Clock3,
  Send,
  PanelBottom,
} from "lucide-react";

import {
  FaFacebookF,
  FaInstagram,
} from "react-icons/fa";

import "./FooterSettingsPage.css";

const API_URL = "/api/v1/dashboard/footer/";
const FOOTER_CACHE_KEY = "fc_bukhara_footer";

const initialForm = {
  brand_name: "FC BUKHARA",
  description: "",
  phone: "",
  phone_2: "",
  phone_3: "",
  phone_4: "",
  email: "",
  address: "",
  working_hours: "",
  telegram_url: "",
  facebook_url: "",
  instagram_url: "",
  copyright_text: "",
};

const fields = [
  {
    name: "phone",
    label: "Telefon raqami 1",
    placeholder: "+998 90 123 45 67",
    icon: Phone,
    maxLength: 30,
  },
  {
    name: "phone_2",
    label: "Telefon raqami 2",
    placeholder: "+998 91 123 45 67",
    icon: Phone,
    maxLength: 30,
  },
  {
    name: "phone_3",
    label: "Telefon raqami 3",
    placeholder: "+998 93 123 45 67",
    icon: Phone,
    maxLength: 30,
  },
  {
    name: "phone_4",
    label: "Telefon raqami 4",
    placeholder: "+998 94 123 45 67",
    icon: Phone,
    maxLength: 30,
  },
  {
    name: "email",
    label: "Email",
    placeholder: "info@example.com",
    icon: Mail,
    type: "email",
  },
  {
    name: "address",
    label: "Manzil",
    placeholder: "Buxoro, O‘zbekiston",
    icon: MapPin,
    maxLength: 255,
  },
  {
    name: "working_hours",
    label: "Ish vaqti",
    placeholder: "Dushanba – Yakshanba, 09:00 – 23:00",
    icon: Clock3,
    maxLength: 150,
  },
  {
    name: "telegram_url",
    label: "Telegram URL",
    placeholder: "https://t.me/username",
    icon: Send,
    type: "url",
    maxLength: 500,
  },
  {
    name: "instagram_url",
    label: "Instagram URL",
    placeholder: "https://instagram.com/username",
    icon: FaInstagram,
    type: "url",
    maxLength: 500,
  },
  {
    name: "facebook_url",
    label: "Facebook URL",
    placeholder: "https://facebook.com/username",
    icon: FaFacebookF,
    type: "url",
    maxLength: 500,
  },
];

function getAccessToken() {
  try {
    return (
      sessionStorage.getItem("access_token") ||
      localStorage.getItem("access_token") ||
      ""
    );
  } catch {
    return "";
  }
}

function getHeaders() {
  const token = getAccessToken();

  return {
    "Content-Type": "application/json",
    ...(token
      ? { Authorization: `Bearer ${token}` }
      : {}),
  };
}

async function parseResponse(response) {
  const contentType =
    response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();

  return {
    detail: text || "Serverdan javob olinmadi.",
  };
}

function getErrorMessage(data, fallback) {
  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (data && typeof data === "object") {
    const first = Object.entries(data)[0];

    if (first) {
      const [field, messages] = first;

      const message = Array.isArray(messages)
        ? messages.join(" ")
        : typeof messages === "string"
          ? messages
          : JSON.stringify(messages);

      return `${field}: ${message}`;
    }
  }

  return fallback;
}

function getHttpError(response, data, fallback) {
  if (response.status === 401) {
    return "Sessiya tugagan yoki token noto‘g‘ri. Qayta tizimga kiring.";
  }

  if (response.status === 403) {
    return "Sizda Footer sozlamalarini boshqarish huquqi yo‘q.";
  }

  if (response.status === 404) {
    return "Footer API topilmadi. Backend URL konfiguratsiyasini tekshiring.";
  }

  if (response.status === 429) {
    return "So‘rovlar soni cheklangan. Birozdan keyin qayta urinib ko‘ring.";
  }

  return getErrorMessage(data, fallback);
}

function normalizeForm(data) {
  const result = { ...initialForm };

  for (const key of Object.keys(initialForm)) {
    const value = data?.[key];

    result[key] =
      typeof value === "string"
        ? value
        : initialForm[key];
  }

  return result;
}

export default function FooterSettingsPage() {
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadFooter() {
      setLoading(true);
      setError("");

      try {
        const response = await fetch(API_URL, {
          method: "GET",
          headers: getHeaders(),
          signal: controller.signal,
        });

        const data = await parseResponse(response);

        if (!response.ok) {
          throw new Error(
            getHttpError(
              response,
              data,
              "Footer ma’lumotlarini yuklashda xatolik yuz berdi."
            )
          );
        }

        if (!controller.signal.aborted) {
          setForm(normalizeForm(data));
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(
            err.message ||
              "Server bilan bog‘lanishda xatolik yuz berdi."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadFooter();

    return () => {
      controller.abort();
    };
  }, []);

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));

    setError("");
    setSuccess("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (saving || loading) return;

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(API_URL, {
        method: "PATCH",
        headers: getHeaders(),
        body: JSON.stringify(form),
      });

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(
          getHttpError(
            response,
            data,
            "Footer ma’lumotlarini saqlashda xatolik yuz berdi."
          )
        );
      }

      setForm(normalizeForm(data));

      // Public Footer eski ma’lumotlarni ko‘rsatmasligi uchun
      // cache tozalanadi.
      try {
        sessionStorage.removeItem(FOOTER_CACHE_KEY);
      } catch {
        // Storage ishlamasa ham saqlash muvaffaqiyatli.
      }

      setSuccess(
        "Footer ma’lumotlari muvaffaqiyatli saqlandi."
      );
    } catch (err) {
      setError(
        err.message ||
          "Saqlashda kutilmagan xatolik yuz berdi."
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="footer-admin-page">
        <p>Footer sozlamalari yuklanmoqda...</p>
      </main>
    );
  }

  return (
    <main className="footer-admin-page">
      <div className="footer-admin-header">
        <div>
          <span className="footer-admin-eyebrow">
            SAYT SOZLAMALARI
          </span>

          <h1>Footer boshqaruvi</h1>

          <p>
            Saytning pastki qismida ko‘rinadigan
            ma’lumotlarni boshqaring.
          </p>
        </div>

        <div className="footer-admin-header-icon">
          <PanelBottom size={28} />
        </div>
      </div>

      <form
        className="footer-admin-form"
        onSubmit={handleSubmit}
      >
        {/* ASOSIY MA'LUMOTLAR */}
        <section className="footer-admin-card">
          <h2>Asosiy ma’lumotlar</h2>

          <div className="footer-admin-grid">
            <label className="footer-admin-field">
              <span>Brend nomi</span>

              <input
                type="text"
                name="brand_name"
                value={form.brand_name}
                onChange={handleChange}
                maxLength={100}
                required
              />
            </label>

            <label className="footer-admin-field">
              <span>Copyright matni</span>

              <input
                type="text"
                name="copyright_text"
                value={form.copyright_text}
                onChange={handleChange}
                maxLength={255}
                placeholder="Barcha huquqlar himoyalangan."
              />
            </label>

            <label
              className="footer-admin-field footer-admin-full"
            >
              <span>Qisqacha tavsif</span>

              <textarea
                name="description"
                value={form.description}
                onChange={handleChange}
                rows={4}
                placeholder="FC BUKHARA haqida qisqacha..."
              />
            </label>
          </div>
        </section>

        {/* KONTAKT VA IJTIMOIY TARMOQLAR */}
        <section className="footer-admin-card">
          <h2>Kontakt va ijtimoiy tarmoqlar</h2>

          <div className="footer-admin-grid">
            {fields.map((field) => {
              const Icon = field.icon;

              return (
                <label
                  key={field.name}
                  className="footer-admin-field"
                >
                  <span className="footer-admin-label">
                    <Icon size={16} />
                    {field.label}
                  </span>

                  <input
                    type={field.type || "text"}
                    name={field.name}
                    value={form[field.name]}
                    onChange={handleChange}
                    placeholder={field.placeholder}
                    maxLength={field.maxLength}
                    autoComplete="off"
                  />
                </label>
              );
            })}
          </div>
        </section>

        {/* XATOLIK */}
        {error && (
          <p
            className="footer-admin-error"
            role="alert"
          >
            {error}
          </p>
        )}

        {/* MUVAFFAQIYAT */}
        {success && (
          <p
            className="footer-admin-success"
            role="status"
          >
            {success}
          </p>
        )}

        {/* SAVE BUTTON */}
        <div className="footer-admin-actions">
          <button
            type="submit"
            disabled={saving}
            className="footer-admin-save"
          >
            <Save size={18} />

            {saving
              ? "Saqlanmoqda..."
              : "O‘zgarishlarni saqlash"}
          </button>
        </div>
      </form>
    </main>
  );
}
