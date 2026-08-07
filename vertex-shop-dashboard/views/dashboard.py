"""
Dashboard view - summary cards, recent orders, and quick insights.
"""
import customtkinter as ctk

import config.settings as settings
from database.database import db
from utils import helpers
from views.widgets import (
    StatCard, StatusBadge, PageHeader, make_button, font, _with_alpha,
)


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Header
        header = PageHeader(
            self,
            "Dashboard",
            subtitle="Overview of your shop's performance and recent activity.",
        )
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))

        # Stat cards row
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=8)
        for i in range(5):
            self.stats_frame.grid_columnconfigure(i, weight=1)

        self.stat_widgets = {}
        card_defs = [
            ("Total Products", "▦", settings.COLORS["accent"]),
            ("Total Orders", "▤", settings.COLORS["primary"]),
            ("Pending Orders", "⏲", settings.COLORS["warning"]),
            ("Completed Orders", "✓", settings.COLORS["primary"]),
            ("Today's Sales", "₦", settings.COLORS["accent"]),
        ]
        for i, (label, icon, accent) in enumerate(card_defs):
            card = StatCard(self.stats_frame, label, "0", icon=icon, accent=accent)
            card.grid(row=0, column=i, padx=6, pady=6, sticky="nsew")
            self.stat_widgets[label] = card

        # Recent orders + quick actions
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="nesw", padx=24, pady=8)
        bottom.grid_columnconfigure(0, weight=3, uniform="b")
        bottom.grid_columnconfigure(1, weight=2, uniform="b")
        self.grid_rowconfigure(2, weight=1)

        # Recent orders card
        recent_card = ctk.CTkFrame(bottom, fg_color=settings.COLORS["card_bg"],
                                   corner_radius=14, border_width=1,
                                   border_color=settings.COLORS["card_border"])
        recent_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        recent_card.grid_columnconfigure(0, weight=1)

        recent_head = ctk.CTkFrame(recent_card, fg_color="transparent")
        recent_head.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
        recent_head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(recent_head, text="Recent Orders", font=font(16, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=0, column=0, sticky="w")
        view_all_btn = make_button(recent_head, "View all", command=self._go_orders,
                                   border=True, fg_color=settings.COLORS["accent"],
                                   width=90, height=30, font_size=12)
        view_all_btn.grid(row=0, column=1, sticky="e")

        self.recent_list = ctk.CTkScrollableFrame(recent_card, fg_color="transparent",
                                                  height=240)
        self.recent_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 12))
        self.recent_list.grid_columnconfigure(0, weight=1)

        # Right column: quick actions + notifications hint
        right = ctk.CTkFrame(bottom, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.grid_columnconfigure(0, weight=1)

        # Quick actions
        actions = ctk.CTkFrame(right, fg_color=settings.COLORS["card_bg"],
                               corner_radius=14, border_width=1,
                               border_color=settings.COLORS["card_border"])
        actions.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        actions.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(actions, text="Quick Actions", font=font(16, "bold"),
                     text_color=settings.COLORS["text"]).grid(
            row=0, column=0, sticky="w", padx=18, pady=(16, 8))

        actions_list = [
            ("➕  Add Product", "Add a new product to the menu", lambda: self.app.open_add_product()),
            ("📦  Manage Products", "Edit or update your menu", lambda: self.app.show_view("products")),
            ("🧾  View Orders", "Review and update order statuses", lambda: self.app.show_view("orders")),
            ("👥  Customers", "See customer activity", lambda: self.app.show_view("customers")),
        ]
        for i, (title, sub, cmd) in enumerate(actions_list):
            row = ctk.CTkFrame(actions, fg_color="transparent")
            row.grid(row=i + 1, column=0, sticky="ew", padx=14, pady=4)
            row.grid_columnconfigure(0, weight=1)
            btn = make_button(row, title, command=cmd, border=True,
                              fg_color=settings.COLORS["accent"], width=150,
                              height=38, font_size=13)
            btn.grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(row, text=sub, font=font(12),
                         text_color=settings.COLORS["text_muted"]).grid(
                row=0, column=1, sticky="e", padx=8)
        actions.grid_rowconfigure(len(actions_list) + 1, weight=1)

        # Notifications hint card
        notif = ctk.CTkFrame(right, fg_color=settings.COLORS["card_bg"],
                             corner_radius=14, border_width=1,
                             border_color=settings.COLORS["card_border"])
        notif.grid(row=1, column=0, sticky="nsew")
        notif.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(notif, text="🔔  Live Orders", font=font(16, "bold"),
                     text_color=settings.COLORS["text"]).grid(
            row=0, column=0, sticky="w", padx=18, pady=(16, 6))
        notif_desc = ctk.CTkLabel(
            notif, text=("New orders will appear here in real time.\n"
                         "Demo mode: simulated orders arrive periodically.\n\n"
                         "When Supabase is connected, this becomes\n"
                         "live order notifications."),
            font=font(12), text_color=settings.COLORS["text_muted"],
            justify="left", anchor="w", wraplength=260)
        notif_desc.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 16))
        right.grid_rowconfigure(1, weight=1)

        self.refresh()

    def _go_orders(self):
        self.app.show_view("orders")

    def refresh(self):
        """Reload stats and recent orders from the database."""
        stats = db.dashboard_stats()
        mapping = {
            "Total Products": str(stats["total_products"]),
            "Total Orders": str(stats["total_orders"]),
            "Pending Orders": str(stats["pending_orders"]),
            "Completed Orders": str(stats["completed_orders"]),
            "Today's Sales": helpers.format_naira(stats["sales_today"]),
        }
        # Update the value labels inside the StatCards
        for label, value in mapping.items():
            self._set_stat_value(self.stat_widgets[label], value)

        # Recent orders
        for child in self.recent_list.winfo_children():
            child.destroy()

        orders = db.recent_orders(6)
        if not orders:
            ctk.CTkLabel(self.recent_list, text="No recent orders yet.",
                         text_color=settings.COLORS["text_muted"]).pack(pady=20)
            return

        for order in orders:
            row = ctk.CTkFrame(self.recent_list, fg_color=settings.COLORS["card_bg"],
                               corner_radius=10, border_width=1,
                               border_color=settings.COLORS["card_border"])
            row.pack(fill="x", pady=4)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=order.order_no, font=font(13, "bold"),
                         text_color=settings.COLORS["accent"]).grid(
                row=0, column=0, padx=(12, 10), pady=(10, 2), sticky="w")
            ctk.CTkLabel(row, text=order.customer_name, font=font(13),
                         text_color=settings.COLORS["text"]).grid(
                row=0, column=1, padx=(0, 6), pady=(10, 2), sticky="w")
            ctk.CTkLabel(row, text=order.total_naira, font=font(13, "semibold"),
                         text_color=settings.COLORS["text"]).grid(
                row=0, column=2, padx=6, pady=(10, 2), sticky="e")
            StatusBadge(row, order.status).grid(row=0, column=3, padx=(6, 12),
                                                pady=(6, 2))

            ctk.CTkLabel(row, text=helpers.format_date(order.created_at),
                         font=font(11), text_color=settings.COLORS["text_muted"]).grid(
                row=1, column=0, columnspan=4, sticky="w", padx=12, pady=(0, 8))

            # Make the row clickable to open the order
            row.bind("<Button-1>", lambda e, oid=order.id: self.app.show_order_detail(oid))

    def _set_stat_value(self, card, value):
        # StatCard stores value in the second label (the value). We saved it by
        # locating the label with the biggest font among children.
        for child in card.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                try:
                    if child.cget("font")[1] == 24:
                        child.configure(text=value)
                        return
                except Exception:
                    pass
