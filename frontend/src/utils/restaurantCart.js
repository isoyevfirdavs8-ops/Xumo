
const KEY = "fc_bukhara_restaurant_cart";

export function getRestaurantCart() {
  try {
    const data = JSON.parse(localStorage.getItem(KEY) || "{}");
    return data && typeof data === "object" && !Array.isArray(data)
      ? data
      : {};
  } catch {
    return {};
  }
}

export function saveRestaurantCart(cart) {
  localStorage.setItem(
    "fc_bukhara_restaurant_cart",
    JSON.stringify(cart)
  );

  window.dispatchEvent(
    new Event("restaurant-cart-changed")
  );
}

export function addRestaurantItem(food) {
  const cart = getRestaurantCart();
  const id = String(food.id);
  const current = Number(cart[id] || 0);

  if (!food.is_active || Number(food.stock) <= current) {
    return false;
  }

  saveRestaurantCart({ ...cart, [id]: current + 1 });
  return true;
}

export function updateRestaurantItem(id, quantity) {
  const cart = getRestaurantCart();
  const key = String(id);

  if (quantity <= 0) {
    delete cart[key];
  } else {
    cart[key] = Math.floor(quantity);
  }

  saveRestaurantCart(cart);
}

export function clearRestaurantCart() {
  localStorage.removeItem(KEY);
  window.dispatchEvent(new Event("restaurant-cart-changed"));
}
