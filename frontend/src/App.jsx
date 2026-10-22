
import { useEffect } from "react";

import {
  BrowserRouter,
  Routes,
  Route,
  Outlet,
  useLocation,
  Navigate,
} from "react-router-dom";

// PUBLIC COMPONENTS
import Header from "./components/layout/Header";
import Footer from "./components/layout/Footer";

import HeroBanner from "./components/home/HeroBanner";
import CategoriesSection from "./components/home/CategoriesSection";
import CoachesSection from "./components/home/CoachesSection";

// AUTH PAGES
import RegisterPage from "./pages/auth/RegisterPage";
import LoginPage from "./pages/auth/LoginPage";
import ProfilePage from "./pages/auth/ProfilePage";

// PUBLIC PAGES
import CategoryDetailPage from "./pages/CategoryDetailPage";
import CoachDetailPage from "./pages/CoachDetailPage";
import CompetitionsPage from "./pages/CompetitionsPage";
import CompetitionDetailPage from "./pages/CompetitionDetailPage";
import ServicesPage from "./pages/ServicesPage";

// RESTAURANT PAGES
import RestaurantMenuPage from "./pages/RestaurantMenuPage";
import RestaurantCartPage from "./pages/RestaurantCartPage";
import RestaurantCheckoutPage from "./pages/RestaurantCheckoutPage";
import RestaurantPaymentPage from "./pages/RestaurantPaymentPage";
import RestaurantOrderSuccessPage from "./pages/RestaurantOrderSuccessPage";

import "./pages/RestaurantCheckout.css";

// DASHBOARD
import DashboardLayout from "./pages/dashboard/DashboardLayout";
import DashboardHome from "./pages/dashboard/DashboardHome";

// BANNERS
import BannerList from "./pages/dashboard/banners/BannerList";
import BannerForm from "./pages/dashboard/banners/BannerForm";

// CATEGORIES
import CategoryList from "./pages/dashboard/categories/CategoryList";
import CategoryForm from "./pages/dashboard/categories/CategoryForm";

// COACHES
import CoachList from "./pages/dashboard/coaches/CoachList";
import CoachForm from "./pages/dashboard/coaches/CoachForm";

// COMPETITIONS
import CompetitionList from "./pages/dashboard/competitions/CompetitionList";
import CompetitionForm from "./pages/dashboard/competitions/CompetitionForm";

// SUBCATEGORIES AND FOODS
import SubCategoryPage from "./pages/dashboard/subcategories/SubCategoryPage";
import FoodPage from "./pages/dashboard/foods/FoodPage";

// FOOTER SETTINGS
import FooterSettingsPage from "./pages/dashboard/footer/FooterSettingsPage";
import FootballPage from "./pages/FootballPage";
import FootballFieldsPage from "./pages/dashboard/FootballFieldsPage";

import TennisCourtsPage from "./pages/dashboard/TennisCourtsPage";
import TennisPage from "./pages/TennisPage";

import BoxingAcademiesPage from "./pages/dashboard/BoxingAcademiesPage";
import BoxingPage from "./pages/BoxingPage";

import FinanceDashboardPage from "./pages/dashboard/FinanceDashboardPage";

import UsersPage from "./pages/dashboard/users/UsersPage";

import AboutPage from "./pages/about/AboutPage";
import AboutManagePage from "./pages/about/AboutManagePage";

import AttendancePage from "./pages/dashboard/attendance/AttendancePage";
import AttendanceDetailPage from "./pages/dashboard/attendance/AttendanceDetailPage";

import FootballAcademiesPage from "./pages/dashboard/FootballAcademiesPage";
import HostelRoomsPage from "./pages/dashboard/HostelRoomsPage";
import HostelBookingPage from "./pages/HostelBookingPage";
// ========================================
// SCROLL TO HASH
// ========================================

function ScrollToHash() {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    if (!hash) return;

    let cancelled = false;
    let frameId;
    let attempts = 0;

    const maxAttempts = 30;

    function scrollToTarget() {
      if (cancelled) return;

      let id;

      try {
        id = decodeURIComponent(hash.slice(1));
      } catch {
        return;
      }

      const target = document.getElementById(id);

      if (target) {
        target.scrollIntoView({
          behavior: window.matchMedia(
            "(prefers-reduced-motion: reduce)"
          ).matches
            ? "auto"
            : "smooth",
          block: "start",
        });

        return;
      }

      attempts += 1;

      if (attempts < maxAttempts) {
        frameId = requestAnimationFrame(scrollToTarget);
      }
    }

    frameId = requestAnimationFrame(scrollToTarget);

    return () => {
      cancelled = true;

      if (frameId) {
        cancelAnimationFrame(frameId);
      }
    };
  }, [pathname, hash]);

  return null;
}

// ========================================
// PUBLIC LAYOUT
// ========================================

function PublicLayout() {
  return (
    <>
      <Header />

      <Outlet />

      <Footer />
    </>
  );
}

// ========================================
// HOME PAGE
// ========================================

function HomePage() {
  return (
    <main>
      <HeroBanner />
      <CategoriesSection />
      <CoachesSection />
    </main>
  );
}

// ========================================
// APP ROUTES
// ========================================

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToHash />

      <Routes>
        {/* ===================================
            PUBLIC ROUTES
        =================================== */}

        <Route element={<PublicLayout />}>
          <Route
            path="/"
            element={<HomePage />}
          />

          <Route
            path="services"
            element={<ServicesPage />}
          />
          <Route path="/football" element={<FootballPage />} />
          <Route path="/tennis" element={<TennisPage />} />
          <Route path="/boxing" element={<BoxingPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="about/manage" element={<AboutManagePage />} />

          {/* AUTH */}
          <Route
            path="register"
            element={<RegisterPage />}
          />

          <Route
            path="login"
            element={<LoginPage />}
          />

          <Route
            path="profile"
            element={<ProfilePage />}
          />
          {/* HOSTEL BOOKING */}
<Route
  path="hostel"
  element={<HostelBookingPage />}
/>

<Route
  path="categories/yotoqxona"
  element={<Navigate to="/hostel" replace />}
/>

<Route
  path="categories/hostel"
  element={<Navigate to="/hostel" replace />}
/>

<Route
  path="categories/hotel"
  element={<Navigate to="/hostel" replace />}
/>

          {/* CATEGORIES */}
          <Route
  path="categories/futbol"
  element={<Navigate to="/football" replace />}
/>

<Route
  path="categories/tennis"
  element={<Navigate to="/tennis" replace />}
/>

<Route
  path="categories/boks"
  element={<Navigate to="/boxing" replace />}
/>

<Route
  path="categories/:slug"
  element={<CategoryDetailPage />}
/>

          {/* COACHES */}
          <Route
            path="coaches/:id"
            element={<CoachDetailPage />}
          />

          {/* COMPETITIONS */}
          <Route
            path="competitions"
            element={<CompetitionsPage />}
          />

          <Route
            path="competitions/:id"
            element={<CompetitionDetailPage />}
          />

          {/* RESTAURANT */}
          <Route
            path="restaurant"
            element={<RestaurantMenuPage />}
          />

          <Route
            path="restaurant/cart"
            element={<RestaurantCartPage />}
          />

          <Route
            path="restaurant/checkout"
            element={<RestaurantCheckoutPage />}
          />

          <Route
            path="restaurant/orders/:orderId/payment"
            element={<RestaurantPaymentPage />}
          />

          <Route
            path="restaurant/orders/:orderId/success"
            element={<RestaurantOrderSuccessPage />}
          />
        </Route>

        {/* ===================================
            DASHBOARD ROUTES
        =================================== */}

        <Route
          path="/dashboard"
          element={<DashboardLayout />}
        >
          <Route
            index
            element={<DashboardHome />}
          />
          <Route path="football-fields" element={<FootballFieldsPage />} />
          <Route
            path="/dashboard/attendance/:sport"
            element={<AttendancePage />}
          />
          <Route
            path="hostel-rooms"
            element={<HostelRoomsPage />}
          />
          <Route
            path="football-academies"
            element={<FootballAcademiesPage />}
          />

          <Route
            path="/dashboard/attendance/:sport/:id"
            element={<AttendanceDetailPage />}
          />

          <Route
            path="tennis-courts"
            element={<TennisCourtsPage />}
          />
          <Route
            path="users"
            element={<UsersPage />}
          />

          <Route
            path="finance"
            element={<FinanceDashboardPage />}
          />

          <Route
            path="boxing-academies"
            element={<BoxingAcademiesPage />}
          />

          {/* BANNERS */}
          <Route
            path="banners"
            element={<BannerList />}
          />

          <Route
            path="banners/create"
            element={<BannerForm />}
          />

          <Route
            path="banners/:id/edit"
            element={<BannerForm />}
          />

          {/* COMPETITIONS */}
          <Route
            path="competitions"
            element={<CompetitionList />}
          />

          <Route
            path="competitions/create"
            element={<CompetitionForm />}
          />

          <Route
            path="competitions/:id/edit"
            element={<CompetitionForm />}
          />

          {/* SUBCATEGORIES */}
          <Route
            path="subcategories"
            element={<SubCategoryPage />}
          />

          {/* FOODS */}
          <Route
            path="foods"
            element={<FoodPage />}
          />

          {/* CATEGORIES */}
          <Route
            path="categories"
            element={<CategoryList />}
          />

          <Route
            path="categories/create"
            element={<CategoryForm />}
          />

          <Route
            path="categories/:id/edit"
            element={<CategoryForm />}
          />

          {/* COACHES */}
          <Route
            path="coaches"
            element={<CoachList />}
          />

          <Route
            path="coaches/create"
            element={<CoachForm />}
          />

          <Route
            path="coaches/:id/edit"
            element={<CoachForm />}
          />

          {/* FOOTER SETTINGS */}
          <Route
            path="footer"
            element={<FooterSettingsPage />}
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
