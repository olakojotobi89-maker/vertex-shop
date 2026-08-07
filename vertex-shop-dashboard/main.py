"""
Vertex Shop - Admin Dashboard (main entry point).

Run with:  python main.py

A Python/CustomTkinter desktop application for managing products, orders,
customers and categories for the Vertex Shop public web app.

DATA LAYER: Supabase (PostgreSQL + Storage + Realtime) is the ONLY backend.
            The dashboard authenticates an administrator via Supabase Auth
            and requires the account to carry the app_role=admin claim.
"""
import os
import sys

# Allow running from the project root regardless of cwd.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

import config.settings as settings
import database.supabase_client as supabase_auth
from views.widgets import Toast, font, make_button
from views.notifications import NotificationCenter, NotificationPanel
from views.login import AdminLoginView


class VertexShopApp(ctk.CTk):
    """Main application window with sidebar navigation."""

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode(settings.APPEARANCE_MODE)
        ctk.set_default_color_theme(settings.COLOR_THEME)

        self.title(settings.APP_TITLE)
        self.geometry("1280x780")
        self.minsize(1024, 680)

        # Views registry
        self.views = {}
        self.current_view = None
        self.logged_in = False

        # Notification center (Supabase Realtime driven)
        self.notifications = NotificationCenter(self)
        self.notifications.on_new_order = self._on_new_order_notification

        # Show the admin login gate first.
        self._build_login_gate()

        # Bind close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Auth gate
    # ------------------------------------------------------------------
    def _build_login_gate(self):
        self.login_view = AdminLoginView(self, self)
        self.login_view.pack(fill="both", expand=True)

    def on_admin_logged_in(self):
        """Called after a successful admin sign-in."""
        self.logged_in = True
        self.login_view.destroy()
        self._build_layout()
        self.notifications.start()
        self.show_view("dashboard")

    def _build_layout(self):
        self._build_sidebar()
        self._build_content_area()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=settings.COLORS["sidebar_bg"],
                                    width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo + brand
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(pady=(24, 20), padx=16, fill="x")
        brand.grid_columnconfigure(1, weight=1)

        logo_lbl = ctk.CTkLabel(brand, text="VS", width=40, height=40,
                                fg_color=settings.COLORS["primary"], corner_radius=10,
                                font=font(18, "bold"), text_color="#0F1720")
        logo_lbl.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        ctk.CTkLabel(brand, text="Vertex Shop", font=font(18, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(brand, text="Admin Dashboard", font=font(11),
                     text_color=settings.COLORS["text_muted"]).grid(row=1, column=1, sticky="w")

        # Nav label
        ctk.CTkLabel(self.sidebar, text="MAIN MENU", font=font(10, "semibold"),
                     text_color=settings.COLORS["text_muted"]).pack(anchor="w", padx=20, pady=(0, 6))

        # Nav buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "▦", "Dashboard"),
            ("products", "▤", "Products"),
            ("orders", "🧾", "Orders"),
            ("customers", "👥", "Customers"),
            ("categories", "🏷", "Categories"),
            ("settings", "⚙", "Settings"),
        ]
        for key, icon, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=f"{icon}   {label}", anchor="w", height=44,
                font=font(14), corner_radius=8,
                fg_color="transparent", hover_color=settings.COLORS["card_bg"],
                text_color=settings.COLORS["text_muted"],
                command=lambda k=key: self.show_view(k))
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[key] = btn

        # Notification bell
        ctk.CTkLabel(self.sidebar, text="NOTIFICATIONS", font=font(10, "semibold"),
                     text_color=settings.COLORS["text_muted"]).pack(anchor="w", padx=20, pady=(18, 6))
        bell_btn = ctk.CTkButton(self.sidebar, text="🔔   Notifications", anchor="w", height=44,
                                 font=font(14), corner_radius=8, fg_color="transparent",
                                 hover_color=settings.COLORS["card_bg"],
                                 text_color=settings.COLORS["text_muted"],
                                 command=self._open_notifications)
        bell_btn.pack(fill="x", padx=12, pady=3)

        # Logout at bottom
        logout_btn = ctk.CTkButton(
            self.sidebar, text="⏻   Logout", anchor="w", height=44,
            font=font(14), corner_radius=8, fg_color="transparent",
            hover_color=settings.COLORS["danger"],
            text_color=settings.COLORS["text_muted"], command=self._logout)
        logout_btn.pack(side="bottom", fill="x", padx=12, pady=(0, 18))

        # Version
        ctk.CTkLabel(self.sidebar, text=settings.APP_TITLE + "  v" + settings.APP_VERSION,
                     font=font(9), text_color=settings.COLORS["text_muted"]).pack(
            side="bottom", pady=(0, 8))

    def _build_content_area(self):
        self.toast = Toast(self)
        self.content = ctk.CTkFrame(self, fg_color=settings.COLORS["content_bg"], corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def show_view(self, name):
        # Instantiate lazily
        if name not in self.views:
            from views.dashboard import DashboardView
            from views.products import ProductsView
            from views.orders import OrdersView
            from views.customers import CustomersView
            from views.categories import CategoriesView
            from views.settings import SettingsView

            factories = {
                "dashboard": DashboardView,
                "products": ProductsView,
                "orders": OrdersView,
                "customers": CustomersView,
                "categories": CategoriesView,
                "settings": SettingsView,
            }
            cls = factories[name]
            view = cls(self.content, self)
            view.grid(row=0, column=0, sticky="nsew")
            self.views[name] = view

        # Hide previous
        if self.current_view and self.current_view in self.views:
            self.views[self.current_view].grid_forget()

        self.current_view = name
        self.views[name].grid(row=0, column=0, sticky="nsew")
        self.views[name].tkraise()

        # Highlight nav
        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.configure(fg_color=settings.COLORS["card_bg"], text_color=settings.COLORS["text"])
            else:
                btn.configure(fg_color="transparent", text_color=settings.COLORS["text_muted"])

        # Refresh views that need live data
        if name in ("dashboard", "products", "orders", "customers", "categories"):
            try:
                view = self.views[name]
                if hasattr(view, "refresh"):
                    view.refresh()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Product actions
    # ------------------------------------------------------------------
    def open_add_product(self):
        from views.add_product import AddProductView
        self._open_form_view(AddProductView, product=None)

    def open_edit_product(self, product_id):
        from database.database import db
        from views.add_product import AddProductView
        product = db.get_product(product_id)
        if product:
            self._open_form_view(AddProductView, product=product)

    def _open_form_view(self, view_cls, product):
        # Remove any existing add_product view
        if "add_product" in self.views:
            self.views["add_product"].destroy()
            del self.views["add_product"]
        if self.current_view and self.current_view in self.views:
            self.views[self.current_view].grid_forget()

        view = view_cls(self.content, self, product=product)
        view.grid(row=0, column=0, sticky="nsew")
        self.views["add_product"] = view
        self.current_view = "add_product"
        view.tkraise()

    # ------------------------------------------------------------------
    # Order detail
    # ------------------------------------------------------------------
    def show_order_detail(self, order_id):
        from views.orders import OrderDetailDialog
        OrderDetailDialog(self, order_id, on_change=self._refresh_current)

    def _refresh_current(self):
        if self.current_view and self.current_view in self.views:
            try:
                self.views[self.current_view].refresh()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    def _open_notifications(self):
        NotificationPanel(self)

    def _on_new_order_notification(self, order):
        # Called from the notification thread. Use `after` to be thread-safe.
        self.after(0, lambda: self._show_new_order_toast(order))

    def _show_new_order_toast(self, order):
        self.toast.show(f"🔔 NEW ORDER {order.order_no} · {order.customer_name} · {order.total_naira}",
                        duration=5000, color=settings.COLORS["accent"])
        # Refresh dashboard/orders if visible
        self._refresh_current()

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    def toast_global(self, message, color="#22C55E"):
        self.toast.show(message, color=color)

    def _logout(self):
        from views.widgets import confirm_dialog
        if confirm_dialog(self, "Log out of the admin dashboard?",
                          title="Logout", confirm_text="Logout", accent=settings.COLORS["danger"]):
            supabase_auth.sign_out_admin()
            self.notifications.stop()
            self.destroy()

    def _on_close(self):
        self.notifications.stop()
        self.destroy()


def main():
    app = VertexShopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
</content>
