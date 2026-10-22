
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ShoppingCart,
  Plus,
  UtensilsCrossed,
  Check,
} from "lucide-react";

import {
  addRestaurantItem,
  getRestaurantCart,
} from "../utils/restaurantCart";

import "./RestaurantMenu.css";

function readResults(data) {
  return Array.isArray(data)
    ? data
    : Array.isArray(data?.results)
      ? data.results
      : [];
}

export default function RestaurantMenuPage() {
  const [subcategories, setSubcategories] = useState([]);
  const [foods, setFoods] = useState([]);
  const [selected, setSelected] = useState("all");
  const [cart, setCart] = useState(getRestaurantCart);
  const [addedId, setAddedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadMenu() {
      try {
        const [subRes, foodRes] = await Promise.all([
          fetch("/api/v1/subcategories/", {
            signal: controller.signal,
          }),
          fetch("/api/v1/foods/", {
            signal: controller.signal,
          }),
        ]);

        if (!subRes.ok || !foodRes.ok) {
          throw new Error("Restoran menyusini yuklab bo‘lmadi.");
        }

        const [subData, foodData] = await Promise.all([
          subRes.json(),
          foodRes.json(),
        ]);

        if (!controller.signal.aborted) {
          setSubcategories(readResults(subData));
          setFoods(readResults(foodData));
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

    loadMenu();

    return () => controller.abort();
  }, []);

  useEffect(() => {
    function syncCart() {
      setCart(getRestaurantCart());
    }

    window.addEventListener("restaurant-cart-changed", syncCart);
    window.addEventListener("storage", syncCart);

    return () => {
      window.removeEventListener("restaurant-cart-changed", syncCart);
      window.removeEventListener("storage", syncCart);
    };
  }, []);

  function handleAdd(food) {
    const success = addRestaurantItem(food);

    if (success) {
      setCart(getRestaurantCart());
      setAddedId(food.id);
    }
  }

  const visibleFoods = foods.filter(
    (food) =>
      selected === "all" ||
      String(food.subcategory) === selected
  );

  const cartCount = Object.values(cart).reduce(
    (sum, quantity) => sum + Number(quantity || 0),
    0
  );

  return (
    <main className="restaurant-page">
      <div className="restaurant-container">
        <header className="restaurant-heading">
          <div>
            <span className="restaurant-eyebrow">
              FC BUKHARA · RESTAURANT
            </span>

            <h1>Restoran menyusi</h1>

            <p>
              Sevimli taomlaringizni tanlang va buyurtma bering.
            </p>
          </div>

          <Link
            to="/restaurant/cart"
            className="restaurant-cart-link"
          >
            <ShoppingCart size={20} />
            Savatcha ({cartCount})
          </Link>
        </header>

        {loading && (
          <div className="restaurant-message">
            Taomlar yuklanmoqda...
          </div>
        )}

        {error && (
          <div className="restaurant-message" role="alert">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="restaurant-tabs">
              <button
                type="button"
                className={selected === "all" ? "active" : ""}
                onClick={() => setSelected("all")}
              >
                Barchasi
              </button>

              {subcategories.map((subcategory) => (
                <button
                  type="button"
                  key={subcategory.id}
                  className={
                    selected === String(subcategory.id)
                      ? "active"
                      : ""
                  }
                  onClick={() =>
                    setSelected(String(subcategory.id))
                  }
                >
                  {subcategory.name}
                </button>
              ))}
            </div>

            {visibleFoods.length === 0 ? (
              <div className="restaurant-message">
                Hozircha bu bo‘limda taom mavjud emas.
              </div>
            ) : (
              <div className="restaurant-grid">
                {visibleFoods.map((food) => {
                  const inCart = Number(cart[food.id] || 0);
                  const stock = Number(food.stock);
                  const available = stock > inCart;

                  return (
                    <article
                      className="restaurant-food"
                      key={food.id}
                    >
                      <div className="restaurant-food-image">
                        {food.image ? (
                          <img
                            src={food.image}
                            alt={food.name}
                            loading="lazy"
                          />
                        ) : (
                          <div className="restaurant-food-placeholder">
                            <UtensilsCrossed size={45} />
                          </div>
                        )}
                      </div>

                      <div className="restaurant-food-body">
                        <h2>{food.name}</h2>

                        <p className="restaurant-food-description">
                          {food.description ||
                            "Mazali va sifatli taom."}
                        </p>

                        <div className="restaurant-food-meta">
                          <strong>
                            {Number(food.price).toLocaleString(
                              "uz-UZ"
                            )}{" "}
                            so‘m
                          </strong>

                          <span>
                            Mavjud: {stock}
                          </span>
                        </div>

                        <button
                          type="button"
                          className="restaurant-add-button"
                          disabled={!available}
                          onClick={() => handleAdd(food)}
                        >
                          {!available ? (
                            "Mavjud emas"
                          ) : addedId === food.id ? (
                            <>
                              <Check size={18} />
                              Yana qo‘shish
                            </>
                          ) : (
                            <>
                              <Plus size={18} />
                              Savatchaga qo‘shish
                            </>
                          )}
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
