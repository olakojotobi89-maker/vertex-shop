"""
Notification panel.

Simulates incoming new-order notifications. When Supabase is connected,
this will be driven by Supabase Realtime instead of the local simulator.
"""
import threading
import time
from datetime import datetime

import customtkinter as ctk

import config.settings as settings
from database.database import db
from models.order import Order, OrderItem
from utils import helpers
from views.widgets import font, make_button


# Demo names/items used to simulate incoming orders.
DEMO_FIRST = ["John", "Mary", "David", "Aisha", "Chinedu", "Fatima", "Grace", "Ibrahim", "Ngozi", "Tunde"]
DEMO_LAST = ["Doe", "James", "Smith", "Bello", "Okafor", "Sani", "Adeyemi", "Musa", "Okon", "Balogun"]
DEMO_ITEMS = [
    ("Jollof Rice", 3500), ("Chicken & Chips", 4800), ("Meat Pie", 1200),
    ("Shawarma", 3200), ("Chocolate Cake", 6500), ("Puff Puff", 1000),
    ("Fresh Juice", 1800), ("Egg Roll", 900), ("Vanilla Cupcake", 1500), ("Samosa", 800),
]


class NotificationCenter:
    """Manages simulated new-order notifications and a callback on new order."""

    def __init__(self, app):
        self.app = app
        self.on_new_order = None    # callable(order) -> None
        self._stop = threading.Event()

    def start(self):
        if not settings.SIMULATE_NEW_ORDERS:
            return
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        # First simulated order after a short delay, then periodically.
        delay = 8
        while not self._stop.wait(delay):
            try:
                order = self._create_simulated_order()
                if self.on_new_order:
                    self.on_new_order(order)
            except Exception:
                pass
            delay = settings.SIMULATE_ORDER_INTERVAL_SEC

    def _create_simulated_order(self) -> Order:
        import random
        name = f"{random.choice(DEMO_FIRST)} {random.choice(DEMO_LAST)}"
        phone = self._random_phone()
        # 1-3 items
        chosen = random.sample(DEMO_ITEMS, k=random.randint(1, 3))
        items = [OrderItem(name=n, price=p, quantity=random.randint(1, 3)) for n, p in chosen]
        subtotal = sum(it.subtotal for it in items)
        is_delivery = random.random() < 0.7
        fee = settings.DELIVERY_FEE if is_delivery else 0
        order = Order(
            customer_name=name,
            customer_phone=phone,
            delivery_method="delivery" if is_delivery else "pickup",
            delivery_address=("23 Somewhere Road, City" if is_delivery else ""),
            delivery_instructions=("Call on arrival" if is_delivery else ""),
            pickup_location=(settings.PICKUP_LOCATIONS[0] if not is_delivery else ""),
            items=items,
            subtotal=subtotal,
            delivery_fee=fee,
            total=subtotal + fee,
            status="Pending",
            created_at=datetime.now().isoformat(),
        )
        return db.add_order(order)

    @staticmethod
    def _random_phone():
        import random
        return "080" + "".join(str(random.randint(0, 9)) for _ in range(8))


class NotificationPanel(ctk.CTkToplevel):
    """A slide-out panel listing recent order notifications."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Notifications")
        self.geometry("360x520")
        self.resizable(False, False)
        self.transient(app)
        self.configure(fg_color=settings.COLORS["card_bg"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        head = ctk.CTkFrame(self, fg_color=settings.COLORS["card_bg"])
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        ctk.CTkLabel(head, text="🔔  Notifications", font=font(18, "bold"),
                     text_color=settings.COLORS["text"]).pack(side="left")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=settings.COLORS["card_bg"])
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.list_frame.grid_columnconfigure(0, weight=1)

        self._refresh()
        self.grab_set()

    def _refresh(self):
        for child in self.list_frame.winfo_children():
            child.destroy()
        orders = db.recent_orders(10)
        if not orders:
            ctk.CTkLabel(self.list_frame, text="No notifications yet.",
                         text_color=settings.COLORS["text_muted"]).pack(pady=30)
            return
        for order in orders:
            card = ctk.CTkFrame(self.list_frame, fg_color=settings.COLORS["card_bg"],
                                corner_radius=10, border_width=1,
                                border_color=settings.COLORS["card_border"])
            card.pack(fill="x", pady=4)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text="🔔 NEW ORDER", font=font(11, "bold"),
                         text_color=settings.COLORS["primary"]).grid(
                row=0, column=0, sticky="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(card, text=f"Order {order.order_no}", font=font(13),
                         text_color=settings.COLORS["text"]).grid(
                row=1, column=0, sticky="w", padx=12, pady=(2, 0))
            ctk.CTkLabel(card, text=f"Customer: {order.customer_name}", font=font(12),
                         text_color=settings.COLORS["text_muted"]).grid(
                row=2, column=0, sticky="w", padx=12)
            ctk.CTkLabel(card, text=f"Total: {order.total_naira}", font=font(12, "semibold"),
                         text_color=settings.COLORS["text"]).grid(
                row=3, column=0, sticky="w", padx=12)
            ctk.CTkLabel(card, text="New order received.", font=font(11),
                         text_color=settings.COLORS["accent"]).grid(
                row=4, column=0, sticky="w", padx=12, pady=(2, 8))
