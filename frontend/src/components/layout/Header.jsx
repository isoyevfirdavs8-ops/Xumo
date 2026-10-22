
import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";

import {
  hasSession,
  getValidAccessToken,
} from "../../utils/auth";

import {
  Menu,
  X,
  ShoppingCart,
  UserRound,
} from "lucide-react";

import { getRestaurantCart } from "../../utils/restaurantCart";
import "./Header.css";

const NAV_CACHE_KEY = "fc_bukhara_navigation";
const NAV_CACHE_TTL = 5 * 60 * 1000;

let navigationPromise = null;
let navigationRetryAfter = 0;

// ========================================
// NAVIGATION CACHE
// ========================================

function getCachedNavigation() {
  try {
    const raw = sessionStorage.getItem(NAV_CACHE_KEY);

    if (!raw) return null;

    const cached = JSON.parse(raw);

    if (
      !Array.isArray(cached.navigation) ||
      Date.now() - cached.timestamp > NAV_CACHE_TTL
    ) {
      return null;
    }

    return cached.navigation;
  } catch {
    return null;
  }
}

// ========================================
// FETCH NAVIGATION
// ========================================

async function fetchNavigation() {
  const cached = getCachedNavigation();

  if (cached !== null) {
    return cached;
  }

  if (Date.now() < navigationRetryAfter) {
    throw new Error("Navigatsiya vaqtincha cheklangan.");
  }

  if (navigationPromise) {
    return navigationPromise;
  }

  navigationPromise = (async () => {
    const response = await fetch("/api/v1/site/navigation/");

    if (response.status === 429) {
      const retrySeconds = Number(
        response.headers.get("Retry-After") || 60
      );

      navigationRetryAfter =
        Date.now() +
        (
          Number.isFinite(retrySeconds) && retrySeconds > 0
            ? retrySeconds
            : 60
        ) * 1000;

      throw new Error(
        "Navigatsiya so‘rovlari vaqtincha cheklangan (429)."
      );
    }

    if (!response.ok) {
      throw new Error(
        `Navigation API error: ${response.status}`
      );
    }

    const data = await response.json();

    const items = Array.isArray(data.navigation)
      ? data.navigation
      : [];

    sessionStorage.setItem(
      NAV_CACHE_KEY,
      JSON.stringify({
        timestamp: Date.now(),
        navigation: items,
      })
    );

    return items;
  })();

  try {
    return await navigationPromise;
  } finally {
    navigationPromise = null;
  }
}

// ========================================
// CART COUNT
// ========================================

function getCartCount() {
  const cart = getRestaurantCart();

  return Object.values(cart).reduce((total, quantity) => {
    const value = Number(quantity);

    return (
      total +
      (Number.isFinite(value) && value > 0 ? value : 0)
    );
  }, 0);
}

// ========================================
// HEADER COMPONENT
// ========================================

export default function Header() {
  const [navigation, setNavigation] = useState(
    () => getCachedNavigation() || []
  );

  const [menuOpen, setMenuOpen] = useState(false);
  const [cartCount, setCartCount] = useState(getCartCount);
  const [isLoggedIn, setIsLoggedIn] = useState(hasSession);

  // NAVIGATION
  useEffect(() => {
    let active = true;

    fetchNavigation()
      .then((items) => {
        if (active) {
          setNavigation(items);
        }
      })
      .catch((error) => {
        console.warn("Navigation:", error.message);
      });

    return () => {
      active = false;
    };
  }, []);

  // CART BADGE
  useEffect(() => {
    const updateCart = () => {
      setCartCount(getCartCount());
    };

    updateCart();

    window.addEventListener(
      "restaurant-cart-changed",
      updateCart
    );

    window.addEventListener("storage", updateCart);

    return () => {
      window.removeEventListener(
        "restaurant-cart-changed",
        updateCart
      );

      window.removeEventListener("storage", updateCart);
    };
  }, []);

  // AUTH STATE
  useEffect(() => {
    let active = true;

    async function syncAuth() {
      const sessionExists = hasSession();

      if (!active) return;

      setIsLoggedIn(sessionExists);

      if (!sessionExists) return;

      try {
        const token = await getValidAccessToken();

        if (!active) return;

        if (!token && !hasSession()) {
          setIsLoggedIn(false);
        }
      } catch {
        // Vaqtinchalik xatolikda Header ishlashda davom etadi.
      }
    }

    syncAuth();

    window.addEventListener("focus", syncAuth);
    window.addEventListener("storage", syncAuth);
    window.addEventListener("auth-changed", syncAuth);

    return () => {
      active = false;

      window.removeEventListener("focus", syncAuth);
      window.removeEventListener("storage", syncAuth);
      window.removeEventListener("auth-changed", syncAuth);
    };
  }, []);

  const closeMenu = () => setMenuOpen(false);

  return (
    <header className="site-header">
      <div className="header-container">

        {/* LOGO */}
        <Link
          to="/"
          className="brand"
          onClick={closeMenu}
        >
          <div className="brand-text">
            <strong>XUMO SPORT MAJMUASI</strong>
            <span>SPORT & LIFESTYLE</span>
          </div>
        </Link>

        {/* NAVIGATION */}
        <nav
          className={`header-nav ${menuOpen ? "open" : ""}`}
          aria-label="Asosiy navigatsiya"
        >
          {navigation.map((item) => {
            const isContact =
              item.label?.trim().toLowerCase() === "aloqa";

            const targetPath = isContact
              ? "/#contact"
              : item.path;

            return (
              <NavLink
                key={item.path}
                to={targetPath}
                end={targetPath === "/"}
                className={({ isActive }) =>
                  isActive && !isContact
                    ? "header-nav-link active"
                    : "header-nav-link"
                }
                onClick={closeMenu}
              >
                {item.label}
              </NavLink>
            );
          })}

          {/* MOBILE AUTH */}
          {!isLoggedIn && (
            <div className="mobile-auth-actions">
              <Link
                to="/register"
                className="register-btn"
                onClick={closeMenu}
              >
                Ro‘yxatdan o‘tish
              </Link>

              <Link
                to="/login"
                className="login-btn"
                onClick={closeMenu}
              >
                Kirish
              </Link>
            </div>
          )}
        </nav>

        {/* RIGHT ACTIONS */}
        <div className="header-actions">

          {/* DESKTOP AUTH */}
          {!isLoggedIn && (
            <div className="desktop-auth-actions">
              <Link
                to="/register"
                className="register-btn"
              >
                Ro‘yxatdan o‘tish
              </Link>

              <Link
                to="/login"
                className="login-btn"
              >
                Kirish
              </Link>
            </div>
          )}

          {/* CART */}
          <Link
            to="/restaurant/cart"
            className="header-cart-button"
            aria-label={`Savatcha, ${cartCount} ta mahsulot`}
            title="Savatcha"
            onClick={closeMenu}
          >
            <ShoppingCart size={22} />

            {cartCount > 0 && (
              <span className="header-cart-badge">
                {cartCount > 99 ? "99+" : cartCount}
              </span>
            )}
          </Link>

          {/* PROFILE */}
          <Link
            to="/profile"
            aria-label="Profil"
            title="Shaxsiy kabinet"
            onClick={closeMenu}
          >
            <UserRound size={21} />
          </Link>

          {/* MOBILE MENU */}
          <button
            type="button"
            className="mobile-menu-button"
            onClick={() => setMenuOpen((prev) => !prev)}
            aria-label={
              menuOpen
                ? "Menyuni yopish"
                : "Menyuni ochish"
            }
            aria-expanded={menuOpen}
          >
            {menuOpen ? (
              <X size={24} />
            ) : (
              <Menu size={24} />
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
