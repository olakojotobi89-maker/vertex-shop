"""
Customers management view.

Lists all customers in a table with search, and provides a detail dialog
showing the order history for a selected customer.

Reads real customer data from Supabase (public.customers) and their order
history from public.orders / public.order_items via the repository.
"""
import customtkinter as ctk

import config.settings as settings
from database.database import db
from utils import helpers
from views.widgets import (
    PageHeader, SearchBar, StatusBadge, make_button, font,
)


class CustomersView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = PageHeader(self, "Customers",
                            subtitle="Review your customers and their order history.")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        # Filter bar
        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        filters.grid_columnconfigure(0, weight=1)

        self.search = SearchBar(filters, placeholder="Search customers by name / phone / email...",
                                command=self._on_search, width=360)
        self.search.grid(row=0, column=0, sticky="w")

        # Table container (scrollable)
        self.table = ctk.CTkScrollableFrame(self, fg_color=settings.COLORS["card_bg"],
                                            corner_radius=14, border_width=1,
                                            border_color=settings.COLORS["card_border"])
        self.table.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.table.grid_columnconfigure(0, weight=1)

        self.refresh()

    def _on_search(self, text):
        self.refresh()

    def refresh(self):
        for child in self.table.winfo_children():
            child.destroy()

        search_text = self.search.get().strip().lower()
        customers = db.get_customers()
        if search_text:
            customers = [
                c for c in customers
                if search_text in (c.name or "").lower()
                or search_text in (c.phone or "").lower()
                or search_text in (c.email or "").lower()
            ]

        self.search.set_result(f"{len(customers)} customer{'s' if len(customers) != 1 else ''}")

        if not customers:
            ctk.CTkLabel(self.table, text="No customers found.", font=font(14),
                         text_color=settings.COLORS["text_muted"]).pack(pady=40)
            return

        # Header
        header = ctk.CTkFrame(self.table, fg_color=settings.COLORS["card_border"],
                              corner_radius=8, height=40)
        header.pack(fill="x", pady=(0, 6))
        header.pack_propagate(False)
        cols = ["Customer", "Phone", "Email", "Orders", "Total Spent", "Last Order"]
        for col in cols:
            ctk.CTkLabel(header, text=col, font=font(12, "semibold"),
                         text_color=settings.COLORS["text_muted"],
                         width=90, anchor="w").pack(side="left", padx=6, fill="x", expand=True)

        for customer in customers:
            row = ctk.CTkFrame(self.table, fg_color=settings.COLORS["card_bg"],
                               corner_radius=8, height=52)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)

            mname = customer.name or "—"
            ctk.CTkLabel(row, text=mname, font=font(13, "semibold"),
                         text_color=settings.COLORS["text"], width=80, anchor="w").pack(side="left", padx=8, fill="x", expand=True)
            ctk.CTkLabel(row, text=(customer.phone or "—"), font=font(12),
                         text_color=settings.COLORS["text_muted"], width=80, anchor="w").pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(row, text=(customer.email or "—"), font=font(12),
                         text_color=settings.COLORS["text_muted"], width=80, anchor="w").pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(row, text=str(customer.order_count or 0), font=font(13, "semibold"),
                         text_color=settings.COLORS["text"], width=50, anchor="w").pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(row, text=helpers.format_naira(customer.total_spent or 0), font=font(13, "semibold"),
                         text_color=settings.COLORS["text"], width=60, anchor="w").pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(row, text=helpers.format_date_short(customer.last_order_at), font=font(11),
                         text_color=settings.COLORS["text_muted"], width=80, anchor="w").pack(side="left", padx=4, fill="x", expand=True)

            # Make row clickable to view order history
            row.bind("<Button-1>", lambda e, c=customer: self._select_customer(c))

    def _select_customer(self, customer):
        """Open a dialog showing the selected customer's order history."""
        CustomerDetailDialog(self.app, customer)


class CustomerDetailDialog(ctk.CTkToplevel):
    """Detailed customer view with their order history."""

    def __init__(self, app, customer):
        super().__init__(app)
        self.app = app
        self.customer = customer
        self.title("Customer Details")
        self.geometry("640x520")
        self.resizable(False, False)
        self.transient(app)
        self.configure(fg_color=settings.COLORS["content_bg"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color=settings.COLORS["content_bg"])
        scroll.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        scroll.columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(scroll, text=customer.name or "Customer", font=font(20, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(scroll, text=f"Phone: {customer.phone or '—'}  ·  Email: {customer.email or '—'}",
                     font=font(13), text_color=settings.COLORS["text_muted"]).grid(
            row=1, column=0, sticky="w", pady=(2, 12))

        # Order history
        ctk.CTkLabel(scroll, text="Order History", font=font(14, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=2, column=0, sticky="w", pady=(6, 6))

        orders = []
        try:
            orders = db.get_customer_orders(phone=customer.phone or "", name=customer.name or "")
        except Exception as exc:
            print(f"[CUSTOMERS] Failed to load order history for {customer.name}: {exc}")
            ctk.CTkLabel(scroll, text=f"Could not load orders: {exc}",
                         text_color=settings.COLORS["danger"], font=font(12)).grid(
                row=3, column=0, sticky="w", pady=8)
            orders = []

        if not orders:
            ctk.CTkLabel(scroll, text="No orders found for this customer.",
                         font=font(13), text_color=settings.COLORS["text_muted"]).grid(
                row=3, column=0, sticky="w", pady=8)
        else:
            for i, order in enumerate(orders):
                card = ctk.CTkFrame(scroll, fg_color=settings.COLORS["card_bg"],
                                    corner_radius=10, border_width=1,
                                    border_color=settings.COLORS["card_border"])
                card.grid(row=3 + i, column=0, sticky="ew", pady=4)
                card.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(card, text=order.order_no, font=font(13, "bold"),
                             text_color=settings.COLORS["accent"]).grid(
                    row=0, column=0, sticky="w", padx=12, pady=(8, 0))
                StatusBadge(card, order.status).grid(row=0, column=1, padx=(6, 12), pady=(6, 0))

                ctk.CTkLabel(card, text=helpers.format_date(order.created_at),
                             font=font(11), text_color=settings.COLORS["text_muted"]).grid(
                    row=1, column=0, columnspan=2, sticky="w", padx=12)
                ctk.CTkLabel(card, text=f"{order.ordered_items_summary()} — {order.total_naira}",
                             font=font(12), text_color=settings.COLORS["text"]).grid(
                    row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 8))

        close_btn = make_button(scroll, "Close", command=self.destroy, border=True,
                                fg_color=settings.COLORS["accent"], width=100, height=34, font_size=13)
        close_btn.grid(row=3 + max(len(orders), 1), column=0, sticky="w", pady=(12, 4))

        self.grab_set()
