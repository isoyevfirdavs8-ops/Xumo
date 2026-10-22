
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { clearRestaurantCart } from "../utils/restaurantCart";

export default function RestaurantPaymentPage() {
  const { orderId } = useParams();
  const navigate = useNavigate();

  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState("");

  const token = sessionStorage.getItem("access_token");

  useEffect(() => {
    if (!token) {
      navigate(
        `/login?next=${encodeURIComponent(
          `/restaurant/orders/${orderId}/payment`
        )}`,
        { replace: true }
      );
      return;
    }

    const controller = new AbortController();

    async function load() {
      try {
        const response = await fetch(
          `/api/v1/restaurant/orders/${orderId}/`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: controller.signal,
          }
        );

        if (!response.ok) {
          throw new Error("Buyurtma topilmadi.");
        }

        const data = await response.json();
        setOrder(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, [orderId, token, navigate]);

  async function pay() {
    if (paying || !order || order.status !== "pending") return;

    setPaying(true);
    setError("");

    try {
      const response = await fetch(
        `/api/v1/restaurant/orders/${orderId}/sandbox-pay/`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || "Test to‘lov amalga oshmadi."
        );
      }

      if (data.status !== "paid") {
        throw new Error("To‘lov tasdiqlanmadi.");
      }

      clearRestaurantCart();
      navigate(`/restaurant/orders/${orderId}/success`, {
        replace: true,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setPaying(false);
    }
  }

  if (loading) return <main className="restaurant-page">Yuklanmoqda...</main>;

  return (
    <main className="restaurant-page">
      <h1>To‘lov</h1>

      {error && <p role="alert">{error}</p>}

      {order && (
        <section className="restaurant-checkout-card">
          <p>Buyurtma: {order.id}</p>
          <h2>
            {Number(order.total_amount).toLocaleString("uz-UZ")} so‘m
          </h2>
          <p>
            To‘lov usuli: {order.provider.toUpperCase()}
          </p>
          <p>Holati: {order.status}</p>

          {order.status === "pending" && (
            <button
              className="restaurant-checkout-button"
              disabled={paying}
              onClick={pay}
            >
              {paying
                ? "Tekshirilmoqda..."
                : `${order.provider.toUpperCase()} — test to‘lov`}
            </button>
          )}

          {order.status === "paid" && (
            <Link to={`/restaurant/orders/${orderId}/success`}>
              Buyurtmani ko‘rish
            </Link>
          )}
        </section>
      )}
    </main>
  );
}
