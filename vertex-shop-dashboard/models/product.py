"""
Product model.

A plain dataclass used across the app. Instances are created from
rows returned by the data layer (currently SQLite, later Supabase).
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Product:
    id: int = 0
    name: str = ""
    description: str = ""
    category: str = ""
    price: float = 0.0
    image: str = ""          # local file path (later: Supabase Storage URL)
    available: bool = True
    created_at: str = ""     # ISO string

    def __post_init__(self):
        self.name = self.name or ""
        self.description = self.description or ""
        self.category = self.category or ""
        self.image = self.image or ""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @property
    def price_naira(self) -> str:
        """Return the price formatted as a Naira string (e.g. ₦8,000)."""
        return f"₦{self.price:,.0f}"

    @property
    def availability_label(self) -> str:
        return "Available" if self.available else "Unavailable"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row) -> "Product":
        """Build a Product from a database row (dict-like)."""
        if row is None:
            return cls()
        return cls(
            id=row.get("id", 0),
            name=row.get("name", ""),
            description=row.get("description", ""),
            category=row.get("category", ""),
            price=float(row.get("price", 0) or 0),
            image=row.get("image", ""),
            available=bool(row.get("available", 1)),
            created_at=row.get("created_at", ""),
        )
