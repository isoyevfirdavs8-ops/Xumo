
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  ShoppingBag,
  Trash2,
  UtensilsCrossed,
} from "lucide-react";

import {
  getRestaurantCart,
  updateRestaurantItem,
} from "../utils/restaurantCart";

import "./RestaurantCart.css";

const formatPrice = (price) =>
  Number(price).toLocaleString("uz-UZ") + " so‘m";

export default function RestaurantCartPage() {
  const navigate = useNavigate();

  const [cart, setCart] = useState(() => getRestaurantCart());
  const [foods, setFoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadFoods() {
      try {
        setLoading(true);

        const response = await fetch("/api/v1/foods/", {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(
            `Taomlarni yuklab bo‘lmadi (HTTP ${response.status}).`
          );
        }

        const data = await response.json();

        if (!controller.signal.aborted) {
          setFoods(
            Array.isArray(data)
              ? data
              : Array.isArray(data.results)
                ? data.results
                : []
          );
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadFoods();

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const syncCart = () => setCart(getRestaurantCart());

    window.addEventListener(
      "restaurant-cart-changed",
      syncCart
    );

    window.addEventListener("storage", syncCart);

    return () => {
      window.removeEventListener(
        "restaurant-cart-changed",
        syncCart
      );

      window.removeEventListener("storage", syncCart);
    };
  }, []);

  const items = foods
    .filter((food) => Number(cart[food.id] || 0) > 0)
    .map((food) => ({
      ...food,
      quantity: Number(cart[food.id]),
    }));

  const totalQuantity = items.reduce(
    (sum, food) => sum + food.quantity,
    0
  );

  const total = items.reduce(
    (sum, food) =>
      sum + Number(food.price) * food.quantity,
    0
  );

  const hasStockIssue = items.some(
    (food) =>
      food.quantity > Number(food.stock) ||
      Number(food.stock) <= 0
  );

  function changeQuantity(food, quantity) {
    if (quantity > Number(food.stock)) return;

    updateRestaurantItem(food.id, Math.max(0, quantity));
    setCart(getRestaurantCart());
  }

  function removeItem(food) {
    updateRestaurantItem(food.id, 0);
    setCart(getRestaurantCart());
  }

  function checkout() {
    if (!items.length || hasStockIssue) return;

    const token = sessionStorage.getItem("access_token");

    if (!token) {
      navigate(
        `/login?next=${encodeURIComponent(
          "/restaurant/checkout"
        )}`
      );
      return;
    }

    navigate("/restaurant/checkout");
  }

  return (
    <main className="restaurant-cart-page">
      <div className="restaurant-cart-container">

        <div className="restaurant-cart-heading">
          <span>FC BUKHARA · RESTAURANT</span>
          <h1>Savatchangiz</h1>
          <p>
            Tanlangan taomlarni tekshiring va buyurtmani
            rasmiylashtiring.
          </p>

          <Link
            to="/restaurant"
            className="restaurant-cart-back"
          >
            <ArrowLeft size={17} />
            Restoran menyusiga qaytish
          </Link>
        </div>

        {error && (
          <div className="restaurant-cart-error" role="alert">
            {error}
          </div>
        )}

        {loading ? (
          <div className="restaurant-cart-empty">
            <p>Taomlar yuklanmoqda...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="restaurant-cart-empty">
            <ShoppingBag size={48} />

            <h2>Savatchangiz bo‘sh</h2>

            <p>
              Restoran menyusidan o‘zingizga yoqqan
              taomlarni tanlang.
            </p>

            <Link
              to="/restaurant"
              className="restaurant-cart-checkout"
            >
              <UtensilsCrossed size={18} />
              Taomlarni ko‘rish
            </Link>
          </div>
        ) : (
          <div className="restaurant-cart-layout">

            {/* MAHSULOTLAR */}
            <section
              className="restaurant-cart-items"
              aria-label="Savatchadagi mahsulotlar"
            >
              {items.map((food) => {
                const stock = Number(food.stock);
                const stockProblem =
                  stock <= 0 || food.quantity > stock;

                return (
                  <article
                    className="restaurant-cart-item"
                    key={food.id}
                  >
                    <div className="restaurant-cart-item-image">
                      {food.image ? (
                        <img
                          src={food.image}
                          alt={food.name}
                          loading="lazy"
                        />
                      ) : (
                        <div className="restaurant-cart-image-empty">
                          <UtensilsCrossed size={32} />
                        </div>
                      )}
                    </div>

                    <div className="restaurant-cart-item-info">
                      <div className="restaurant-cart-item-title">
                        <h2>{food.name}</h2>

                        <button
                          type="button"
                          className="restaurant-cart-remove"
                          onClick={() => removeItem(food)}
                          aria-label={`${food.name}ni savatchadan o‘chirish`}
                          title="O‘chirish"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>

                      <p className="restaurant-cart-unit-price">
                        {formatPrice(food.price)} / dona
                      </p>

                      <span className="restaurant-cart-stock">
                        Omborda: {stock} dona
                      </span>

                      {stockProblem && (
                        <p
                          className="restaurant-cart-stock-error"
                          role="alert"
                        >
                          Tanlangan miqdor ombordagi
                          mavjud miqdordan ko‘p.
                        </p>
                      )}

                      <div className="restaurant-cart-item-bottom">
                        <div className="restaurant-cart-quantity">
                          <button
                            type="button"
                            onClick={() =>
                              changeQuantity(
                                food,
                                food.quantity - 1
                              )
                            }
                            aria-label="Miqdorni kamaytirish"
                          >
                            −
                          </button>

                          <span>{food.quantity}</span>

                          <button
                            type="button"
                            disabled={
                              food.quantity >= stock
                            }
                            onClick={() =>
                              changeQuantity(
                                food,
                                food.quantity + 1
                              )
                            }
                            aria-label="Miqdorni oshirish"
                          >
                            +
                          </button>
                        </div>

                        <strong className="restaurant-cart-subtotal">
                          {formatPrice(
                            Number(food.price) *
                              food.quantity
                          )}
                        </strong>
                      </div>
                    </div>
                  </article>
                );
              })}
            </section>

            {/* BUYURTMA XULOSASI */}
            <aside className="restaurant-cart-summary">
              <h2>Buyurtma xulosasi</h2>

              <div className="restaurant-cart-summary-row">
                <span>Mahsulot turlari</span>
                <strong>{items.length} ta</strong>
              </div>

              <div className="restaurant-cart-summary-row">
                <span>Jami miqdor</span>
                <strong>{totalQuantity} dona</strong>
              </div>

              <div className="restaurant-cart-summary-row">
                <span>Mahsulotlar narxi</span>
                <strong>{formatPrice(total)}</strong>
              </div>

              <div className="restaurant-cart-summary-total">
                <span>Jami</span>
                <strong>{formatPrice(total)}</strong>
              </div>

              <button
                type="button"
                className="restaurant-cart-checkout"
                onClick={checkout}
                disabled={hasStockIssue}
              >
                Buyurtmani rasmiylashtirish
                <ArrowRight size={19} />
              </button>

              <p className="restaurant-cart-note">
                To‘lov usulini keyingi bosqichda
                tanlaysiz.
              </p>
            </aside>

          </div>
        )}
      </div>
    </main>
  );
}
