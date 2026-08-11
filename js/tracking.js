/* ============================================================
   VERTEX SHOP — ORDER TRACKING LOGIC (js/tracking.js)
   Handles fetching and displaying customer order history.

   Requires: js/config.js, js/auth.js
   ============================================================ */

document.addEventListener("DOMContentLoaded", async () => {
  const container = document.getElementById("order-tracking-container");
  if (!container) return;

  // --- Helper Functions ---
  const formatNaira = (amount) => "₦" + (amount || 0).toLocaleString("en-NG");
  const formatDate = (isoString) => {
    if (!isoString) return "N/A";
    return new Date(isoString).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  // --- Check Authentication ---
  const user = await VertexAuth.getSessionUser();

  if (!user) {
    container.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        <h2>Sign In to View Orders</h2>
        <p>Please log in to your account to see your order history and track your purchases.</p>
        <a href="login.html" class="btn btn-primary" style="margin-top: 1rem;">Go to Login</a>
      </div>`;
    return;
  }

  // --- Fetch Orders from Supabase ---
  async function fetchOrders() {
    try {
      // RLS ensures this only returns orders for the logged-in user.
      // We also fetch the related order_items for each order.
      const { data, error } = await supabaseClient
        .from("orders")
        .select(`
          *,
          order_items (
            product_name,
            quantity,
            unit_price
          )
        `)
        .order("created_at", { ascending: false });

      if (error) throw error;
      return data;
    } catch (err) {
      console.error("Error fetching orders:", err);
      container.innerHTML = `
        <div class="empty-state">
          <h2>Could Not Load Orders</h2>
          <p>There was a problem fetching your order history. Please check your connection and try again.</p>
        </div>`;
      return null;
    }
  }

  const orders = await fetchOrders();

  if (orders === null) return; // Error already displayed

  if (orders.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
        <h2>No Orders Yet</h2>
        <p>You haven't placed any orders. Let's change that!</p>
        <a href="shop.html" class="btn btn-primary" style="margin-top: 1rem;">Start Shopping</a>
      </div>`;
    return;
  }

  // --- Render Orders ---
  container.innerHTML = orders.map(orderCardTemplate).join("");

  // Add event listeners for toggling details
  container.querySelectorAll(".order-card-header").forEach((header) => {
    header.addEventListener("click", () => {
      const card = header.closest(".order-card");
      card.classList.toggle("is-open");
    });
  });
});

// --- Templates ---

function orderCardTemplate(order) {
  const isCancelled = order.status === "cancelled";
  const statusClass = isCancelled ? "status-cancelled" : "";

  return `
    <div class="order-card ${statusClass}">
      <div class="order-card-header">
        <div class="order-card-summary">
          <h3>Order #${order.order_number}</h3>
          <p>${new Date(order.created_at).toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
          })}</p>
        </div>
        <div class="order-card-meta">
          <span class="order-status-badge status-${order.status}">${order.status.replace("_", " ")}</span>
          <span class="order-card-total">${formatNaira(order.total_amount)}</span>
          <svg class="order-card-chevron" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>
        </div>
      </div>
      <div class="order-card-details">
        ${orderDetailsTemplate(order)}
      </div>
    </div>
  `;
}

function orderDetailsTemplate(order) {
  const items = order.order_items || [];
  return `
    <div class="order-details-grid">
      <div class="order-items-summary">
        <h4>Items</h4>
        ${items
          .map(
            (item) => `
          <div class="order-summary-item">
            <span>${item.product_name} &times; ${item.quantity}</span>
            <span>${formatNaira(item.unit_price * item.quantity)}</span>
          </div>`
          )
          .join("")}
        <div class="order-summary-item">
          <span>Delivery Fee</span>
          <span>${formatNaira(order.delivery_fee)}</span>
        </div>
        <div class="order-summary-item total">
          <span>Total</span>
          <span>${formatNaira(order.total_amount)}</span>
        </div>
      </div>
      <div class="order-status-tracker">
        <h4>Status</h4>
        ${statusTrackerTemplate(order.status)}
      </div>
    </div>
  `;
}

function statusTrackerTemplate(currentStatus) {
  // These statuses MUST match the values in the database and admin dashboard.
  const ALL_STATUSES = [
    "pending",
    "confirmed",
    "preparing",
    "ready",
    "out_for_delivery",
    "delivered",
  ];

  const STATUS_LABELS = {
    pending: "Order Placed",
    confirmed: "Order Confirmed",
    preparing: "Preparing",
    ready: "Ready for Pickup/Delivery",
    out_for_delivery: "Out for Delivery",
    delivered: "Delivered",
    cancelled: "Cancelled",
  };

  if (currentStatus === "cancelled") {
    return `
      <div class="status-timeline">
        <div class="timeline-step is-cancelled">
          <div class="timeline-marker"></div>
          <div class="timeline-label">
            <strong>${STATUS_LABELS.cancelled}</strong>
            <p>This order has been cancelled.</p>
          </div>
        </div>
      </div>
    `;
  }

  const currentIndex = ALL_STATUSES.indexOf(currentStatus);

  let timelineHtml = '<div class="status-timeline">';

  ALL_STATUSES.forEach((status, index) => {
    const isCompleted = index < currentIndex;
    const isActive = index === currentIndex;
    const isFuture = index > currentIndex;

    let stepClass = "timeline-step";
    if (isActive) stepClass += " is-active";
    if (isCompleted) stepClass += " is-completed";

    timelineHtml += `
      <div class="${stepClass}">
        <div class="timeline-marker"></div>
        <div class="timeline-label">
          <strong>${STATUS_LABELS[status]}</strong>
          ${
            isActive
              ? `<p>${getFriendlyStatusMessage(status)}</p>`
              : ""
          }
        </div>
      </div>
    `;
  });

  timelineHtml += "</div>";
  return timelineHtml;
}

function getFriendlyStatusMessage(status) {
    const messages = {
        pending: "We've received your order and are verifying the details.",
        confirmed: "Your order is confirmed. We'll start preparing it soon.",
        preparing: "Our kitchen is now preparing your delicious food.",
        ready: "Your order is ready and waiting for you or the delivery rider.",
        out_for_delivery: "Your order is on its way to you. Enjoy!",
        delivered: "Your order has been delivered. Thank you for choosing us!",
    };
    return messages[status] || "Your order is being processed.";
}

function formatNaira(amount) {
  return "₦" + (amount || 0).toLocaleString("en-NG", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}