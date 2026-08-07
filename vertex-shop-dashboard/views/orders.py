"""
Orders management view.

Displays all orders in a professional table with search + status filters,
and provides a detailed order dialog with a status-update workflow.
"""
import customtkinter as ctk

import config.settings as settings
from database.database import db
from utils import helpers
from views.widgets import (
    PageHeader, SearchBar, StatusBadge, make_button, font, confirm_dialog,
)


class OrdersView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = PageHeader(self, "Orders",
                            subtitle="Review incoming orders and update their status.")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        # Filter bar
        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        filters.grid_columnconfigure(0, weight=1)

        self.search = SearchBar(filters, placeholder="Search by order no / customer / phone",
                                command=self._on_search, width=360)
        self.search.grid(row=0, column=0, sticky="w")

        self.status_filter = ctk.StringVar(value="All")
        statuses = ["All"] + settings.ORDER_STATUSES
        status_menu = ctk.CTkOptionMenu(
            filters, variable=self.status_filter, values=statuses,
            command=lambda _: self.refresh(), font=font(13), dropdown_font=font(13),
            fg_color=settings.COLORS["card_bg"], button_color=settings.COLORS["card_border"],
            button_hover_color=settings.COLORS["card_border"],
            text_color=settings.COLORS["text"], width=180, height=36)
        status_menu.grid(row=0, column=1, padx=(8, 0), sticky="e")

        # Table
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

        search_text = self.search.get().strip()
        status = self.status_filter.get()
        orders = db.get_orders(search=search_text, status=status)

        self.search.set_result(f"{len(orders)} order{'s' if len(orders) != 1 else ''}")

        if not orders:
            ctk.CTkLabel(self.table, text="No orders found.", font=font(14),
                         text_color=settings.COLORS["text_muted"]).pack(pady=40)
            return

        # Header
        header = ctk.CTkFrame(self.table, fg_color=settings.COLORS["card_border"], corner_radius=8, height=40)
        header.pack(fill="x", pady=(0, 6))
        header.pack_propagate(False)
        cols = ["Order", "Customer", "Phone", "Items", "Total", "Type", "Date/Time", "Status"]
        for col in cols:
            ctk.CTkLabel(header, text=col, font=font(12, "semibold"),
                         text_color=settings.COLORS["text_muted"],
                         width=90, anchor="w").pack(side="left", padx=6, fill="x", expand=True)

        for order in orders:
            row = ctk.CTkFrame(self.table, fg_color=settings.COLORS["card_bg"], corner_radius=8, height=52)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=order.order_no, font=font(13, "bold"),
                         text_color=settings.COLORS["accent"], width=60, anchor="w").pack(side="left", padx=8, fill="x", expand=True)
            ctk.CTkLabel(row, text=order.customer_name, font=font(13),
                         text_color=settings.COLORS["text"], width=80, anchor="w").pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(row, text=order.customer_phone, font=font(12),
                         text_color=settings.COLORS["text_muted"], width=80, anchor="w").pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(row, text=order.ordered_items_summary()[:24], font=font(12),
                         text_color=settings.COLORS["text"], width=110, anchor="w").pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(row, text=order.total_naira, font=font(13, "semibold"),
                         text_color=settings.COLORS["text"], width=60, anchor="w").pack(side="left", padx=4, fill="x", expand=True)
            type_text = "Delivery" if order.is_delivery else "Pickup"
            ctk.CTkLabel(row, text=type_text, font=font(12),
                         text_color=settings.COLORS["accent"] if order.is_delivery else settings.COLORS["primary"],
                         width=50, anchor="w").pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(row, text=helpers.format_date(order.created_at, "%d %b %H:%M"), font=font(11),
                         text_color=settings.COLORS["text_muted"], width=90, anchor="w").pack(side="left", padx=4, fill="x", expand=True)

            status_frame = ctk.CTkFrame(row, fg_color="transparent", width=80)
            status_frame.pack(side="left", padx=6)
            StatusBadge(status_frame, order.status).pack()

            # Make row clickable
            row.bind("<Button-1>", lambda e, oid=order.id: self.app.show_order_detail(oid))

    def open_detail(self, order_id):
        OrderDetailDialog(self.app, order_id, on_change=self.refresh)


class OrderDetailDialog(ctk.CTkToplevel):
    """Detailed order view with a status-update dropdown."""

    def __init__(self, app, order_id, on_change=None):
        super().__init__(app)
        self.app = app
        self.order_id = order_id
        self.on_change = on_change
        self.title("Order Details")
        self.geometry("640x600")
        self.resizable(False, False)
        self.transient(app)
        self.configure(fg_color=settings.COLORS["content_bg"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.order = db.get_order(order_id)

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self, fg_color=settings.COLORS["content_bg"])
        scroll.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        scroll.columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(scroll, text=f"ORDER {self.order.order_no}", font=font(20, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(scroll, text=helpers.format_date(self.order.created_at), font=font(12),
                     text_color=settings.COLORS["text_muted"]).grid(row=1, column=0, sticky="w", pady=(2, 12))

        # Customer info
        self._section_title(scroll, "Customer Information", 2)
        cust_card = ctk.CTkFrame(scroll, fg_color=settings.COLORS["card_bg"], corner_radius=10)
        cust_card.grid(row=3, column=0, sticky="ew", pady=(4, 12))
        cust_card.columnconfigure(0, weight=1)
        self._info_line(cust_card, 0, "Name", self.order.customer_name)
        self._info_line(cust_card, 1, "Phone", self.order.customer_phone)
        if self.order.customer_email:
            self._info_line(cust_card, 2, "Email", self.order.customer_email)

        # Order info (items)
        self._section_title(scroll, "Order Information", 4)
        items_card = ctk.CTkFrame(scroll, fg_color=settings.COLORS["card_bg"], corner_radius=10)
        items_card.grid(row=5, column=0, sticky="ew", pady=(4, 4))
        items_card.columnconfigure(3, weight=1)
        for i, h in enumerate(["Product", "Qty", "Unit", "Subtotal"]):
            ctk.CTkLabel(items_card, text=h, font=font(11, "semibold"),
                         text_color=settings.COLORS["text_muted"]).grid(
                row=0, column=i, sticky="w", padx=10, pady=(8, 2))
        row_i = 1
        for item in self.order.items:
            ctk.CTkLabel(items_card, text=item.name, font=font(12),
                         text_color=settings.COLORS["text"]).grid(row=row_i, column=0, sticky="w", padx=10, pady=3)
            ctk.CTkLabel(items_card, text=str(item.quantity), font=font(12),
                         text_color=settings.COLORS["text_muted"]).grid(row=row_i, column=1, sticky="w", padx=10, pady=3)
            ctk.CTkLabel(items_card, text=f"₦{item.price:,.0f}", font=font(12),
                         text_color=settings.COLORS["text_muted"]).grid(row=row_i, column=2, sticky="w", padx=10, pady=3)
            ctk.CTkLabel(items_card, text=item.subtotal_naira, font=font(12, "semibold"),
                         text_color=settings.COLORS["text"]).grid(row=row_i, column=3, sticky="w", padx=10, pady=3)
            row_i += 1
        # Totals
        ctk.CTkLabel(items_card, text="Subtotal", font=font(12),
                     text_color=settings.COLORS["text_muted"]).grid(row=row_i, column=2, sticky="e", padx=10, pady=(8, 0))
        ctk.CTkLabel(items_card, text=self.order.subtotal_naira, font=font(12, "semibold"),
                     text_color=settings.COLORS["text"]).grid(row=row_i, column=3, sticky="w", padx=10, pady=(8, 0))
        row_i += 1
        ctk.CTkLabel(items_card, text="Delivery Fee", font=font(12),
                     text_color=settings.COLORS["text_muted"]).grid(row=row_i, column=2, sticky="e", padx=10)
        ctk.CTkLabel(items_card, text=f"₦{self.order.delivery_fee:,.0f}", font=font(12, "semibold"),
                     text_color=settings.COLORS["text"]).grid(row=row_i, column=3, sticky="w", padx=10)
        row_i += 1
        ctk.CTkLabel(items_card, text="Total", font=font(13, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=row_i, column=2, sticky="e", padx=10, pady=(2, 10))
        ctk.CTkLabel(items_card, text=self.order.total_naira, font=font(15, "bold"),
                     text_color=settings.COLORS["primary"]).grid(row=row_i, column=3, sticky="w", padx=10, pady=(2, 10))

        # Delivery / Pickup info
        self._section_title(scroll, "Delivery Information", 6)
        deliv_card = ctk.CTkFrame(scroll, fg_color=settings.COLORS["card_bg"], corner_radius=10)
        deliv_card.grid(row=7, column=0, sticky="ew", pady=(4, 12))
        deliv_card.columnconfigure(0, weight=1)
        if self.order.is_delivery:
            self._info_line(deliv_card, 0, "Type", "Delivery")
            self._info_line(deliv_card, 1, "Delivery Address", self.order.delivery_address)
            self._info_line(deliv_card, 2, "Delivery Instructions",
                            self.order.delivery_instructions or "—")
            self._info_line(deliv_card, 3, "Phone", self.order.customer_phone)
        else:
            self._info_line(deliv_card, 0, "Type", "Pickup")
            self._info_line(deliv_card, 1, "Pickup Location", self.order.pickup_location or "—")
            self._info_line(deliv_card, 2, "Phone", self.order.customer_phone)

        # Order status update
        self._section_title(scroll, "Order Status", 8)
        status_card = ctk.CTkFrame(scroll, fg_color=settings.COLORS["card_bg"], corner_radius=10)
        status_card.grid(row=9, column=0, sticky="ew", pady=(4, 4))
        status_card.columnconfigure(1, weight=1)

        ctk.CTkLabel(status_card, text="Current status:", font=font(13),
                     text_color=settings.COLORS["text_muted"]).grid(row=0, column=0, sticky="w", padx=12, pady=10)
        StatusBadge(status_card, self.order.status).grid(row=0, column=1, sticky="w", padx=4, pady=10)

        ctk.CTkLabel(status_card, text="Update status:", font=font(13),
                     text_color=settings.COLORS["text"]).grid(row=1, column=0, sticky="w", padx=12, pady=(4, 12))
        self.status_var = ctk.StringVar(value=self.order.status)
        status_menu = ctk.CTkOptionMenu(
            status_card, variable=self.status_var, values=settings.ORDER_STATUSES,
            font=font(13), dropdown_font=font(12), width=180, height=34,
            fg_color=settings.COLORS["card_border"], button_color=settings.COLORS["card_border"],
            button_hover_color=settings.COLORS["card_border"], text_color=settings.COLORS["text"])
        status_menu.grid(row=1, column=1, sticky="w", padx=4, pady=(4, 12))

        update_btn = make_button(scroll, "Update Status", command=self._update_status,
                                 width=180, height=38, font_size=14)
        update_btn.grid(row=10, column=0, sticky="w", pady=(12, 4))

        close_btn = make_button(scroll, "Close", command=self.destroy, border=True,
                                fg_color=settings.COLORS["accent"], width=100, height=34, font_size=13)
        close_btn.grid(row=11, column=0, sticky="w", pady=(4, 10))

        self.grab_set()

    def _section_title(self, parent, text, row):
        ctk.CTkLabel(parent, text=text, font=font(14, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=row, column=0, sticky="w", pady=(6, 2))

    def _info_line(self, parent, row, key, value):
        ctk.CTkLabel(parent, text=f"{key}:", font=font(12, "semibold"),
                     text_color=settings.COLORS["text_muted"]).grid(row=row, column=0, sticky="w", padx=12, pady=4)
        ctk.CTkLabel(parent, text=str(value or "—"), font=font(12),
                     text_color=settings.COLORS["text"], anchor="w", wraplength=380).grid(
            row=row, column=1, sticky="ew", padx=12, pady=4)

    def _update_status(self):
        new_status = self.status_var.get()
        if new_status == self.order.status:
            self.app.toast_global("Status unchanged")
            return
        db.update_order_status(self.order_id, new_status)
        self.app.toast_global(f"Order {self.order.order_no} → {new_status}")
        if self.on_change:
            self.on_change()
        self.order = db.get_order(self.order_id)
        self.destroy()
