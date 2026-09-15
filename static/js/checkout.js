// HOODRANKED checkout page.
document.addEventListener("DOMContentLoaded", () => {
  const SERVICE_FEE = 2000;

  function getCart() {
    const raw = localStorage.getItem("hoodranked_cart");
    try {
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  function renderOrderSummary() {
    const cart = getCart();
    const container = document.getElementById("order-items");
    const placeOrderBtn = document.getElementById("place-order-btn");
    container.innerHTML = "";

    if (cart.length === 0) {
      container.innerHTML =
        '<p class="text-center font-body text-body-md text-outline py-8">Your cart is empty</p>';
      placeOrderBtn.disabled = true;
      return;
    }

    placeOrderBtn.disabled = false;

    let subtotal = 0;

    cart.forEach((item) => {
      const itemTotal = item.price * item.quantity;
      subtotal += itemTotal;

      const row = document.createElement("div");
      row.className =
        "flex gap-4 pb-6 border-b border-muted-steel last:border-b-0 last:pb-0";
      row.innerHTML = `
        <img src="${item.image}" alt="${item.name}" class="w-20 h-20 object-cover object-top bg-pitch-black flex-shrink-0">
        <div class="flex-1 min-w-0">
          <h4 class="font-body font-bold text-body-md text-stark-white truncate">${item.name}</h4>
          <p class="font-mono text-label-caps text-outline mt-1">SIZE ${item.size} &times; ${item.quantity}</p>
          <p class="font-mono text-label-caps text-stark-white mt-1">₦${itemTotal.toLocaleString()}</p>
        </div>
      `;
      container.appendChild(row);
    });

    const total = subtotal + SERVICE_FEE;
    document.getElementById("order-subtotal").textContent =
      `₦${subtotal.toLocaleString()}`;
    document.getElementById("service-fee").textContent =
      `₦${SERVICE_FEE.toLocaleString()}`;
    document.getElementById("order-total").textContent =
      `₦${total.toLocaleString()}`;
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function showCheekyPopup() {
    // Remove any existing popup
    document.getElementById("cheeky-popup")?.remove();

    const modal = document.createElement("div");
    modal.id = "cheeky-popup";
    modal.innerHTML = `
      <div class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/80 p-4">
        <div class="bg-pitch-black border border-muted-steel p-8 md:p-10 text-center max-w-sm w-full">
          <h2 class="font-display text-headline-md text-stark-white mb-4">Ah cheeky boy!</h2>
          <p class="font-body text-body-md text-on-surface-variant mb-8">
            Nice try. Prices are verified on the server.
          </p>
          <button id="cheeky-close-btn"
            class="font-body font-bold bg-stark-white text-pitch-black px-8 py-4 uppercase tracking-widest hover:bg-on-surface-variant transition-all">
            Okay
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    document
      .getElementById("cheeky-close-btn")
      .addEventListener("click", () => {
        modal.remove();
      });

    // Also close when clicking the dark overlay
    modal.addEventListener("click", (e) => {
      if (e.target === modal.firstElementChild) {
        modal.remove();
      }
    });
  }

  renderOrderSummary();

  const form = document.getElementById("checkout-form");
  const placeOrderBtn = document.getElementById("place-order-btn");

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();

    placeOrderBtn.disabled = true;
    const originalLabel = placeOrderBtn.textContent;
    placeOrderBtn.textContent = "Processing...";

    const formData = {
      full_name: document.getElementById("full_name").value,
      email: document.getElementById("email").value,
      phone: document.getElementById("phone").value,
      address: document.getElementById("address").value,
      city: document.getElementById("city").value,
      state: document.getElementById("state").value,
      additional_notes: document.getElementById("notes").value,
      service_fee: SERVICE_FEE,
      cart_items: getCart(),
    };

    if (
      !formData.full_name ||
      !formData.email ||
      !formData.phone ||
      !formData.address ||
      !formData.cart_items.length
    ) {
      alert(
        "Please fill all required fields and ensure your cart is not empty.",
      );
      placeOrderBtn.disabled = false;
      placeOrderBtn.textContent = originalLabel;
      return;
    }

    try {
      const response = await fetch(window.HOODRANKED_CHECKOUT_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      // Price mismatch → cheeky boy
      if (data.code === "PRICE_MISMATCH") {
        showCheekyPopup();
        return;
      }

      if (!response.ok) {
        throw new Error(data.error || "Something went wrong");
      }

      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      } else {
        alert("Payment initialization failed. Please try again.");
      }
    } catch (error) {
      alert(error.message);
      console.error(error);
    } finally {
      placeOrderBtn.disabled = false;
      placeOrderBtn.textContent = originalLabel;
    }
  });
});
