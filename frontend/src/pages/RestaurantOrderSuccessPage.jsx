
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";

export default function RestaurantOrderSuccessPage() {
  const { orderId } = useParams();
  const navigate = useNavigate();

  const [order, setOrder] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = sessionStorage.getItem("access_token");

    if (!token) {
      navigate("/login", { replace: true });
      return;
    }

    const controller = new AbortController();

    fetch(`/api/v1/restaurant/orders/${orderId}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Buyurtma ma’lumotlari topilmadi.");
        }
        return response.json();
      })
      .then((data) => setOrder(data))
      .catch((err) => {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      });

    return () => controller.abort();
  }, [orderId, navigate]);

  return (
    <main className="restaurant-page">
      {error && <p role="alert">{error}</p>}

      {!order && !error && <p>Buyurtma yuklanmoqda...</p>}

      {order?.status === "paid" ? (
        <section className="restaurant-success">
          <CheckCircle2 size={64} color="#22c55e" />

          <h1>Test to‘lov muvaffaqiyatli!</h1>
          <p>Buyurtmangiz tasdiqlandi.</p>

          <p>Buyurtma raqami: {order.id}</p>

          <h2>
            {Number(order.total_amount).toLocaleString("uz-UZ")} so‘m
          </h2>

          <h3>Buyurtmadagi taomlar</h3>

          {order.items.map((item) => (
            <div key={item.food_id} className="restaurant-checkout-line">
              <span>
                {item.name} × {item.quantity}
              </span>
              <strong>
                {Number(item.subtotal).toLocaleString("uz-UZ")} so‘m
              </strong>
            </div>
          ))}

          <Link to="/restaurant">
            Restoranga qaytish
          </Link>
        </section>
      ) : (
        order && (
          <section className="restaurant-checkout-card">
            <h1>Buyurtma hali to‘lanmagan</h1>
            <p>Holati: {order.status}</p>

            {order.status === "pending" && (
              <Link to={`/restaurant/orders/${orderId}/payment`}>
                To‘lovga qaytish
              </Link>
            )}
          </section>
        )
      )}
    </main>
  );
}
