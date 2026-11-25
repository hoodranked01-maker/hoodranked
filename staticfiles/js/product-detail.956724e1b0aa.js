// HOODRANKED product detail page.
document.addEventListener("DOMContentLoaded", () => {
  const product = window.HOODRANKED_PRODUCT || {};

  if (product.id) {
        trackEvent('view_item', {
            currency: 'NGN',
            value: product.basePrice,
            items: [{
                item_id: product.id,
                item_name: product.name,
                item_category: product.category || 'other',
                price: product.basePrice,
                quantity: 1
            }]
        });
    }

  // --- Size guide accordion ---
  const guideToggle = document.getElementById("guide-toggle");
  const guideContent = document.getElementById("size-guide-content");
  const guideIcon = document.getElementById("guide-icon");
  guideToggle?.addEventListener("click", () => {
    guideContent.classList.toggle("hidden");
    guideIcon.textContent = guideContent.classList.contains("hidden") ? "expand_more" : "expand_less";
  });

  // --- Thumbnail gallery ---
  document.querySelectorAll("[data-full]").forEach((thumb) => {
    thumb.addEventListener("click", function () {
      document.getElementById("mainImage").src = this.dataset.full;
      document.querySelectorAll(".thumbnail").forEach((t) => t.classList.remove("active"));
      this.classList.add("active");
    });
  });

  // --- Quantity stepper ---
  const qtyInput = document.getElementById("quantity");
  document.getElementById("qty-decrement")?.addEventListener("click", () => {
    qtyInput.value = Math.max(1, parseInt(qtyInput.value || "1", 10) - 1);
  });
  document.getElementById("qty-increment")?.addEventListener("click", () => {
    qtyInput.value = Math.min(10, parseInt(qtyInput.value || "1", 10) + 1);
  });

  // --- Cart helpers (shared localStorage cart used across the site) ---
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
  }
  function showToast(msg = "Added to cart!") {
    const toast = document.getElementById("cart-toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2500);
  }

  // --- Size selection + add to cart ---
  const addToCartBtn = document.getElementById("add-to-cart-btn");
  let selectedVariant = null;

  document.querySelectorAll(".size-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      // 1. Reset ALL buttons back to the default HTML state
      document.querySelectorAll(".size-btn").forEach((b) => {
        b.classList.remove("bg-stark-white", "text-pitch-black");
        b.classList.add("text-stark-white");
      });

      // 2. Apply active styles to the clicked button
      this.classList.remove("text-stark-white");
      this.classList.add("bg-stark-white", "text-pitch-black");

      // 3. Save selected data
      selectedVariant = {
        id: this.dataset.variantId,
        size: this.dataset.size,
        addPrice: parseFloat(this.dataset.addPrice || "0"),
        stock: parseInt(this.dataset.stock, 10),
      };
      
      if (addToCartBtn) addToCartBtn.disabled = false;
    });
  });


  addToCartBtn?.addEventListener("click", () => {
    if (!selectedVariant) {
        showToast("Please select a size first");
        return;
    }

    const quantity = parseInt(qtyInput.value, 10) || 1;
    const finalPrice = product.basePrice + selectedVariant.addPrice;

    let cart = getCart();
    const idx = cart.findIndex((i) => i.variant_id === selectedVariant.id);

    if (idx !== -1) {
        const newQty = cart[idx].quantity + quantity;
        if (newQty > selectedVariant.stock) {
            showToast(`Only ${selectedVariant.stock} left!`);
            return;
        }
        cart[idx].quantity = newQty;
        showToast(`Cart updated (${newQty})`);
    } else {
        if (quantity > selectedVariant.stock) {
            showToast(`Only ${selectedVariant.stock} left!`);
            return;
        }
        cart.push({
            variant_id: selectedVariant.id,
            product_id: product.id,
            name: product.name,
            size: selectedVariant.size,
            price: finalPrice,
            quantity: quantity,
            image: product.image,
            slug: product.slug,
        });
        showToast();
    }

    saveCart(cart);

    // === GA4 Event Tracking ===
    trackEvent('add_to_cart', {
        currency: 'NGN',
        value: finalPrice * quantity,
        items: [{
            item_id: product.id,
            item_name: product.name,
            item_variant: selectedVariant.size,
            price: finalPrice,
            quantity: quantity
        }]
    });
});
});