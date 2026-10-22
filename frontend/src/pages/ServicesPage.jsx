
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

import CategoriesSection from "../components/home/CategoriesSection";

import "./ServicesPage.css";

export default function ServicesPage() {
  return (
    <main className="services-page">
      <div className="services-page-top">
        <div className="services-page-container">
          <Link to="/" className="services-page-back">
            <ArrowLeft size={18} />
            Bosh sahifaga qaytish
          </Link>
        </div>
      </div>

      <CategoriesSection />
    </main>
  );
}
