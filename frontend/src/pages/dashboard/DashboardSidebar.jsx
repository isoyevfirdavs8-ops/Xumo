
import { NavLink, Link } from "react-router-dom";

import {
  LayoutDashboard,
  Images,
  Layers3,
  CalendarDays,
  Users,
  ShoppingBag,
  UtensilsCrossed,
  ArrowLeft,
  Shield,
  UsersRound,
  Trophy,
  PanelBottom,
  Goal,
  CircleDot,
  Dumbbell,
  ChartNoAxesCombined,
  BedDouble,
} from "lucide-react";

import "./DashboardSidebar.css";

const menuItems = [
  {
    title: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
    end: true,
  },
  {
    title: "Stadionlar",
    path: "/dashboard/football-fields",
    icon: Goal,
  },
  {
    title: "Futbol akademiyalari",
    path: "/dashboard/football-academies",
    icon: Goal,
  },

  {
    title: "Tennis kortlari",
    path: "/dashboard/tennis-courts",
    icon: CircleDot,
  },
  {
    title: "Boks akademiyasi",
    path: "/dashboard/boxing-academies",
    icon: Dumbbell,
  },
  {
    title: "Yotoqxona",
    path: "/dashboard/hostel-rooms",
    icon: BedDouble,
  },

  {
    title: "Bannerlar",
    path: "/dashboard/banners",
    icon: Images,
  },
  {
    title: "Kategoriyalar",
    path: "/dashboard/categories",
    icon: Layers3,
  },
  {
    title: "Murabbiylar",
    path: "/dashboard/coaches",
    icon: UsersRound,
  },
  {
    title: "Musobaqalar",
    path: "/dashboard/competitions",
    icon: Trophy,
  },
  {
    title: "Subkategoriyalar",
    path: "/dashboard/subcategories",
    icon: Layers3,
  },
  {
    title: "Restoran taomlari",
    path: "/dashboard/foods",
    icon: UtensilsCrossed,
  },
  {
    title: "Foydalanuvchilar",
    path: "/dashboard/users",
    icon: Users,
  },
  {
    title: "Football Academy davomati",
    path: "/dashboard/attendance/football",
    icon: Goal,
  },
  {
    title: "Boks davomati",
    path: "/dashboard/attendance/boxing",
    icon: Dumbbell,
  },
  {
    title: "Tennis davomati",
    path: "/dashboard/attendance/tennis",
    icon: CalendarDays,
  },

  {
    title: "Footer sozlamalari",
    path: "/dashboard/footer",
    icon: PanelBottom,
  },
  {
    title: "Moliyaviy statistika",
    path: "/dashboard/finance",
    icon: ChartNoAxesCombined,
  },




];
const futureItems = [

];



export default function DashboardSidebar() {
  return (
    <aside className="dashboard-sidebar">
      <Link to="/dashboard" className="dashboard-brand">
        <Shield size={32} />

        <div>
          <strong>FC BUKHARA</strong>
          <span>ADMIN PANEL</span>
        </div>
      </Link>

      <div className="dashboard-menu-label">
        BOSHQARUV
      </div>

      <nav className="dashboard-menu">
        {menuItems.map(({ title, path, icon: Icon, end }) => (
          <NavLink
            key={path}
            to={path}
            end={end}
            className={({ isActive }) =>
              `dashboard-menu-item ${isActive ? "active" : ""}`
            }
          >
            <Icon size={19} />
            <span>{title}</span>
          </NavLink>
        ))}
      </nav>


      <div className="dashboard-menu">
        {futureItems.map(({ title, icon: Icon }) => (
          <div
            key={title}
            className="dashboard-menu-item disabled"
            title="Tez orada"
          >
            <Icon size={19} />
            <span>{title}</span>
          </div>
        ))}
      </div>

      <Link to="/" className="dashboard-back-link">
        <ArrowLeft size={18} />
        <span>Saytga qaytish</span>
      </Link>
    </aside>
  );
}