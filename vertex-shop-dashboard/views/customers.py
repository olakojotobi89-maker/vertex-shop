"""
Customers view.

Shows aggregated customer information and order history when a customer
is selected.
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
        self.grid_rowconfigure(2, weight=1)

        header = PageHeader(self, "Customers",
                            subtitle="See who's ordering and their order history.")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        self.search = SearchBar(self, placeholder="Search customers by name or phone...",
                                command=self._on_search, width=360)
        self.search.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 10))

        # Main split: customer list + history
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))
        body.grid_columnconfigure(0, weight=2, uniform="c")
        body.grid_columnconfigure(1, weight=3, uniform="c")
        body.grid_rowconfigure(0, weight=1)

        # Customer list
        list_card = ctk.CTkFrame(body, fg_color=settings.COLORS["card_bg"], corner_radius=14,
                                 border_width=1, border_color=settings.COLORS["card_border"])
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        list_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(list_card, text="Customers", font=font(16, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=0, column=0, sticky="w", padx=16, pady=14)
        self.customer_list = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.customer_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.customer_list.grid_columnconfigure(0, weight=1)

        # History panel
        hist_card = ctk.CTkFrame(body, fg_color=settings.COLORS["card_bg"], corner_radius=14,
                                 border_width=1, border_color=settings.COLORS["card_border"])
        hist_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        hist_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hist_card, text="Order History", font=font(16, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=0, column=0, sticky="w", padx=16, pady=14)
        self.history_frame = ctk.CTkScrollableFrame(hist_card, fg_color="transparent")
        self.history_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.history_frame.grid_columnconfigure(0, weight=1)

        self.selected_customer = None
        self.refresh()

    def _on_search(self, text):
        self.refresh()

    def refresh(self):
        # Clear lists
        for child in self.customer_list.winfo_children():
            child.destroy()
        for child in self.history_frame.winfo_children():
            child.destroy()

        search_text = self.search.get().strip().lower()
        customers = db.get_customers()
        if search_text:
            customers = [c for c in customers
                         if search_text in c.name.lower() or search_text in c.phone.lower()]

        if not customers:
            ctk.CTkLabel(self.customer_list, text="No customers found.", font=font(13),
                         text_color=settings.COLORS["text_muted"]).pack(pady=30)
            ctk.CTkLabel(self.history_frame, text="Select a customer to see their orders.",
                         font=font(13), text_color=settings.COLORS["text_muted"]).pack(pady=30)
            return

        for cust in customers:
            row = ctk.CTkFrame(self.customer_list, fg_color=settings.COLORS["card_bg"],
                               corner_radius=10, border_width=1,
                               border_color=settings.COLORS["card_border"])
            row.pack(fill="x", pady=3)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(row, text="👤  " + cust.name, font=font(13, "semibold"),
                         text_color=settings.COLORS["text"]).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(row, text=f"{cust.phone}  ·  {cust.order_count} order{'s' if cust.order_count != 1 else ''}  ·  {cust.total_spent_naira}",
                         font=font(11), text_color=settings.COLORS["text_muted"]).grid(
                row=1, column=0, sticky="w", padx=12, pady=(0, 8))
            row.bind("<Button-1>", lambda e, c=cust: self._select_customer(c))

        # Select the first customer by default
        self._select_customer(customers[0])

    def _select_customer(self, customer):
        self.selected_customer = customer
        # Highlight selection by reloading list with selected marked
        for child in self.customer_list.winfo_children():
            pass  # simple: we just show history

        # Load history
        for child in self.history_frame.winfo_children():
            child.destroy()

        orders = db.get_customer_orders(phone=customer.phone, name=customer.name)
        if not orders:
            ctk.CTkLabel(self.history_frame, text="No orders yet.", font=font(13),
                         text_color=settings.COLORS["text_muted"]).pack(pady=30)
            return

        for order in orders:
            row = ctk.CTkFrame(self.history_frame, fg_color=settings.COLORS["card_bg"],
                               corner_radius=10, border_width=1,
                               border_color=settings.COLORS["card_border"])
            row.pack(fill="x", pady=3)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=order.order_no, font=font(13, "bold"),
                         text_color=settings.COLORS["accent"]).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(row, text=order.total_naira, font=font(13, "semibold"),
                         text_color=settings.COLORS["text"]).grid(row=0, column=2, sticky="e", padx=12, pady=(8, 0))
            StatusBadge(row, order.status).grid(row=0, column=3, padx=(6, 12), pady=(4, 0))
            ctk.CTkLabel(row, text=f"{order.ordered_items_summary()} · {helpers.format_date(order.created_at)}",
                         font=font(11), text_color=settings.COLORS["text_muted"]).grid(
                row=1, column=0, columnspan=4, sticky="w", padx=12, pady=(0, 8))
            row.bind("<Button-1>", lambda e, oid=order.id: self.app.show_order_detail(oid))
