
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  Send,
  Phone,
  Mail,
  Clock3,
  ArrowUp,
  MapPin,
} from "lucide-react";

import {
  FaFacebookF,
  FaInstagram,
} from "react-icons/fa";

import "./Footer.css";
const BRAND_NAME = "XUMO SPORT MAJMUASI";
const API_URL = "/api/v1/site/footer/";
const CACHE_KEY = "fc_bukhara_footer";
const CACHE_TTL = 5 * 60 * 1000;

const defaultFooter = {
  brand_name: BRAND_NAME,
  description:
    "Sport, sog‘lom turmush va mazmunli hordiq uchun zamonaviy imkoniyatlar.",
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
  copyright_text: "Barcha huquqlar himoyalangan.",
};

const navigationLinks = [
  { label: "Bosh sahifa", path: "/" },
  { label: "Xizmatlar", path: "/services" },
  { label: "Musobaqalar", path: "/competitions" },
  { label: "Restoran", path: "/restaurant" },
  { label: "Savatcha", path: "/restaurant/cart" },
  { label: "Profil", path: "/profile" },
];

let footerPromise = null;
let retryAfter = 0;

function getCachedFooter() {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY);

    if (!raw) return null;

    const cached = JSON.parse(raw);

    if (
      !cached ||
      !cached.data ||
      typeof cached.data !== "object" ||
      Array.isArray(cached.data) ||
      !Number.isFinite(cached.timestamp) ||
      Date.now() - cached.timestamp > CACHE_TTL
    ) {
      return null;
    }

    return cached.data;
  } catch {
    return null;
  }
}

function saveCachedFooter(data) {
  try {
    sessionStorage.setItem(
      CACHE_KEY,
      JSON.stringify({
        timestamp: Date.now(),
        data,
      })
    );
  } catch {
    // Storage ishlamasa ham Footer ishlaydi.
  }
}

async function loadFooter() {
  const cached = getCachedFooter();

  if (cached) return cached;

  if (footerPromise) return footerPromise;

  if (Date.now() < retryAfter) {
    throw new Error("Footer API vaqtincha cheklangan.");
  }

  footerPromise = (async () => {
    const response = await fetch(API_URL);

    if (response.status === 429) {
      const retrySeconds = Number(
        response.headers.get("Retry-After") || 60
      );

      const seconds =
        Number.isFinite(retrySeconds) && retrySeconds > 0
          ? retrySeconds
          : 60;

      retryAfter = Date.now() + seconds * 1000;

      throw new Error("Footer API: 429 Too Many Requests");
    }

    if (!response.ok) {
      throw new Error(
        `Footer API error: ${response.status}`
      );
    }

    const data = await response.json();

    if (
      !data ||
      typeof data !== "object" ||
      Array.isArray(data)
    ) {
      throw new Error("Footer API noto‘g‘ri javob qaytardi.");
    }

    saveCachedFooter(data);

    return data;
  })();

  try {
    return await footerPromise;
  } finally {
    footerPromise = null;
  }
}

function getSafeUrl(value) {
  if (typeof value !== "string" || !value.trim()) {
    return null;
  }

  try {
    const url = new URL(value.trim());

    if (
      url.protocol !== "https:" &&
      url.protocol !== "http:"
    ) {
      return null;
    }

    return url.href;
  } catch {
    return null;
  }
}

function SocialLink({ href, label, children }) {
  const safeUrl = getSafeUrl(href);

  if (!safeUrl) return null;

  return (
    <a
      href={safeUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="fc-footer-social"
      aria-label={label}
      title={label}
    >
      {children}
    </a>
  );
}

export default function Footer() {
  const [footer, setFooter] = useState(() => ({
    ...defaultFooter,
    ...(getCachedFooter() || {}),
  }));

  useEffect(() => {
    let active = true;

    loadFooter()
      .then((data) => {
        if (!active) return;

        setFooter({
          ...defaultFooter,
          ...data,
        });
      })
      .catch((error) => {
        if (active) {
          console.warn("Footer:", error.message);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const year = new Date().getFullYear();

  const phones = [
    footer.phone,
    footer.phone_2,
    footer.phone_3,
    footer.phone_4,
  ]
    .filter((phone) => typeof phone === "string")
    .map((phone) => phone.trim())
    .filter(Boolean);

  const email = String(footer.email || "");

  function scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  return (
    <footer id="contact" className="fc-footer">
      <div className="fc-footer-container">
        <div className="fc-footer-main">

          {/* BRAND */}
          <div className="fc-footer-brand">
            <Link to="/" className="fc-footer-logo">
              {BRAND_NAME}
            </Link>

            {footer.description && (
              <p className="fc-footer-description">
                {footer.description}
              </p>
            )}

            <div className="fc-footer-socials">
              <SocialLink
                href={footer.telegram_url}
                label="Telegram"
              >
                <Send size={19} />
              </SocialLink>

              <SocialLink
                href={footer.facebook_url}
                label="Facebook"
              >
                <FaFacebookF size={19} />
              </SocialLink>

              <SocialLink
                href={footer.instagram_url}
                label="Instagram"
              >
                <FaInstagram size={19} />
              </SocialLink>
            </div>
          </div>

          {/* NAVIGATION */}
          <div className="fc-footer-column">
            <h3 className="fc-footer-title">
              Navigatsiya
            </h3>

            <ul className="fc-footer-links">
              {navigationLinks.map((item) => (
                <li key={item.path}>
                  <Link to={item.path}>
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* CONTACT */}
          <div className="fc-footer-column">
            <h3 className="fc-footer-title">
              Aloqa
            </h3>

            <div className="fc-footer-contact">

              {/* 4 TA TELEFON — 2x2 GRID */}
              {phones.length > 0 && (
                <div className="fc-footer-phones-grid">
                  {phones.map((phone, index) => (
                    <div
                      key={`${phone}-${index}`}
                      className="fc-footer-contact-item fc-footer-phone-item"
                    >
                      <span className="fc-footer-contact-icon">
                        <Phone size={17} />
                      </span>

                      <a
                        href={`tel:${phone.replace(/[^\d+]/g, "")}`}
                      >
                        {phone}
                      </a>
                    </div>
                  ))}
                </div>
              )}

              {/* EMAIL */}
              {email && (
                <div className="fc-footer-contact-item">
                  <span className="fc-footer-contact-icon">
                    <Mail size={19} />
                  </span>

                  <a href={`mailto:${email}`}>
                    {email}
                  </a>
                </div>
              )}

              {/* WORKING HOURS */}
              {footer.working_hours && (
                <div className="fc-footer-contact-item">
                  <span className="fc-footer-contact-icon">
                    <Clock3 size={19} />
                  </span>

                  <span>{footer.working_hours}</span>
                </div>
              )}

              {/* ADDRESS */}
              {footer.address && (
                <div className="fc-footer-contact-item">
                  <span className="fc-footer-contact-icon">
                    <MapPin size={19} />
                  </span>

                  <span>{footer.address}</span>
                </div>
              )}

            </div>
          </div>

        </div>

        {/* BOTTOM */}

        <div className="fc-footer-bottom">
          <p>
            © {year} {BRAND_NAME} (Barcha huquqlar himoyalangan)
          </p>

          <button
            type="button"
            className="fc-footer-top"
            onClick={scrollToTop}
            aria-label="Sahifa yuqorisiga qaytish"
            title="Yuqoriga qaytish"
          >
            <ArrowUp size={22} />
          </button>
        </div>
      </div>
    </footer>
  );
}

