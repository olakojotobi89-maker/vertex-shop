"""
Vertex Shop Admin Dashboard - Data layer.

CURRENT: SQLite persistence (local demo data).
FUTURE : Supabase (PostgreSQL + Storage + Realtime).

This module is the ONLY place that talks to storage. Views and models use
the repository methods below. When integrating Supabase, implement the same
methods (or a new Repository class) against Supabase and swap it here —
without touching the UI code.

SECURITY: No service-role keys here. Supabase credentials will come from
environment variables (see config/settings.py).
"""
import json
import sqlite3
from datetime import datetime, timedelta

import config.settings as settings
from models.product import Product
from models.order import Order, OrderItem
from models.customer import Customer


# ===========================================================================
# Schema
# ===========================================================================
SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT NOT NULL,
    price REAL NOT NULL DEFAULT 0,
    image TEXT DEFAULT '',
    available INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    customer_email TEXT DEFAULT '',
    delivery_method TEXT NOT NULL DEFAULT 'delivery',
    delivery_address TEXT DEFAULT '',
    delivery_instructions TEXT DEFAULT '',
    pickup_location TEXT DEFAULT '',
    subtotal REAL NOT NULL DEFAULT 0,
    delivery_fee REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Pending',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER DEFAULT 0,
    name TEXT NOT NULL,
    price REAL NOT NULL DEFAULT 0,
    quantity INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
);
"""


# ===========================================================================
# Repository
# ===========================================================================
class Database:
    """SQLite-backed repository. Swap this class for a Supabase one later."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or settings.DATABASE_PATH)
        self._init_db()

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        conn = self._connect()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            conn.close()
        self._seed_if_empty()

    def _row_to_dict(self, row) -> dict:
        return dict(row) if row is not None else {}

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------
    def get_categories(self) -> list:
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_category_names(self) -> list:
        return [c["name"] for c in self.get_categories()]

    def add_category(self, name: str) -> dict:
        conn = self._connect()
        try:
            cur = conn.execute(
                "INSERT INTO categories (name, created_at) VALUES (?, ?)",
                (name.strip(), datetime.now().isoformat()),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM categories WHERE id = ?", (cur.lastrowid,)
            ).fetchone()
            return dict(row)
        finally:
            conn.close()

    def update_category(self, cat_id: int, name: str):
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE categories SET name = ? WHERE id = ?", (name.strip(), cat_id)
            )
            conn.commit()
        finally:
            conn.close()

    def delete_category(self, cat_id: int):
        conn = self._connect()
        try:
            conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------
    def get_products(self, search: str = "", category: str = "") -> list:
        """Return products, optionally filtered by search text and category."""
        conn = self._connect()
        try:
            sql = "SELECT * FROM products WHERE 1=1"
            params = []
            if search:
                sql += " AND (name LIKE ? OR description LIKE ?)"
                like = f"%{search}%"
                params += [like, like]
            if category and category != "All":
                sql += " AND category = ?"
                params.append(category)
            sql += " ORDER BY created_at DESC, id DESC"
            rows = conn.execute(sql, params).fetchall()
            return [Product.from_row(dict(r)) for r in rows]
        finally:
            conn.close()

    def get_product(self, product_id: int):
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
            return Product.from_row(dict(row)) if row else None
        finally:
            conn.close()

    def add_product(
        self,
        name: str,
        description: str,
        category: str,
        price: float,
        image: str = "",
        available: bool = True,
    ) -> Product:
        conn = self._connect()
        try:
            cur = conn.execute(
                """INSERT INTO products
                   (name, description, category, price, image, available, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    name.strip(),
                    description.strip(),
                    category.strip(),
                    float(price),
                    image,
                    1 if available else 0,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM products WHERE id = ?", (cur.lastrowid,)
            ).fetchone()
            return Product.from_row(dict(row))
        finally:
            conn.close()

    def update_product(
        self,
        product_id: int,
        name: str,
        description: str,
        category: str,
        price: float,
        image: str = None,
        available: bool = True,
    ):
        conn = self._connect()
        try:
            # If image is None, keep the existing image.
            if image is None:
                conn.execute(
                    """UPDATE products SET name=?, description=?, category=?,
                       price=?, available=? WHERE id=?""",
                    (
                        name.strip(),
                        description.strip(),
                        category.strip(),
                        float(price),
                        1 if available else 0,
                        product_id,
                    ),
                )
            else:
                conn.execute(
                    """UPDATE products SET name=?, description=?, category=?,
                       price=?, image=?, available=? WHERE id=?""",
                    (
                        name.strip(),
                        description.strip(),
                        category.strip(),
                        float(price),
                        image,
                        1 if available else 0,
                        product_id,
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def delete_product(self, product_id: int):
        conn = self._connect()
        try:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
        finally:
            conn.close()

    def product_count(self) -> int:
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()
            return int(row["c"])
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    def _fetch_items(self, order_id: int) -> list:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
            ).fetchall()
            return [OrderItem.from_dict(dict(r)) for r in rows]
        finally:
            conn.close()

    def get_orders(self, search: str = "", status: str = "") -> list:
        """Return orders, optionally filtered by search text and status."""
        conn = self._connect()
        try:
            sql = "SELECT * FROM orders WHERE 1=1"
            params = []
            if search:
                sql += (
                    " AND (order_no LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)"
                )
                like = f"%{search}%"
                params += [like, like, like]
            if status and status != "All":
                sql += " AND status = ?"
                params.append(status)
            sql += " ORDER BY created_at DESC, id DESC"
            rows = conn.execute(sql, params).fetchall()
            orders = []
            for r in rows:
                d = dict(r)
                items = self._fetch_items(d["id"])
                orders.append(Order.from_row(d, items=items))
            return orders
        finally:
            conn.close()

    def get_order(self, order_id: int):
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM orders WHERE id = ?", (order_id,)
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            items = self._fetch_items(d["id"])
            return Order.from_row(d, items=items)
        finally:
            conn.close()

    def add_order(self, order: Order) -> Order:
        """Insert a new order (with its items)."""
        conn = self._connect()
        try:
            # Use a temporary unique order_no so the UNIQUE constraint never
            # trips; the real order_no is set right after insert below.
            temp_no = f"TMP-{datetime.now().timestamp():.0f}-{order.customer_phone or 'x'}"
            cur = conn.execute(
                """INSERT INTO orders
                   (order_no, customer_name, customer_phone, customer_email,
                    delivery_method, delivery_address, delivery_instructions,
                    pickup_location, subtotal, delivery_fee, total, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    temp_no,
                    order.customer_name,
                    order.customer_phone,
                    order.customer_email,
                    order.delivery_method,
                    order.delivery_address,
                    order.delivery_instructions,
                    order.pickup_location,
                    order.subtotal,
                    order.delivery_fee,
                    order.total,
                    order.status,
                    order.created_at,
                ),
            )
            order_id = cur.lastrowid
            # Generate a unique order number from the real row id.
            order_no = Order.generate_order_no(order_id)
            conn.execute(
                "UPDATE orders SET order_no = ? WHERE id = ?", (order_no, order_id)
            )
            for item in order.items:
                conn.execute(
                    """INSERT INTO order_items
                       (order_id, product_id, name, price, quantity)
                       VALUES (?, ?, ?, ?, ?)""",
                    (order_id, item.product_id, item.name, item.price, item.quantity),
                )
            conn.commit()
            return self.get_order(order_id)
        finally:
            conn.close()

    def update_order_status(self, order_id: int, status: str):
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
            )
            conn.commit()
        finally:
            conn.close()

    def order_count(self) -> int:
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) AS c FROM orders").fetchone()
            return int(row["c"])
        finally:
            conn.close()

    def orders_by_status(self, status: str) -> int:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM orders WHERE status = ?", (status,)
            ).fetchone()
            return int(row["c"])
        finally:
            conn.close()

    def orders_today(self) -> int:
        conn = self._connect()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM orders WHERE substr(created_at,1,10) = ?",
                (today,),
            ).fetchone()
            return int(row["c"])
        finally:
            conn.close()

    def sales_today(self) -> float:
        """Sum of totals for non-cancelled orders placed today."""
        conn = self._connect()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            row = conn.execute(
                """SELECT COALESCE(SUM(total),0) AS s FROM orders
                   WHERE substr(created_at,1,10) = ? AND status != 'Cancelled'""",
                (today,),
            ).fetchone()
            return float(row["s"])
        finally:
            conn.close()

    def recent_orders(self, limit: int = 5) -> list:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM orders ORDER BY created_at DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            orders = []
            for r in rows:
                d = dict(r)
                items = self._fetch_items(d["id"])
                orders.append(Order.from_row(d, items=items))
            return orders
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------
    def get_customers(self) -> list:
        """Aggregate customers from orders (grouped by phone/name)."""
        conn = self._connect()
        try:
            rows = conn.execute(
                """SELECT customer_name, customer_phone, customer_email,
                          COUNT(*) AS order_count,
                          COALESCE(SUM(CASE WHEN status != 'Cancelled' THEN total ELSE 0 END), 0) AS total_spent,
                          MAX(created_at) AS last_order_at
                   FROM orders
                   GROUP BY LOWER(COALESCE(NULLIF(customer_phone,''), customer_name))
                   ORDER BY total_spent DESC""",
            ).fetchall()
            customers = []
            for r in rows:
                d = dict(r)
                customers.append(
                    Customer(
                        name=d["customer_name"],
                        phone=d["customer_phone"],
                        email=d["customer_email"],
                        order_count=int(d["order_count"]),
                        total_spent=float(d["total_spent"]),
                        last_order_at=d["last_order_at"],
                    )
                )
            return customers
        finally:
            conn.close()

    def get_customer_orders(self, phone: str = "", name: str = "") -> list:
        """Return orders for a specific customer (matched by phone or name)."""
        conn = self._connect()
        try:
            sql = "SELECT * FROM orders WHERE 1=1"
            params = []
            if phone:
                sql += " AND customer_phone = ?"
                params.append(phone)
            if name:
                sql += " AND customer_name = ?"
                params.append(name)
            sql += " ORDER BY created_at DESC"
            rows = conn.execute(sql, params).fetchall()
            orders = []
            for r in rows:
                d = dict(r)
                items = self._fetch_items(d["id"])
                orders.append(Order.from_row(d, items=items))
            return orders
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Dashboard stats
    # ------------------------------------------------------------------
    def dashboard_stats(self) -> dict:
        return {
            "total_products": self.product_count(),
            "total_orders": self.order_count(),
            "pending_orders": self.orders_by_status("Pending"),
            "completed_orders": self.orders_by_status("Delivered"),
            "sales_today": self.sales_today(),
            "orders_today": self.orders_today(),
        }

    # ------------------------------------------------------------------
    # Seeding (demo data - only runs when the DB is empty)
    # ------------------------------------------------------------------
    def _seed_if_empty(self):
        conn = self._connect()
        try:
            count = conn.execute("SELECT COUNT(*) AS c FROM categories").fetchone()["c"]
            if count > 0:
                return
        finally:
            conn.close()
        self._seed_demo_data()

    def _seed_demo_data(self):
        now = datetime.now()

        # Categories
        categories = [
            "Meals", "Pastries", "Cakes", "Drinks", "Snacks", "Fast Food", "Desserts",
        ]
        for name in categories:
            self.add_category(name)

        # Seed products (matching the public web app's demo catalog)
        products = [
            ("Jollof Rice", "Smoky party-style jollof rice, slow-cooked with peppers and spices.", "Meals", 3500, True),
            ("Chicken & Chips", "Grilled chicken thigh with golden fries and house pepper sauce.", "Meals", 4800, True),
            ("Meat Pie", "Flaky pastry filled with seasoned minced beef, carrots and potato.", "Pastries", 1200, True),
            ("Shawarma", "Chicken shawarma wrap with garlic sauce, pickles and fresh veg.", "Fast Food", 3200, True),
            ("Chocolate Cake", "Rich, moist chocolate layer cake with dark chocolate ganache.", "Cakes", 6500, True),
            ("Puff Puff", "Sweet, fluffy fried dough balls — a classic Nigerian street favorite.", "Snacks", 1000, True),
            ("Fresh Juice", "Cold-pressed pineapple, ginger and watermelon juice blend.", "Drinks", 1800, True),
            ("Egg Roll", "Boiled egg wrapped in soft, lightly spiced dough and deep fried.", "Snacks", 900, True),
            ("Vanilla Cupcake", "Soft vanilla cupcake topped with buttercream frosting.", "Desserts", 1500, True),
            ("Samosa", "Crispy pastry triangles filled with spiced minced meat.", "Snacks", 800, True),
        ]
        for name, desc, cat, price, avail in products:
            self.add_product(name, desc, cat, price, "", avail)

        # Seed customers + orders
        demo_orders = [
            {
                "customer_name": "John Doe",
                "customer_phone": "08012345678",
                "customer_email": "john@example.com",
                "delivery_method": "delivery",
                "delivery_address": "12 Adeola Odeku St, Victoria Island, Lagos",
                "delivery_instructions": "Call on arrival, gate code 4451",
                "items": [("Jollof Rice", 3500, 2), ("Chicken & Chips", 4800, 1)],
                "status": "Pending",
                "created_at": now - timedelta(minutes=25),
            },
            {
                "customer_name": "Mary James",
                "customer_phone": "08098765432",
                "customer_email": "mary@example.com",
                "delivery_method": "delivery",
                "delivery_address": "4 Bola Street, Wuse II, Abuja",
                "delivery_instructions": "",
                "items": [("Chocolate Cake", 6500, 1), ("Fresh Juice", 1800, 2)],
                "status": "Preparing",
                "created_at": now - timedelta(minutes=90),
            },
            {
                "customer_name": "David Smith",
                "customer_phone": "08055556666",
                "customer_email": "",
                "delivery_method": "pickup",
                "pickup_location": "Vertex Shop - Wuse II Station",
                "items": [("Meat Pie", 1200, 2), ("Puff Puff", 1000, 1)],
                "status": "Delivered",
                "created_at": now - timedelta(hours=3),
            },
            {
                "customer_name": "Aisha Bello",
                "customer_phone": "08123456789",
                "customer_email": "aisha@example.com",
                "delivery_method": "delivery",
                "delivery_address": "22 Usman Street, Garki, Abuja",
                "delivery_instructions": "Leave with security guard",
                "items": [("Shawarma", 3200, 3)],
                "status": "Confirmed",
                "created_at": now - timedelta(hours=1, minutes=10),
            },
            {
                "customer_name": "Chinedu Okafor",
                "customer_phone": "07033445566",
                "customer_email": "",
                "delivery_method": "pickup",
                "pickup_location": "Vertex Shop - Jabi Station",
                "items": [("Egg Roll", 900, 4), ("Samosa", 800, 3)],
                "status": "Ready",
                "created_at": now - timedelta(hours=2),
            },
            {
                "customer_name": "Fatima Sani",
                "customer_phone": "09011223344",
                "customer_email": "fatima@example.com",
                "delivery_method": "delivery",
                "delivery_address": "8 Aminu Kano Cres, Wuse II, Abuja",
                "delivery_instructions": "",
                "items": [("Fresh Juice", 1800, 2), ("Vanilla Cupcake", 1500, 2)],
                "status": "Out for Delivery",
                "created_at": now - timedelta(hours=4),
            },
            {
                "customer_name": "Grace Adeyemi",
                "customer_phone": "08077889900",
                "customer_email": "grace@example.com",
                "delivery_method": "delivery",
                "delivery_address": "3 Admiralty Way, Lekki, Lagos",
                "delivery_instructions": "Ring bell twice",
                "items": [("Chicken & Chips", 4800, 2), ("Fresh Juice", 1800, 1)],
                "status": "Delivered",
                "created_at": now - timedelta(days=1, hours=2),
            },
            {
                "customer_name": "Ibrahim Musa",
                "customer_phone": "08112233445",
                "customer_email": "",
                "delivery_method": "delivery",
                "delivery_address": "15 Ahmadu Bello Way, Kaduna",
                "delivery_instructions": "",
                "items": [("Jollof Rice", 3500, 1), ("Samosa", 800, 2)],
                "status": "Cancelled",
                "created_at": now - timedelta(days=2, hours=5),
            },
        ]

        for od in demo_orders:
            items = [
                OrderItem(product_id=0, name=n, price=p, quantity=q)
                for n, p, q in od["items"]
            ]
            subtotal = sum(it.subtotal for it in items)
            is_delivery = od["delivery_method"] == "delivery"
            fee = settings.DELIVERY_FEE if is_delivery else 0
            order = Order(
                customer_name=od["customer_name"],
                customer_phone=od["customer_phone"],
                customer_email=od["customer_email"],
                delivery_method=od["delivery_method"],
                delivery_address=od.get("delivery_address", ""),
                delivery_instructions=od.get("delivery_instructions", ""),
                pickup_location=od.get("pickup_location", ""),
                items=items,
                subtotal=subtotal,
                delivery_fee=fee,
                total=subtotal + fee,
                status=od["status"],
                created_at=od["created_at"].isoformat(),
            )
            self.add_order(order)


# --------------------------------------------------------------------------
# Active data layer selection
# --------------------------------------------------------------------------
# Prefer Supabase when credentials are configured; otherwise fall back to
# the local SQLite database. Both expose the same interface, so views work
# unchanged regardless of which is active.
def _build_active_database():
    from .supabase_client import get_supabase_client
    from .supabase_repository import SupabaseDatabase

    client = get_supabase_client()
    if client is not None:
        try:
            sb = SupabaseDatabase()
            if sb.available:
                return sb
        except Exception as exc:
            print(f"Supabase init failed, falling back to SQLite: {exc}")
    return Database()


# Singleton instance used across the app
db = _build_active_database()
