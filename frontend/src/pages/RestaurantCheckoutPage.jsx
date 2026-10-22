
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getRestaurantCart } from "../utils/restaurantCart";

const FOOD_API = "/api/v1/foods/";
const CHECKOUT_API = "/api/v1/restaurant/checkout/";

export default function RestaurantCheckoutPage() {
  const navigate = useNavigate();
  const checkoutKey = useRef(crypto.randomUUID());

  const [foods, setFoods] = useState([]);
  const [cart] = useState(getRestaurantCart);
  const [provider, setProvider] = useState("click");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const response = await fetch(FOOD_API, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("Taomlarni yuklab bo‘lmadi.");
        }

        const data = await response.json();

        setFoods(
          Array.isArray(data) ? data : data.results || []
        );
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
  }, []);

  const selectedItems = Object.entries(cart)
    .filter(([, quantity]) => Number(quantity) > 0)
    .map(([id, quantity]) => {
      const food = foods.find(
        (item) => String(item.id) === id
      );

      return food
        ? { ...food, quantity: Number(quantity) }
        : null;
    });

  const items = selectedItems.filter(Boolean);
  const hasMissingFood = selectedItems.some((item) => !item);

  const hasStockError = items.some(
    (food) => food.quantity > Number(food.stock)
  );

  const total = items.reduce(
    (sum, food) =>
      sum + Number(food.price) * food.quantity,
    0
  );

  async function submitCheckout(event) {
    event.preventDefault();

    if (submitting || loading) return;

    const token = sessionStorage.getItem("access_token");

    if (!token) {
      navigate(
        `/login?next=${encodeURIComponent("/restaurant/checkout")}`
      );
      return;
    }

    if (!items.length || hasMissingFood || hasStockError) {
      setError(
        "Savatchadagi taomlar yoki ombor qoldig‘ini tekshiring."
      );
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const response = await fetch(CHECKOUT_API, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          provider,
          idempotency_key: checkoutKey.current,
          items: items.map((food) => ({
            food_id: food.id,
            quantity: food.quantity,
          })),
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data)
        );
      }

      navigate(`/restaurant/orders/${data.id}/payment`);
    } catch (err) {
      setError(err.message || "Checkout xatosi.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="restaurant-page">
      <Link to="/restaurant/cart">
        ← Savatchaga qaytish
      </Link>

      <h1>Buyurtmani rasmiylashtirish</h1>
      <p>Taomlar va to‘lov usulini tekshiring.</p>

      {error && <p role="alert">{error}</p>}
      {loading && <p>Yuklanmoqda...</p>}

      {!loading && (
        <form onSubmit={submitCheckout}>
          <section className="restaurant-checkout-card">
            <h2>Buyurtmangiz</h2>

            {items.map((food) => (
              <div
                key={food.id}
                className="restaurant-checkout-line"
              >
                <span>
                  {food.name} × {food.quantity}
                </span>
                <strong>
                  {(
                    Number(food.price) * food.quantity
                  ).toLocaleString("uz-UZ")} so‘m
                </strong>
              </div>
            ))}

            <div className="restaurant-checkout-total">
              <strong>Jami</strong>
              <strong>
                {total.toLocaleString("uz-UZ")} so‘m
              </strong>
            </div>
          </section>

          <section className="restaurant-checkout-card">
            <h2>To‘lov usuli</h2>

            <label className="restaurant-payment-option">
              <input
                type="radio"
                name="provider"
                value="click"
                checked={provider === "click"}
                onChange={(event) => {
                  setProvider(event.target.value);
                  checkoutKey.current = crypto.randomUUID();
                }}
              />
              Click — TEST
            </label>

            <label className="restaurant-payment-option">
              <input
                type="radio"
                name="provider"
                value="payme"
                checked={provider === "payme"}
                onChange={(event) => {
                  setProvider(event.target.value);
                  checkoutKey.current = crypto.randomUUID();
                }}
              />
              Payme — TEST
            </label>

            <p>
              Test rejimida haqiqiy pul yechilmaydi.
            </p>
          </section>

          <button
            type="submit"
            className="restaurant-checkout-button"
            disabled={
              submitting ||
              !items.length ||
              hasMissingFood ||
              hasStockError
            }
          >
            {submitting
              ? "Buyurtma yaratilmoqda..."
              : "Buyurtmani yaratish"}
          </button>
        </form>
      )}
    </main>
  );
}
