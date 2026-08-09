"""
Notification Center and Panel.

The NotificationCenter connects to Supabase Realtime (using an async client
in a separate thread) to listen for new orders and triggers a callback.
The NotificationPanel is a UI component
that displays a list of recent notifications.
"""
import time
import threading
import asyncio
from datetime import datetime

import customtkinter as ctk

import config.settings as settings
from database.database import db
from database.supabase_client import (
    get_supabase_client,
    get_supabase_async_client,
    get_admin_access_token,
)
from views.widgets import font, make_button


class NotificationCenter:
    """Listens to Supabase Realtime for new orders."""
    def __init__(self, app):
        self.app = app
        self.on_new_order = None    # callable(order) -> None
        self.subscription = None
        self._realtime_thread = None # Thread for async event loop
        self._realtime_loop = None   # Event loop for async operations

    def start(self):
        """Subscribe to new order inserts on the 'orders' table."""
        # Get the async client for Realtime
        try:
            async_client = get_supabase_async_client()
        except RuntimeError as e:
            print(f"Realtime disabled: Failed to get async Supabase client: {e}")
            return

        def on_new_order_callback(payload):
            try:
                order_id = payload.get("new", {}).get("id")
                if not order_id:
                    return
                # Fetch the full order details from the database
                # This uses the synchronous db client, which is safe from the async thread.
                order = db.get_order(order_id)
                if order and self.on_new_order:
                    # GUI update must be on the main thread
                    self.app.after(0, lambda: self.on_new_order(order))
            except Exception as e:
                print(f"Error processing realtime order notification: {e}")
                import traceback; traceback.print_exc()

        # Start a new thread for the async event loop
        self._realtime_thread = threading.Thread(
            target=self._run_realtime_loop, args=(async_client, on_new_order_callback), daemon=True
        )
        self._realtime_thread.start()
        print("Realtime thread started.")

    async def _subscribe_to_realtime(self, async_client, on_new_order_callback):
        """Actual async subscription logic."""
        try:
            # Authenticate the realtime socket as the signed-in admin so RLS
            # (orders-admin-read) permits postgres_changes events. Without
            # this, the socket connects with the anon key and silently
            # receives zero rows.
            token = get_admin_access_token()
            if token:
                await async_client.realtime.set_auth(token)
                print("[Realtime] Authenticated realtime socket with admin session.")
            else:
                print("[Realtime] No admin access token available; "
                      "realtime subscription will use the anon key and may "
                      "receive no rows under RLS.")

            self.subscription = (
                async_client.realtime.channel("public:orders")
                .on("postgres_changes", {"event": "INSERT", "schema": "public", "table": "orders"}, on_new_order_callback)
                .subscribe()
            )
            print("Subscribed to Supabase Realtime for new orders.")
            # Keep the event loop running to process Realtime messages
            while True:
                await asyncio.sleep(1) # Keep the task alive
        except Exception as e:
            print(f"Failed to subscribe to Supabase Realtime: {e}")
            import traceback; traceback.print_exc()

    def _run_realtime_loop(self, async_client, on_new_order_callback):
        """Runs the asyncio event loop in a separate thread."""
        self._realtime_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._realtime_loop)
        self._realtime_loop.run_until_complete(self._subscribe_to_realtime(async_client, on_new_order_callback))
        self._realtime_loop.close()
        print("Realtime event loop closed.")

    def stop(self):
        """Unsubscribe from Realtime and stop the async event loop."""
        if self.subscription and self._realtime_loop and self._realtime_loop.is_running():
            try:
                # Unsubscribe needs to be run in the async loop
                asyncio.run_coroutine_threadsafe(self.subscription.unsubscribe(), self._realtime_loop)
                print("Unsubscribed from Supabase Realtime.")
            except Exception as e:
                print(f"Error unsubscribing from Realtime: {e}")
                import traceback; traceback.print_exc()
            self.subscription = None

        # Stop the event loop if it's running
        if self._realtime_loop and self._realtime_loop.is_running():
            self._realtime_loop.call_soon_threadsafe(self._realtime_loop.stop)
            # Wait for the thread to finish if it's still alive
            if self._realtime_thread and self._realtime_thread.is_alive():
                self._realtime_thread.join(timeout=5) # Give it some time to shut down
            print("Realtime event loop stopped.")
        self._realtime_loop = None
        self._realtime_thread = None


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