from dataclasses import dataclass, field

@dataclass
class Customer:
    id: str = None  # UUID from public.customers table (if registered)
    customer_id: str = None # UUID from public.customers table (if registered)
    name: str = ""
    phone: str = ""
    email: str = ""
    order_count: int = 0
    total_spent: float = 0.0
    last_order_at: str = ""
    orders: list = field(default_factory=list)

    def __hash__(self):
        return hash((self.id, self.phone, self.email))