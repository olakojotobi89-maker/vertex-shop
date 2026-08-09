/* ============================================================
   VERTEX SHOP — SHOP LOGIC (js/shop.js)

   SUPABASE INTEGRATION:
   Products and categories are loaded from Supabase. Orders are inserted
   into the `orders` and `order_items` tables, which the Python admin
   dashboard reads from.

   THIS FILE EXPECTS js/config.js to have been loaded first so that the
   global `supabaseClient` is available.
   ============================================================ */

const DELIVERY_FEE = 800;
const CART_KEY = "vertexShop.cart";

/* ---------- Categories (loaded from Supabase) ---------- */
let CATEGORIES = [{ id: "all", label: "All" }];

/* ---------- Load categories from Supabase ---------- */
async function loadCategories() {
  if (!supabaseClient) return;
  try {
    const { data, error } = await supabaseClient
      .from("categories")
      .select("id, name")
      .order("name");
    if (error) throw error;
    if (data && data.length) {
      // category.id is a UUID; the product.category fields store the name.
      CATEGORIES = [
        { id: "all", label: "All" },
        ...data.map((c) => ({ id: c.name.toLowerCase().replace(/\s+/g, "-"), label: c.name, name: c.name })),
      ];
      // Keep a name->id map for matching products.
      CATEGORY_MAP = {};
      data.forEach((c) => { CATEGORY_MAP[c.name] = c.id; });
    }
  } catch (err) {
    console.error("Failed to load categories:", err);
  }
}

let CATEGORY_MAP = {};

/* ---------- Load products from Supabase ----------
   The products table references category_id (FK). We join categories to
   resolve the category name for display/filtering. We only show products
   where available = true. */
async function loadProducts() {
  if (!supabaseClient) return [];

  try {
    const { data, error } = await supabaseClient
      .from("products")
      .select("id, name, description, price, image_url, available, category_id, categories(name)");

    if (error) throw error;

    return (data || [])
      .filter((p) => p.available !== false)
      .map((p) => ({
        // The Python dashboard / Supabase use integer ids; keep string for
        // the cart keys, but also keep the raw id.
        id: String(p.id),
        rawId: p.id,
        name: p.name,
        description: p.description || "",
        price: Number(p.price || 0),
        category: p.categories?.name || "",
        image: p.image_url || "",
        tag: "",
        available: p.available !== false,
      }));
  } catch (err) {
    console.error("Failed to load products:", err);
    return [];
  }
}

/* ---------- Cart state (persisted to localStorage) ---------- */
const Cart = {
  items: JSON.parse(localStorage.getItem(CART_KEY) || "{}"), // { productId: quantity }

  save() {
    localStorage.setItem(CART_KEY, JSON.stringify(this.items));
  },
  add(productId) {
    this.items[productId] = (this.items[productId] || 0) + 1;
    this.save();
  },
  increase(productId) {
    this.items[productId] = (this.items[productId] || 0) + 1;
    this.save();
  },
  decrease(productId) {
    if (!this.items[productId]) return;
    this.items[productId] -= 1;
    if (this.items[productId] <= 0) delete this.items[productId];
    this.save();
  },
  remove(productId) {
    delete this.items[productId];
    this.save();
  },
  clear() {
    this.items = {};
    this.save();
  },
  totalCount() {
    return Object.values(this.items).reduce((sum, qty) => sum + qty, 0);
  },
  totalPrice(catalog) {
    return Object.entries(this.items).reduce((sum, [id, qty]) => {
      const product = catalog.find((p) => p.id === id);
      return product ? sum + product.price * qty : sum;
    }, 0);
  },
};

/* ---------- Formatting ---------- */
function formatNaira(amount) {
  return "₦" + amount.toLocaleString("en-NG");
}

/* ---------- App state ---------- */
let catalog = [];
let activeCategory = "all";
let searchTerm = "";

/* ============================================================
   RENDERING
   ============================================================ */

function renderCategories() {
  const list = document.getElementById("category-list");
  list.innerHTML = "";
  CATEGORIES.forEach((cat) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "category-chip" + (cat.id === activeCategory ? " is-active" : "");
    chip.textContent = cat.label;
    chip.setAttribute("role", "tab");
    chip.setAttribute("aria-selected", cat.id === activeCategory ? "true" : "false");
    chip.addEventListener("click", () => {
      activeCategory = cat.id;
      renderCategories();
      renderProducts();
    });
    list.appendChild(chip);
  });
}

function getFilteredProducts() {
  return catalog.filter((p) => {
    const catId = (p.category || "").toLowerCase().replace(/\s+/g, "-");
    const matchesCategory = activeCategory === "all" || catId === activeCategory;
    const matchesSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch && p.available !== false;
  });
}

function productCardTemplate(product) {
  const qty = Cart.items[product.id] || 0;

  const footerHTML = qty > 0
    ? `<div class="qty-stepper" data-id="${product.id}">
         <button type="button" class="qty-minus" aria-label="Decrease quantity">−</button>
         <span>${qty}</span>
         <button type="button" class="qty-plus" aria-label="Increase quantity">+</button>
       </div>`
    : `<button type="button" class="add-btn" data-id="${product.id}" aria-label="Add ${product.name} to cart">+</button>`;

  return `
    <article class="product-card" data-product-id="${product.id}">
      <div class="product-card-media">
        ${product.tag ? `<span class="product-card-tag">${product.tag}</span>` : ""}
        <img src="${product.image}" alt="${product.name}" loading="lazy">
      </div>
      <div class="product-card-body">
        <h3>${product.name}</h3>
        <p class="product-card-desc">${product.description}</p>
        <div class="product-card-footer">
          <span class="product-price">${formatNaira(product.price)}</span>
          ${footerHTML}
        </div>
      </div>
    </article>
  `;
}

function renderProducts() {
  const container = document.getElementById("products-container");
  const emptyState = document.getElementById("empty-state");
  const countLabel = document.getElementById("product-count");
  const filtered = getFilteredProducts();

  countLabel.textContent = `${filtered.length} item${filtered.length === 1 ? "" : "s"}`;

  if (filtered.length === 0) {
    container.innerHTML = "";
    emptyState.classList.remove("hidden");
    return;
  }
  emptyState.classList.add("hidden");
  container.innerHTML = filtered.map(productCardTemplate).join("");

  // Wire up add / stepper buttons for the cards just rendered.
  container.querySelectorAll(".add-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      Cart.add(btn.dataset.id);
      renderProducts();
      renderCart();
      showToast("Added to cart");
    });
  });
  container.querySelectorAll(".qty-stepper").forEach((stepper) => {
    const id = stepper.dataset.id;
    stepper.querySelector(".qty-plus").addEventListener("click", () => {
      Cart.increase(id);
      renderProducts();
      renderCart();
    });
    stepper.querySelector(".qty-minus").addEventListener("click", () => {
      Cart.decrease(id);
      renderProducts();
      renderCart();
    });
  });
}

/* ---------- Cart drawer rendering ---------- */
function cartLineTemplate(product, qty) {
  return `
    <div class="cart-line" data-id="${product.id}">
      <img class="cart-line-img" src="${product.image}" alt="${product.name}">
      <div class="cart-line-info">
        <h4>${product.name}</h4>
        <span class="cart-line-price">${formatNaira(product.price * qty)}</span>
        <div class="cart-line-actions">
          <div class="qty-stepper" data-id="${product.id}">
            <button type="button" class="qty-minus" aria-label="Decrease quantity">−</button>
            <span>${qty}</span>
            <button type="button" class="qty-plus" aria-label="Increase quantity">+</button>
          </div>
          <button type="button" class="cart-line-remove" data-id="${product.id}">Remove</button>
        </div>
      </div>
    </div>
  `;
}

function renderCart() {
  const badge = document.getElementById("cart-badge");
  const body = document.getElementById("cart-body");
  const subtotalEl = document.getElementById("cart-subtotal");
  const totalEl = document.getElementById("cart-total");
  const checkoutBtn = document.getElementById("checkout-btn");

  const count = Cart.totalCount();
  badge.textContent = count;
  badge.classList.toggle("hidden", count === 0);

  const entries = Object.entries(Cart.items)
    .map(([id, qty]) => [catalog.find((p) => p.id === id), qty])
    .filter(([product]) => Boolean(product));

  if (entries.length === 0) {
    body.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
        <p>Your cart is empty. Add something delicious!</p>
      </div>`;
    checkoutBtn.disabled = true;
    checkoutBtn.style.opacity = "0.5";
  } else {
    body.innerHTML = entries.map(([product, qty]) => cartLineTemplate(product, qty)).join("");
    checkoutBtn.disabled = false;
    checkoutBtn.style.opacity = "1";

    body.querySelectorAll(".qty-stepper").forEach((stepper) => {
      const id = stepper.dataset.id;
      stepper.querySelector(".qty-plus").addEventListener("click", () => {
        Cart.increase(id);
        renderCart();
        renderProducts();
      });
      stepper.querySelector(".qty-minus").addEventListener("click", () => {
        Cart.decrease(id);
        renderCart();
        renderProducts();
      });
    });
    body.querySelectorAll(".cart-line-remove").forEach((btn) => {
      btn.addEventListener("click", () => {
        Cart.remove(btn.dataset.id);
        renderCart();
        renderProducts();
      });
    });
  }

  const subtotal = Cart.totalPrice(catalog);
  subtotalEl.textContent = formatNaira(subtotal);
  totalEl.textContent = formatNaira(subtotal); // delivery fee added at checkout step
}

/* ============================================================
   CART DRAWER OPEN / CLOSE
   ============================================================ */
const cartDrawer = document.getElementById("cart-drawer");
const cartOverlay = document.getElementById("cart-overlay");

function openCart() { // Reverted to non-async as no await is needed here.
  renderCart();
  cartDrawer.classList.add("is-open");
  cartOverlay.classList.add("is-open");
}
function closeCart() {
  cartDrawer.classList.remove("is-open"); // Corrected typo
  cartOverlay.classList.remove("is-open"); // Corrected typo
}

document.getElementById("cart-toggle").addEventListener("click", openCart);
document.getElementById("mobile-cart-btn").addEventListener("click", (e) => {
  e.preventDefault();
  openCart();
});
document.getElementById("cart-close").addEventListener("click", closeCart);
cartOverlay.addEventListener("click", closeCart);

/* ============================================================
   SEARCH
   ============================================================ */
document.getElementById("search-toggle").addEventListener("click", () => {
  const bar = document.getElementById("search-bar");
  bar.classList.toggle("hidden");
  if (!bar.classList.contains("hidden")) {
    document.getElementById("product-search").focus();
  }
});
document.getElementById("product-search").addEventListener("input", (e) => {
  searchTerm = e.target.value;
  renderProducts();
});

/* ============================================================
   CHECKOUT MODAL
   ============================================================ */
const checkoutOverlay = document.getElementById("checkout-overlay");
const deliveryFields = document.getElementById("delivery-fields");
const pickupFields = document.getElementById("pickup-fields");
const optionDelivery = document.getElementById("option-delivery");
const optionPickup = document.getElementById("option-pickup");
const deliveryMethodInput = document.getElementById("delivery-method");

function setDeliveryMethod(method) {
  deliveryMethodInput.value = method;
  const isDelivery = method === "delivery";
  optionDelivery.classList.toggle("is-selected", isDelivery);
  optionDelivery.setAttribute("aria-checked", String(isDelivery));
  optionPickup.classList.toggle("is-selected", !isDelivery);
  optionPickup.setAttribute("aria-checked", String(!isDelivery));
  deliveryFields.classList.toggle("hidden", !isDelivery);
  pickupFields.classList.toggle("hidden", isDelivery);

  // Delivery address is only required when "Delivery" is selected.
  document.getElementById("delivery-address").required = isDelivery;

  renderCheckoutSummary();
}

[optionDelivery, optionPickup].forEach((el) => {
  el.addEventListener("click", () => setDeliveryMethod(el.dataset.value));
  el.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setDeliveryMethod(el.dataset.value);
    }
  });
});

function renderCheckoutSummary() {
  const itemsBox = document.getElementById("checkout-items");
  const totalEl = document.getElementById("checkout-total");

  const entries = Object.entries(Cart.items)
    .map(([id, qty]) => [catalog.find((p) => p.id === id), qty])
    .filter(([product]) => Boolean(product));

  const subtotal = Cart.totalPrice(catalog);
  const isDelivery = deliveryMethodInput.value === "delivery";
  const fee = isDelivery ? DELIVERY_FEE : 0;
  const total = subtotal + fee;

  itemsBox.innerHTML =
    entries.map(([p, qty]) =>
      `<div class="order-summary-item"><span>${p.name} × ${qty}</span><span>${formatNaira(p.price * qty)}</span></div>`
    ).join("") +
    `<div class="order-summary-item"><span>${isDelivery ? "Delivery fee" : "Pickup fee"}</span><span>${isDelivery ? formatNaira(fee) : "Free"}</span></div>`;

  totalEl.textContent = formatNaira(total);
}

async function openCheckout() { // Made async to await Supabase session check
  if (Cart.totalCount() === 0) return;

  // Verify authenticated Supabase session
  const { data: { session } } = await supabaseClient.auth.getSession();

  if (!session) {
    showToast("Please sign in before placing an order.");
    // Redirect to login page, potentially with a redirect_to parameter
    window.location.href = "login.html?redirect_to=" + encodeURIComponent(window.location.href);
    return;
  }

  // If session exists, proceed with opening checkout
  closeCart(); // Close the cart drawer
  renderCheckoutSummary(); // Update the summary in the checkout modal
  checkoutOverlay.classList.add("is-open"); // Open the checkout modal
}
function closeCheckout() {
  checkoutOverlay.classList.remove("is-open");
}

document.getElementById("checkout-btn").addEventListener("click", openCheckout);
document.getElementById("checkout-close").addEventListener("click", closeCheckout);
checkoutOverlay.addEventListener("click", (e) => {
  if (e.target === checkoutOverlay) closeCheckout();
});

/* ---------- Place order ---------- */
document.getElementById("checkout-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  // Ensure Supabase client is available
  if (!supabaseClient) {
    showToast("Supabase client not initialized. Cannot place order.");
    console.error("Supabase client is null.");
    return;
  }

  const formData = new FormData(form);
  const isDelivery = formData.get("deliveryMethod") === "delivery";
  const subtotal = Cart.totalPrice(catalog);
  const deliveryFee = isDelivery ? DELIVERY_FEE : 0;
  const total = subtotal + deliveryFee;

  // Get authenticated user session
  const { data: { session } } = await supabaseClient.auth.getSession();
  if (!session || !session.user) {
    showToast("Authentication error: You must be signed in to place an order. Redirecting to login.");
    window.location.href = "login.html?redirect_to=" + encodeURIComponent(window.location.href);
    return;
  }
  const authUserId = session.user.id;

  let customerProfileId = null;
  // Fetch the customer's profile ID from the 'customers' table
  const { data: customerProfile, error: profileError } = await supabaseClient
    .from("customers")
    .select("id")
    .eq("auth_user_id", authUserId)
    .single();

  if (profileError && profileError.code !== 'PGRST116') { // PGRST116 is "no rows found"
    console.error("Error fetching customer profile ID:", profileError);
    showToast("Error fetching your customer profile. Please try again.");
    return;
  } else if (customerProfile) {
    customerProfileId = customerProfile.id;
  }

  // Defensive check: If customerProfileId is still null, it means no profile exists for the auth user.
  if (!customerProfileId) {
    showToast("Your customer profile is incomplete. Please ensure your account details are fully registered.");
    console.error("Customer profile not found for auth user ID:", authUserId);
    return; // Prevent order placement
  }

  // --- DEBUG LOGS ---
  console.log("[ORDER DEBUG] Auth user ID:", authUserId); // Use the already fetched authUserId
  console.log("[ORDER DEBUG] customerProfileId (fetched from public.customers):", customerProfileId);

  // Build order_items payload (product_id, quantity, product_name, unit_price, subtotal).
  const items = Object.entries(Cart.items).map(([id, qty]) => {
    const product = catalog.find((p) => p.id === id);
    return {
      product_id: product.rawId ?? id,
      quantity: qty,
      product_name: product.name,
      unit_price: product.price,
      subtotal: product.price * qty,
    };
  });

// Unique human-friendly order reference (also stored in public.orders so the
  // Python dashboard can display it).
  let orderRef = "VS-" + Date.now().toString().slice(-8);

  const orderPayload = {
    order_number: orderRef,
    customer_id: customerProfileId, // Directly use the fetched customerProfileId
    customer_name: formData.get("customerName"),
    customer_phone: formData.get("customerPhone"),
    order_type: isDelivery ? "delivery" : "pickup",
    delivery_address: isDelivery ? (formData.get("deliveryAddress") || null) : null, // Keep this line as is
    delivery_instructions: isDelivery ? (formData.get("deliveryInstructions") || null) : null,
    pickup_location: isDelivery ? null : (formData.get("pickupLocation") || null),
    subtotal,
    delivery_fee: isDelivery ? DELIVERY_FEE : 0,
    total_amount: total,
    status: "pending",
  };
  console.log("[ORDER DEBUG] STATUS BEING SENT:", orderPayload.status);
  console.log("[ORDER DEBUG] ORDER TYPE BEING SENT:", orderPayload.order_type);
  console.log("[ORDER DEBUG] Final orderPayload before INSERT:", orderPayload);

  if (supabaseClient) {
    try {
      // Insert the order header first.
      console.log("[ORDER DEBUG] Attempting to insert order...");
      const { data: orderRow, error: orderError } = await supabaseClient
        .from("orders")
        .insert([orderPayload])
        .select()
        .single();
      console.log("[ORDER DEBUG] Order INSERT result:", { orderRow, orderError });
      if (orderError) throw orderError;

      orderRef = orderRow.order_number || orderRef;

      // Insert the order_items linked to the new order.
      const itemsPayload = items.map((it) => ({ ...it, order_id: orderRow.id }));
      const { error: itemsError } = await supabaseClient
        .from("order_items")
        .insert(itemsPayload);
      console.log("[ORDER DEBUG] Order Items INSERT result:", { itemsError });
      if (itemsError) throw itemsError;
    } catch (err) {
      const msg = err.message || "Something went wrong placing your order.";
      showToast("Order failed: " + msg);
      console.error("Order insert error:", err);
      return;
    }
  } else {
    // Fallback: keep a local record if Supabase isn't configured.
    const orders = JSON.parse(localStorage.getItem("vertexShop.orders") || "[]");
    orders.push({ ...orderPayload, order_number: orderRef, items });
    localStorage.setItem("vertexShop.orders", JSON.stringify(orders));
  }

  Cart.clear();
  renderProducts();
  renderCart();
  closeCheckout();
  form.reset();
  setDeliveryMethod("delivery");
  showToast(`Order placed! Reference ${orderRef}`);
});

/* ============================================================
   TOAST
   ============================================================ */
let toastTimer = null;
function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("is-open");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("is-open"), 2400);
}

/* ============================================================
   INIT
   ============================================================ */
(async function init() {
  await loadCategories();
  catalog = await loadProducts();
  renderCategories();
  renderProducts();
  renderCart();
})();
