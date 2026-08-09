"""
Supabase-backed repository.

Implements the data-layer interface used by the views. Reads use the anon
(publishable) key. Writes (products, categories) require the admin session
to be active so that RLS (app_role=admin) permits them. If a write is
attempted without an admin session, an error is raised (never silently
swallowed).

Table / column mapping (see supabase_migration.sql):
    - categories : id(uuid), name, created_at
    - products   : id(uuid), name, description, price, image_url, available,
                   category_id(fk->categories.id), created_at
    - orders     : id(uuid), order_number, customer_id, customer_name,
                   customer_phone, order_type, delivery_address,
                   delivery_instructions, pickup_location, subtotal,
                   delivery_fee, total_amount, status, created_at
    - order_items: id, order_id(fk), product_id, quantity, product_name,
                   unit_price, subtotal
    - customers  : id(uuid), auth_user_id, full_name, phone, email
"""
from datetime import date, datetime

from models.product import Product
from models.order import Order, OrderItem
from models.customer import Customer

from .supabase_client import (
    get_supabase_client,
    is_admin_authenticated,
    get_admin_session,
    get_admin_user,
)


class SupabaseDatabase:
    """Supabase-backed implementation of the data-layer interface."""

    def __init__(self, client=None):
        self.client = client or get_supabase_client()
        self.available = self.client is not None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _require_admin(self):
        if not is_admin_authenticated():
            raise RuntimeError(
                "Administrator access required. Please sign in with an admin "
                "account on the Settings page."
            )

    def _resolve_category_id(self, category_name: str):
        """Resolve a category name to its id in Supabase."""
        if not category_name:
            return None
        try:
            resp = self.client.table("categories").select("id, name").ilike("name", category_name).execute()
            rows = resp.data or []
            if rows:
                return rows[0]["id"]
        except Exception:
            return None
        return None

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------
    def get_categories(self) -> list:
        resp = self.client.table("categories").select("id, name, created_at").order("name").execute()
        return resp.data or []

    def get_category_names(self) -> list:
        return [c["name"] for c in self.get_categories()]

    def add_category(self, name: str) -> dict:
        self._require_admin()
        resp = self.client.table("categories").insert({
            "name": name.strip(),
            "created_at": datetime.now().isoformat(),
        }).execute()
        return resp.data[0] if resp.data else {}

    def update_category(self, cat_id, name: str):
        self._require_admin()
        self.client.table("categories").update({"name": name.strip()}).eq("id", cat_id).execute()

    def delete_category(self, cat_id):
        self._require_admin()
        self.client.table("categories").delete().eq("id", cat_id).execute()

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------
    def get_products(self, search: str = "", category: str = "") -> list:
        query = self.client.table("products").select(
            "id, name, description, price, image_url, available, category_id, categories(name), created_at"
        )
        if search:
            query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")
        if category and category != "All":
            cat_id = self._resolve_category_id(category)
            if cat_id:
                query = query.eq("category_id", cat_id)
        query = query.order("created_at", desc=True)
        resp = query.execute()
        rows = resp.data or []
        return [self._product_from_sb(r) for r in rows]

    def get_product(self, product_id):
        resp = self.client.table("products").select(
            "id, name, description, price, image_url, available, category_id, categories(name), created_at"
        ).eq("id", product_id).execute()
        rows = resp.data or []
        if not rows:
            return None
        return self._product_from_sb(rows[0])

    def add_product(self, name, description="", category="", price=0.0, image="", available=True) -> Product:
        self._require_admin()
        cat_id = self._resolve_category_id(category)
        payload = {
            "name": name.strip(),
            "description": description.strip(),
            "price": float(price),
            "image_url": image,
            "available": available,
            "created_at": datetime.now().isoformat(),
        }
        if cat_id:
            payload["category_id"] = cat_id
        resp = self.client.table("products").insert(payload).execute()
        if not resp.data:
            raise RuntimeError("Could not insert product into Supabase.")
        inserted = resp.data[0]
        return self.get_product(inserted["id"])

    def update_product(self, product_id, name, description="", category="", price=0.0,
                       image=None, available=True):
        self._require_admin()
        cat_id = self._resolve_category_id(category)
        payload = {
            "name": name.strip(),
            "description": description.strip(),
            "price": float(price),
            "available": available,
        }
        if cat_id:
            payload["category_id"] = cat_id
        if image is not None:
            payload["image_url"] = image
        self.client.table("products").update(payload).eq("id", product_id).execute()

    def delete_product(self, product_id):
        self._require_admin()
        self.client.table("products").delete().eq("id", product_id).execute()

    def product_count(self) -> int:
        resp = self.client.table("products").select("id").execute()
        return len(resp.data or [])

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    def _items_for_order(self, order_id) -> list:
        resp = self.client.table("order_items").select(
            "id, product_id, quantity, product_name, unit_price, subtotal"
        ).eq("order_id", order_id).execute()
        return [
            OrderItem(
                product_id=it.get("product_id") or 0,
                name=it.get("product_name", ""),
                price=float(it.get("unit_price", 0) or 0),
                quantity=int(it.get("quantity", 1)),
            )
            for it in (resp.data or [])
        ]

    def get_orders(self, search: str = "", status: str = "") -> list:
        query = self.client.table("orders").select("*")
        if search:
            query = query.or_(
                f"order_number.ilike.%{search}%,customer_name.ilike.%{search}%,customer_phone.ilike.%{search}%"
            )
        if status and status != "All":
            query = query.eq("status", status)
        query = query.order("created_at", desc=True)
        resp = query.execute()
        rows = resp.data or []
        orders = []
        for r in rows:
            items = self._items_for_order(r["id"])
            orders.append(self._order_from_sb(r, items=items))
        return orders

    def get_order(self, order_id):
        resp = self.client.table("orders").select("*").eq("id", order_id).execute()
        rows = resp.data or []
        if not rows:
            return None
        items = self._items_for_order(rows[0]["id"])
        return self._order_from_sb(rows[0], items=items)

    def add_order(self, order: Order) -> Order:
        resp = self.client.table("orders").insert({
            "customer_id": getattr(order, "customer_id", None),
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "customer_email": order.customer_email,
            "order_type": order.delivery_method,
            "delivery_address": order.delivery_address or None,
            "delivery_instructions": order.delivery_instructions or None,
            "pickup_location": order.pickup_location or None,
            "subtotal": order.subtotal,
            "delivery_fee": order.delivery_fee,
            "total_amount": order.total,
            "status": order.status,
            "created_at": order.created_at,
        }).execute()
        if not resp.data:
            raise RuntimeError("Could not insert order into Supabase.")
        row = resp.data[0]

        items_payload = []
        for it in order.items:
            items_payload.append({
                "order_id": row["id"],
                "product_id": it.product_id,
                "quantity": it.quantity,
                "product_name": it.name,
                "unit_price": it.price,
                "subtotal": it.subtotal,
            })
        if items_payload:
            self.client.table("order_items").insert(items_payload).execute()

        return self.get_order(row["id"])

    def update_order_status(self, order_id, status: str):
        self._require_admin()
        self.client.table("orders").update({"status": status}).eq("id", order_id).execute()

    def order_count(self) -> int:
        resp = self.client.table("orders").select("id").execute()
        return len(resp.data or [])

    def orders_by_status(self, status: str) -> int:
        resp = self.client.table("orders").select("id").eq("status", status).execute()
        return len(resp.data or [])

    def orders_today(self) -> int:
        today = date.today().isoformat()
        resp = self.client.table("orders").select("id").gte("created_at", today).execute()
        return len(resp.data or [])

    def sales_today(self) -> float:
        today = date.today().isoformat()
        resp = self.client.table("orders").select("total_amount").gte("created_at", today).neq("status", "Cancelled").execute()
        rows = resp.data or []
        return sum(float(r.get("total_amount", 0) or 0) for r in rows)

    def recent_orders(self, limit: int = 5) -> list:
        resp = self.client.table("orders").select("*").order("created_at", desc=True).limit(limit).execute()
        rows = resp.data or []
        orders = []
        for r in rows:
            items = self._items_for_order(r["id"])
            orders.append(self._order_from_sb(r, items=items))
        return orders

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------
    def get_customers(self) -> list:
        resp = self.client.table("customers").select(
            "id, full_name, phone, email, auth_user_id, created_at"
        ).order("created_at", desc=True).execute()
        rows = resp.data or []
        customers = []
        for r in rows:
            order_count, total_spent, last_order = self._customer_order_stats(r.get("id"))
            customers.append(Customer(
                name=r.get("full_name", ""),
                phone=r.get("phone", ""),
                email=r.get("email", ""),
                order_count=order_count,
                total_spent=total_spent,
                last_order_at=last_order,
            ))
        if not customers:
            customers = self._customers_from_orders()
        return customers

    def _customer_order_stats(self, customer_id):
        resp = self.client.table("orders").select("total_amount, status, created_at").eq("customer_id", customer_id).execute()
        rows = resp.data or []
        order_count = len(rows)
        total_spent = sum(float(r.get("total_amount", 0) or 0) for r in rows if r.get("status") != "Cancelled")
        last_order = max((r["created_at"] for r in rows), default="") if rows else ""
        return order_count, total_spent, last_order

    def _customers_from_orders(self) -> list:
        resp = self.client.table("orders").select(
            "id, customer_name, customer_phone, customer_email, total_amount, status, created_at"
        ).order("created_at", desc=True).execute()
        rows = resp.data or []
        grouped = {}
        for r in rows:
            key = r.get("customer_phone") or r.get("customer_name") or ""
            key = key.strip().lower()
            if not key:
                key = r.get("customer_name", "").lower()
            if key not in grouped:
                grouped[key] = {
                    "name": r.get("customer_name", ""),
                    "phone": r.get("customer_phone", ""),
                    "email": r.get("customer_email", ""),
                    "count": 0,
                    "spent": 0.0,
                    "last": r.get("created_at", ""),
                }
            grouped[key]["count"] += 1
            if r.get("status") != "Cancelled":
                grouped[key]["spent"] += float(r.get("total_amount", 0) or 0)
            grouped[key]["last"] = max(grouped[key]["last"], r.get("created_at", ""))
        customers = [Customer(
            name=g["name"], phone=g["phone"], email=g["email"],
            order_count=g["count"], total_spent=g["spent"], last_order_at=g["last"],
        ) for g in grouped.values()]
        customers.sort(key=lambda c: c.total_spent, reverse=True)
        return customers

    def get_customer_orders(self, phone: str = "", name: str = "") -> list:
        query = self.client.table("orders").select("*").order("created_at", desc=True)
        if phone:
            query = query.eq("customer_phone", phone)
        if name:
            query = query.eq("customer_name", name)
        resp = query.execute()
        rows = resp.data or []
        orders = []
        for r in rows:
            items = self._items_for_order(r["id"])
            orders.append(self._order_from_sb(r, items=items))
        return orders

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
    # Mappers (Supabase rows -> models)
    # ------------------------------------------------------------------
    def _product_from_sb(self, r) -> Product:
        category_name = ""
        if r.get("categories"):
            category_name = r["categories"].get("name", "")
        return Product(
            id=r["id"],
            name=r.get("name", ""),
            description=r.get("description", ""),
            category=category_name,
            price=float(r.get("price", 0) or 0),
            image=r.get("image_url", ""),
            available=bool(r.get("available", True)),
            created_at=r.get("created_at", ""),
        )

    def _order_from_sb(self, r, items=None) -> Order:
        order = Order(
            id=r["id"],
            order_no=r.get("order_number", ""),
            customer_name=r.get("customer_name", ""),
            customer_phone=r.get("customer_phone", ""),
            customer_email=r.get("customer_email", ""),
            delivery_method=r.get("order_type", "delivery"),
            delivery_address=r.get("delivery_address", ""),
            delivery_instructions=r.get("delivery_instructions", ""),
            pickup_location=r.get("pickup_location", ""),
            subtotal=float(r.get("subtotal", 0) or 0),
            delivery_fee=float(r.get("delivery_fee", 0) or 0),
            total=float(r.get("total_amount", 0) or 0),
            status=r.get("status", "Pending"),
            created_at=r.get("created_at", ""),
        )
        order.items = items or []
        return order
