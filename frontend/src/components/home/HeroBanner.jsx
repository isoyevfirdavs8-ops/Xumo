
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, ChevronLeft, ChevronRight } from "lucide-react";
import "./HeroBanner.css";

export default function HeroBanner() {
  const [banners, setBanners] = useState([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadBanners() {
      try {
        const response = await fetch("/api/v1/banners/", {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Banner API: HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!controller.signal.aborted) {
          setBanners(
            Array.isArray(data) ? data : data.results || []
          );
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Banner yuklanmadi.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadBanners();

    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (banners.length <= 1) return;

    const timer = window.setInterval(() => {
      setActiveIndex((index) => (index + 1) % banners.length);
    }, 6500);

    return () => window.clearInterval(timer);
  }, [banners.length]);

  const goTo = (index) => {
    setActiveIndex(
      (index + banners.length) % banners.length
    );
  };

  if (loading) {
    return (
      <section className="hero-banner hero-banner-loading">
        <p>XUMO yuklanmoqda...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="hero-banner hero-banner-empty">
        <div className="hero-banner-inner">
          <h1>Xumo sport majmuasi</h1>
          <p>Sport va dam olish markaziga xush kelibsiz.</p>
        </div>
      </section>
    );
  }

  if (banners.length === 0) {
    return (
      <section className="hero-banner hero-banner-empty">
        <div className="hero-banner-inner">
          <span className="hero-eyebrow">SPORT & LIFESTYLE</span>
          <h1>Xumo</h1>
          <p>Sport, energiya va yangi imkoniyatlar maskani.</p>
        </div>
      </section>
    );
  }

  const banner = banners[activeIndex];

  const buttonUrl =
    banner.button_url?.startsWith("/") &&
    !banner.button_url.startsWith("//")
      ? banner.button_url
      : "/";

  return (
    <section
      className="hero-banner"
      aria-label="XUMO bannerlari"
    >
      <div className="hero-banner-background" aria-hidden="true">
        <picture key={banner.id}>
          {banner.mobile_image && (
            <source
              media="(max-width: 640px)"
              srcSet={banner.mobile_image}
            />
          )}
          <img
            src={banner.image}
            alt=""
            className="hero-banner-image"
          />
        </picture>
      </div>

      <div className="hero-banner-overlay" />

      <div className="hero-banner-inner">
        <div className="hero-banner-content" key={banner.id}>
          <span className="hero-eyebrow">
            XUMO · SPORT & LIFESTYLE
          </span>

          <h1>{banner.title}</h1>

          {banner.subtitle && (
            <p className="hero-banner-description">
              {banner.subtitle}
            </p>
          )}

          {banner.button_text && (
            <Link to={buttonUrl} className="hero-banner-button">
              {banner.button_text}
              <ArrowUpRight size={20} />
            </Link>
          )}
        </div>
      </div>

      {banners.length > 1 && (
        <div className="hero-banner-controls">
          <button
            type="button"
            onClick={() => goTo(activeIndex - 1)}
            aria-label="Oldingi banner"
          >
            <ChevronLeft size={21} />
          </button>

          <div className="hero-banner-dots">
            {banners.map((item, index) => (
              <button
                type="button"
                key={item.id}
                className={index === activeIndex ? "active" : ""}
                onClick={() => goTo(index)}
                aria-label={`${index + 1}-banner`}
                aria-current={index === activeIndex ? "true" : undefined}
              />
            ))}
          </div>

          <button
            type="button"
            onClick={() => goTo(activeIndex + 1)}
            aria-label="Keyingi banner"
          >
            <ChevronRight size={21} />
          </button>
        </div>
      )}
    </section>
  );
}
