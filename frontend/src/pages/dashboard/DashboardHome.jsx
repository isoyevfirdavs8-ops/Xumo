
import { Link } from "react-router-dom";
import { Images, ArrowUpRight } from "lucide-react";

export default function DashboardHome() {
  return (
    <div>
      <div className="dashboard-page-heading">
        <h1>Dashboard</h1>
      </div>

      <div className="dashboard-card">
        <Images size={35} color="#c79b4b" />

        <h2>Bannerlarni boshqarish</h2>

        <p>
          Saytning bosh sahifasidagi bannerlarni qo‘shish,
          tahrirlash va boshqarish.
        </p>

        <Link
          to="/dashboard/banners"
          className="dashboard-primary-btn"
        >
          Bannerlar bo‘limi
          <ArrowUpRight size={18} />
        </Link>
      </div>
    </div>
  );
}
