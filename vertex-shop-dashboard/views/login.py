"""
Admin Login view.

A full-window gate shown before the main dashboard. The administrator enters
their Supabase Auth email + password. The app authenticates via Supabase and
only proceeds if the account carries the `app_role=admin` claim. The password
is never stored.
"""
import customtkinter as ctk

import config.settings as settings
import database.supabase_client as supabase_auth
from database.supabase_client import sign_in_admin
from views.widgets import font, make_button


class AdminLoginView(ctk.CTkFrame):
    """Full-window login screen."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=settings.COLORS["content_bg"], **kwargs)
        self.app = app
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self, fg_color=settings.COLORS["card_bg"], corner_radius=16,
                            border_width=1, border_color=settings.COLORS["card_border"])
        card.grid(row=0, column=0)

        # Brand
        logo = ctk.CTkLabel(card, text="VS", width=64, height=64,
                            fg_color=settings.COLORS["primary"], corner_radius=16,
                            font=font(26, "bold"), text_color="#0F1720")
        logo.pack(pady=(40, 12))
        ctk.CTkLabel(card, text="Vertex Shop", font=font(22, "bold"),
                     text_color=settings.COLORS["text"]).pack()
        ctk.CTkLabel(card, text="Admin Dashboard", font=font(13),
                     text_color=settings.COLORS["text_muted"]).pack(pady=(2, 24))

        # Email
        ctk.CTkLabel(card, text="Admin Email", font=font(12, "semibold"),
                     text_color=settings.COLORS["text_muted"], anchor="w").pack(padx=40, anchor="w")
        self.email_entry = ctk.CTkEntry(card, placeholder_text="admin@vertexshop.com",
                                        font=font(14), width=320, height=42,
                                        fg_color=settings.COLORS["card_border"], border_width=0,
                                        text_color=settings.COLORS["text"])
        self.email_entry.pack(padx=40, pady=(6, 14))

        # Password
        ctk.CTkLabel(card, text="Password", font=font(12, "semibold"),
                     text_color=settings.COLORS["text_muted"], anchor="w").pack(padx=40, anchor="w")
        self.password_entry = ctk.CTkEntry(card, placeholder_text="••••••••",
                                           show="•", font=font(14), width=320, height=42,
                                           fg_color=settings.COLORS["card_border"], border_width=0,
                                           text_color=settings.COLORS["text"])
        self.password_entry.pack(padx=40, pady=(6, 6))
        self.password_entry.bind("<Return>", lambda e: self._login())

        # Error
        self.error_label = ctk.CTkLabel(card, text="", font=font(12),
                                        text_color=settings.COLORS["danger"])
        self.error_label.pack(pady=(10, 0))

        # Button
        self.login_btn = make_button(card, "Sign In", command=self._login,
                                     width=320, height=44, font_size=15)
        self.login_btn.pack(padx=40, pady=(16, 8))

        # Connection check
        self.conn_label = ctk.CTkLabel(card, text="", font=font(11),
                                       text_color=settings.COLORS["text_muted"])
        self.conn_label.pack(pady=(4, 30))

        # Pre-check Supabase connectivity
        self._check_connection()

    def _check_connection(self):
        try:
            supabase_auth.get_supabase_client()
            self.conn_label.configure(text="✓ Supabase reachable", text_color=settings.COLORS["primary"])
        except Exception as exc:
            self.conn_label.configure(
                text=f"Supabase connection failed. Please check your configuration.\n{exc}",
                text_color=settings.COLORS["danger"])

    def _login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        if not email or not password:
            self.error_label.configure(text="Please enter your admin email and password.")
            return

        self.login_btn.configure(state="disabled", text="Signing in…")
        self.error_label.configure(text="")
        try:
            sign_in_admin(email, password)
        except Exception as exc:
            self.error_label.configure(text=str(exc))
            self.login_btn.configure(state="normal", text="Sign In")
            return
        self.login_btn.configure(state="normal", text="Sign In")
        self.app.on_admin_logged_in()
