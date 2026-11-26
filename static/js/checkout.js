// HOODRANKED checkout page.
document.addEventListener("DOMContentLoaded", () => {
  const SERVICE_FEE = 2000;
  let selectedRate = null;
  let pendingFormattedAddress = null;
  let rateFetchTimeout = null;
  let lastFetchedAddress = "";

  function getCart() {
    const raw = localStorage.getItem("hoodranked_cart");
    try {
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  // Coupon is set by the inline script in checkout.html (window.HR_COUPON).
  // Display only: the server recalculates every amount before charging.
  function getDiscount(subtotal) {
    const c = window.HR_COUPON;
    if (c && c.kind === "percent") {
      return Math.round((subtotal * c.percent) / 100);
    }
    return 0;
  }

  function updateTotals() {
    const cart = getCart();
    let subtotal = 0;
    cart.forEach((item) => {
      subtotal += item.price * item.quantity;
    });

    const coupon = window.HR_COUPON;
    const freeShipping = !!(coupon && coupon.kind === "free_delivery");
    const shipping = freeShipping
      ? 0
      : selectedRate
        ? selectedRate.shipping_fee
        : 0;
    const discount = getDiscount(subtotal);
    const total = subtotal - discount + SERVICE_FEE + shipping;

    document.getElementById("order-subtotal").textContent =
      `₦${subtotal.toLocaleString()}`;
    document.getElementById("service-fee").textContent =
      `₦${SERVICE_FEE.toLocaleString()}`;
    document.getElementById("shipping-fee").textContent =
      freeShipping && selectedRate
        ? "FREE"
        : shipping > 0
          ? `₦${shipping.toLocaleString()}`
          : "—";

    const row = document.getElementById("discount-row");
    if (row) {
      row.classList.toggle("hidden", discount <= 0);
      row.classList.toggle("flex", discount > 0);
      const amount = document.getElementById("discount-amount");
      if (amount) amount.textContent = `−₦${discount.toLocaleString()}`;
    }

    document.getElementById("order-total").textContent =
      `₦${total.toLocaleString()}`;
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

    placeOrderBtn.disabled = !selectedRate;

    cart.forEach((item) => {
      const itemTotal = item.price * item.quantity;
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

    updateTotals();
  }

  // Re-run totals whenever a coupon is applied, changed or cleared
  document.addEventListener("coupon-changed", updateTotals);

  function renderShippingOptions(couriers, requestToken, receiverAddressCode) {
    const container = document.getElementById("shipping-options");
    if (!container) return;

    container.innerHTML = `
      <h3 class="font-display text-headline-md text-stark-white mb-4">SHIPPING</h3>
      <div class="space-y-3" id="courier-list"></div>
    `;

    const list = document.getElementById("courier-list");

    if (!couriers || couriers.length === 0) {
      list.innerHTML = `<p class="text-outline text-sm">No shipping options available for this address.</p>`;
      selectedRate = null;
      renderOrderSummary();
      return;
    }

    couriers.forEach((c) => {
      const fee = Number(c.total || c.rate_card_amount || 0);
      const div = document.createElement("label");
      div.className =
        "flex items-start gap-3 p-4 border border-muted-steel cursor-pointer hover:border-stark-white transition-all";
      div.innerHTML = `
        <input type="radio" name="shipping_option" class="mt-1" value="${c.service_code}">
        <div class="flex-1">
          <div class="flex justify-between items-center">
            <span class="font-body font-bold text-stark-white">${c.courier_name || "Courier"}</span>
            <span class="font-mono text-stark-white">₦${fee.toLocaleString()}</span>
          </div>
          <p class="font-mono text-label-caps text-outline mt-1">${c.delivery_eta || c.delivery_eta_time || "Standard delivery"}</p>
        </div>
      `;

      div.querySelector("input").addEventListener("change", () => {
        selectedRate = {
          request_token: requestToken,
          service_code: c.service_code,
          courier_id: c.courier_id,
          shipping_fee: fee,
          receiver_address_code: receiverAddressCode,
          courier_name: c.courier_name || "",
        };
        renderOrderSummary();
      });

      list.appendChild(div);
    });
  }

  async function fetchShippingRates() {
    const full_name = document.getElementById("full_name").value.trim();
    const email = document.getElementById("email").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const address = document.getElementById("address").value.trim();
    const city = document.getElementById("city").value.trim();
    const state = document.getElementById("state").value.trim();
    const cart = getCart();

    if (
      !full_name ||
      !email ||
      !phone ||
      !address ||
      !city ||
      !state ||
      cart.length === 0
    ) {
      return;
    }

    const currentAddress = `${full_name}|${email}|${phone}|${address}|${city}|${state}`;
    if (currentAddress === lastFetchedAddress) {
      return;
    }

    lastFetchedAddress = currentAddress;

    const container = document.getElementById("shipping-options");
    container.innerHTML = `<p class="font-body text-outline py-4">Calculating shipping...</p>`;

    try {
      const response = await fetch("/orders/shipping-rates/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({
          full_name,
          email,
          phone,
          address,
          city,
          state,
          cart_items: cart,
        }),
      });

      const data = await response.json();

      if (!response.ok) throw new Error(data.error || "Could not fetch rates");

      pendingFormattedAddress =
        data.formatted_address || `${address}, ${city}, ${state}`;
      renderShippingOptions(
        data.couriers,
        data.request_token,
        data.receiver_address_code,
      );
    } catch (err) {
      console.error(err);
      container.innerHTML = `<p class="text-red-400 text-sm py-2">${err.message}</p>`;
      selectedRate = null;
      pendingFormattedAddress = null;
      lastFetchedAddress = "";
      renderOrderSummary();
    }
  }

  function scheduleRateFetch() {
    clearTimeout(rateFetchTimeout);
    rateFetchTimeout = setTimeout(fetchShippingRates, 600);
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
    document.getElementById("cheeky-popup")?.remove();
    const modal = document.createElement("div");
    modal.id = "cheeky-popup";
    modal.innerHTML = `
      <div class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/80 p-4">
        <div class="bg-pitch-black border border-muted-steel p-8 md:p-10 text-center max-w-sm w-full">
          <h2 class="font-display text-headline-md text-stark-white mb-4">Ah cheeky boy!</h2>
          <p class="font-body text-body-md text-on-surface-variant mb-8">Nice try. Prices are verified on the server.</p>
          <button id="cheeky-close-btn" class="font-body font-bold bg-stark-white text-pitch-black px-8 py-4 uppercase tracking-widest hover:bg-on-surface-variant transition-all">Okay</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    document
      .getElementById("cheeky-close-btn")
      .addEventListener("click", () => modal.remove());
  }

  function showAddressConfirmModal(formattedAddress, onConfirm) {
    document.getElementById("address-confirm-modal")?.remove();

    const modal = document.createElement("div");
    modal.id = "address-confirm-modal";
    modal.innerHTML = `
      <div class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/80 p-4">
        <div class="bg-pitch-black border border-muted-steel p-8 md:p-10 max-w-md w-full">
          <h2 class="font-display text-headline-md text-stark-white mb-4">Confirm Delivery Address</h2>
          <p class="font-body text-body-md text-on-surface-variant mb-6">
            Shipbubble will deliver to this address:
          </p>
          <div class="bg-surface-gray border border-muted-steel p-4 mb-8">
            <p class="font-body text-stark-white">${formattedAddress}</p>
          </div>
          <div class="flex gap-4">
            <button id="address-cancel-btn"
              class="flex-1 font-body font-bold border border-muted-steel text-stark-white py-4 uppercase tracking-widest hover:bg-muted-steel transition-all">
              Edit
            </button>
            <button id="address-confirm-btn"
              class="flex-1 font-body font-bold bg-stark-white text-pitch-black py-4 uppercase tracking-widest hover:bg-on-surface-variant transition-all">
              Confirm & Pay
            </button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    document
      .getElementById("address-cancel-btn")
      .addEventListener("click", () => modal.remove());
    document
      .getElementById("address-confirm-btn")
      .addEventListener("click", () => {
        modal.remove();
        onConfirm();
      });
  }

  // Debounced rate fetching
  ["address", "city", "state", "phone"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("blur", scheduleRateFetch);
      el.addEventListener("input", scheduleRateFetch);
    }
  });

  renderOrderSummary();

  const form = document.getElementById("checkout-form");
  const placeOrderBtn = document.getElementById("place-order-btn");

  form?.addEventListener("submit", (e) => {
    e.preventDefault();

    if (!selectedRate) {
      alert("Please select a shipping option.");
      return;
    }

    if (!pendingFormattedAddress) {
      alert("Please wait for shipping rates to finish loading.");
      return;
    }

    showAddressConfirmModal(pendingFormattedAddress, async () => {
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
        shipping_fee: selectedRate.shipping_fee,
        shipping_courier: selectedRate.courier_name,
        request_token: selectedRate.request_token,
        service_code: selectedRate.service_code,
        courier_id: selectedRate.courier_id,
        receiver_address_code: selectedRate.receiver_address_code,
        coupon_code: window.HR_COUPON ? window.HR_COUPON.code : "",
      };

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

        if (data.code === "PRICE_MISMATCH") {
          showCheekyPopup();
          return;
        }

        if (!response.ok) throw new Error(data.error || "Something went wrong");

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
});
