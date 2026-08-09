"""
Order model.

Represents a customer order placed through the Vertex Shop public website.
The dashboard reads these, updates their status, and (later) receives them
in real time from Supabase Realtime.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class OrderItem:
    product_id: int = 0
    name: str = ""
    price: float = 0.0
    quantity: int = 1

    @property
    def subtotal(self) -> float:
        return self.price * self.quantity

    @property
    def subtotal_naira(self) -> str:
        return f"₦{self.subtotal:,.0f}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "OrderItem":
        return cls(
            product_id=int(data.get("product_id", data.get("id", 0))),
            name=data.get("name", ""),
            price=float(data.get("price", 0)),
            quantity=int(data.get("quantity", 1)),
        )


@dataclass
class Order:
    id: int = 0
    order_no: str = ""            # e.g. #VS-1001
    customer_id: str = None       # UUID from public.customers (optional)
    customer_name: str = ""
    customer_phone: str = ""
    customer_email: str = ""      # optional
    delivery_method: str = "delivery"  # "delivery" | "pickup"
    delivery_address: str = ""
    delivery_instructions: str = ""
    pickup_location: str = ""
    items: list = field(default_factory=list)   # list[OrderItem]
    subtotal: float = 0.0
    delivery_fee: float = 0.0
    total: float = 0.0
    status: str = "pending"
    created_at: str = ""          # ISO string

    def __post_init__(self):
        if not self.order_no:
            self.order_no = self.generate_order_no(self.id)
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @staticmethod
    def generate_order_no(oid: int) -> str:
        return f"VS-{1000 + int(oid or 0)}"

    @property
    def is_delivery(self) -> bool:
        return self.delivery_method == "delivery"

    @property
    def total_naira(self) -> str:
        return f"₦{self.total:,.0f}"

    @property
    def subtotal_naira(self) -> str:
        return f"₦{self.subtotal:,.0f}"

    @property
    def order_items(self) -> list:
        return self.items

    @property
    def customer_order_count(self) -> int:
        return len(self.items)

    def ordered_items_summary(self) -> str:
        """Human-readable summary like 'Jollof Rice x2, Chicken x1'."""
        return ", ".join(f"{it.name} x{it.quantity}" for it in self.items)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["items"] = [it.to_dict() for it in self.items]
        return data

    @classmethod
    def from_row(cls, row, items=None) -> "Order":
        """Build an Order from a database row (dict) plus optional items."""
        if row is None:
            return cls()
        order = cls(
            id=row.get("id", 0),
            order_no=row.get("order_no", ""),
            customer_name=row.get("customer_name", ""),
            customer_phone=row.get("customer_phone", ""),
            customer_email=row.get("customer_email", ""),
            delivery_method=row.get("delivery_method", "delivery"),
            delivery_address=row.get("delivery_address", ""),
            delivery_instructions=row.get("delivery_instructions", ""),
            pickup_location=row.get("pickup_location", ""),
            subtotal=float(row.get("subtotal", 0) or 0),
            delivery_fee=float(row.get("delivery_fee", 0) or 0),
            total=float(row.get("total", 0) or 0),
            status=row.get("status", "pending"),
            created_at=row.get("created_at", ""),
        )
        order.items = items or []
        return order
