# Vertex Shop — Python Admin Dashboard

A complete **Python desktop admin dashboard** for the Vertex Shop restaurant
ordering platform. Built with **CustomTkinter**, it lets the shop administrator
manage products, categories, orders and customers with a modern, professional
interface — entirely in Python (no HTML/CSS/JS/Flutter/React/Electron).

> **Stage status:** Local demo build with SQLite persistence. Supabase will be
> integrated later as the shared backend between this dashboard and the
> Vertex Shop HTML/CSS/JS public website.

---

## Features

- **Dashboard** — summary cards (Total Products, Total Orders, Pending,
  Completed, Today's Sales) + recent orders.
- **Products** — list/table with image, name, category, price, availability,
  date added; **Add**, **Edit**, **Delete** (with confirmation dialog), and
  image selection via a file picker.
- **Product Availability** — mark products Available / Unavailable.
- **Categories** — add, edit, delete categories.
- **Orders** — professional table with Order No, Customer, Phone, Items, Total,
  Type (Delivery/Pickup), Date/Time, Status.
- **Order workflow** — `Pending → Confirmed → Preparing → Ready →
  Out for Delivery → Delivered / Cancelled`, updated via a dropdown.
- **Order details** — full view with customer info, items, delivery/pickup info,
  and status update.
- **Delivery vs Pickup** — clearly shows the selected option and its details.
- **Customers** — name, phone, email, order count, total spent, last order,
  plus order history on selection.
- **Search & Filtering** — search products, orders (by order no/customer/phone),
  categories, customers; filter orders by status.
- **Notifications** — a notification panel that simulates incoming new orders
  (later driven by Supabase Realtime).
- **SQLite persistence** — data survives restarts.

---

## Project Structure

```
vertex-shop-dashboard/
├── main.py                     # App entry point, sidebar, navigation
├── requirements.txt
├── config/settings.py          # Constants, paths, Supabase env placeholders
├── assets/logo.png             # Replace with the real Vertex Shop logo
├── database/database.py        # SQLite repository (swap for Supabase later)
├── models/
│   ├── product.py
│   ├── order.py
│   └── customer.py
├── views/
│   ├── dashboard.py
│   ├── products.py
│   ├── add_product.py
│   ├── orders.py
│   ├── customers.py
│   ├── categories.py
│   ├── settings.py
│   ├── notifications.py
│   └── widgets.py              # Shared UI components
└── utils/
    ├── validators.py
    └── helpers.py
```

---

## Installing Dependencies

Requires **Python 3.9+** on Windows.

```bash
cd vertex-shop-dashboard
pip install -r requirements.txt
```

This installs:
- `customtkinter` — the modern GUI framework
- `pillow` — for image handling

> On first run, the app creates the SQLite database (`data/vertex_shop.db`)
> and seeds it with realistic demo products, categories, customers and orders.

---

## Running the Application

```bash
cd vertex-shop-dashboard
python main.py
```

---

## Adding Your Logo

Replace `assets/logo.png` with the actual Vertex Shop logo. The dashboard
currently shows a "VS" badge placeholder in the sidebar.

---

## Future Supabase Architecture

The final setup will be:

```
                 SUPABASE
        ┌──────────────────────┐
        │ PostgreSQL Database  │
        │ Storage              │
        │ Realtime             │
        │ Authentication       │
        └──────────┬───────────┘
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
┌─────────────────┐   ┌─────────────────┐
│ Vertex Shop     │   │ Python Admin    │
│ Public Website  │   │ Dashboard       │
│ (HTML/CSS/JS)   │   │ (CustomTkinter) │
└─────────────────┘   └─────────────────┘
```

### How the swap happens

The **only** module that talks to storage is `database/database.py`. It exposes
a repository (`Database`) with methods like `get_products`, `add_product`,
`get_orders`, `update_order_status`, `get_customers`, etc.

To integrate Supabase:

1. Implement the same methods against Supabase (PostgreSQL for products/orders/
   customers, Storage for product images, Realtime for order notifications).
2. Swap the `db = Database()` instance in `database/database.py` for the
   Supabase-backed repository.
3. **No UI code needs to change** — the views consume the repository methods.

### Security

- **No Supabase secret/service-role keys are hard-coded** anywhere.
- When Supabase is connected, credentials are read from **environment variables**
  (see `config/settings.py`):
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY` (never exposed to the public web app)
- The public web application must never receive the service-role key.

---

## Notes

- The UI is designed for **Windows laptops/desktops** (resizable desktop layout).
- Demo data is seeded only when the database is empty; your changes persist.
- The notification simulation can be toggled in `config/settings.py`
  (`SIMULATE_NEW_ORDERS`).
