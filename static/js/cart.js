// HOODRANKED cart page.
document.addEventListener("DOMContentLoaded", () => {
  const emptyState = document.getElementById("cart-empty");
  const cartContent = document.getElementById("cart-content");
  const itemsContainer = document.getElementById("cart-items");
  const toast = document.getElementById("cart-toast");

  function getCart() {
    const raw = localStorage.getItem("hoodranked_cart");
    try {
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  function saveCart(cart) {
    localStorage.setItem("hoodranked_cart", JSON.stringify(cart));
    window.hoodranked?.updateCartCount?.();
    renderCart();
  }

  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2500);
  }

  function renderCart() {
    const cart = getCart();
    itemsContainer.innerHTML = "";

    if (cart.length === 0) {
      cartContent.classList.add("hidden");
      emptyState.classList.remove("hidden");
      return;
    }

    cartContent.classList.remove("hidden");
    emptyState.classList.add("hidden");

    let subtotal = 0;

    cart.forEach((item, index) => {
      const itemTotal = item.price * item.quantity;
      subtotal += itemTotal;

      const row = document.createElement("div");
      row.className =
        "bg-surface-gray border border-muted-steel md:grid md:grid-cols-12 md:gap-6 md:p-6 md:items-center";
      row.dataset.index = index;

      row.innerHTML = `
        <div class="md:col-span-6 p-5 md:p-0 flex items-start md:items-center gap-5">
          <img src="${item.image}" alt="${item.name}" class="w-28 h-28 md:w-24 md:h-24 object-cover object-top bg-pitch-black flex-shrink-0">
          <div class="flex-1 min-w-0">
            <h4 class="font-body font-bold text-body-lg md:text-body-md text-stark-white truncate">${item.name}</h4>
            <a href="/product/${item.slug}" class="font-mono text-label-caps text-outline hover:text-stark-white transition-colors mt-2 block w-fit">
              View product
            </a>
          </div>
        </div>

        <div class="md:col-span-2 px-5 py-3 md:p-0 font-body text-body-md text-on-surface-variant md:text-center">
          <span class="font-mono text-label-caps text-outline md:hidden inline-block mr-2">Size:</span>${item.size}
        </div>

        <div class="md:col-span-2 px-5 py-3 md:p-0 font-body text-body-md text-on-surface-variant md:text-center">
          <span class="font-mono text-label-caps text-outline md:hidden inline-block mr-2">Price:</span>₦${item.price.toLocaleString()}
        </div>

        <div class="md:col-span-2 px-5 py-5 md:p-0 flex items-center justify-between md:justify-center gap-6">
          <div class="flex items-center border border-muted-steel">
            <button type="button" class="qty-decrement px-4 py-2 text-stark-white hover:bg-pitch-black transition-colors text-lg" aria-label="Decrease quantity">&minus;</button>
            <span class="px-6 py-2 font-body font-bold text-stark-white">${item.quantity}</span>
            <button type="button" class="qty-increment px-4 py-2 text-stark-white hover:bg-pitch-black transition-colors text-lg" aria-label="Increase quantity">+</button>
          </div>
          <button type="button" class="remove-item text-error hover:opacity-70 transition-opacity" aria-label="Remove item">
            <span class="material-symbols-outlined">delete</span>
          </button>
        </div>
      `;

      itemsContainer.appendChild(row);
    });

    document.getElementById("cart-subtotal").textContent = `₦${subtotal.toLocaleString()}`;
    document.getElementById("cart-total").textContent = `₦${subtotal.toLocaleString()}`;
  }

  function updateQuantity(index, change) {
    const cart = getCart();
    if (!cart[index]) return;
    const newQty = cart[index].quantity + change;
    if (newQty < 1) return;
    cart[index].quantity = newQty;
    saveCart(cart);
  }

  function removeItem(index) {
    const cart = getCart();
    if (!cart[index]) return;
    cart.splice(index, 1);
    saveCart(cart);
    showToast("Item removed");
  }

  // Event delegation — one listener handles all rows, including ones
  // re-rendered after quantity/remove actions.
  itemsContainer.addEventListener("click", (e) => {
    const row = e.target.closest("[data-index]");
    if (!row) return;
    const index = parseInt(row.dataset.index, 10);

    if (e.target.closest(".qty-increment")) {
      updateQuantity(index, 1);
    } else if (e.target.closest(".qty-decrement")) {
      updateQuantity(index, -1);
    } else if (e.target.closest(".remove-item")) {
      removeItem(index);
    }
  });

  renderCart();
});