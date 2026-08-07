"""
Customer model.

Representation of a customer that has placed orders. Currently derived from
order data; when Supabase is integrated this can map to a `customers` table
or the auth user profile.
"""
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Customer:
    name: str = ""
    phone: str = ""
    email: str = ""
    order_count: int = 0
    total_spent: float = 0.0
    last_order_at: str = ""
    orders: list = None  # list of Order objects (order history)

    def __post_init__(self):
        if self.orders is None:
            self.orders = []

    @property
    def total_spent_naira(self) -> str:
        return f"₦{self.total_spent:,.0f}"

    @property
    def display_key(self) -> str:
        """A stable key used to group orders for the same customer."""
        # Group by phone if present, otherwise by name.
        key = (self.phone or "").strip().lower()
        return key if key else (self.name or "").strip().lower()

    def to_dict(self) -> dict:
        return asdict(self)
