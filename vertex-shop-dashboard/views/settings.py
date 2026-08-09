"""
Settings view.

App settings, theme, and Supabase connection status.
No secret keys are stored here — Supabase credentials come from
environment variables when integrated.
"""
import customtkinter as ctk

import config.settings as settings
from database.database import db
from views.widgets import PageHeader, make_button, font


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = PageHeader(self, "Settings",
                            subtitle="Application preferences and data connection.")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        # ----- Appearance card -----
        appear = ctk.CTkFrame(self, fg_color=settings.COLORS["card_bg"], corner_radius=14,
                              border_width=1, border_color=settings.COLORS["card_border"])
        appear.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))
        appear.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(appear, text="Appearance", font=font(16, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(16, 8))

        ctk.CTkLabel(appear, text="Theme", font=font(13),
                     text_color=settings.COLORS["text_muted"]).grid(row=1, column=0, sticky="w", padx=18, pady=6)
        self.theme_var = ctk.StringVar(value=settings.APPEARANCE_MODE)
        theme_menu = ctk.CTkOptionMenu(
            appear, variable=self.theme_var, values=["dark", "light", "system"],
            command=self._change_theme, font=font(13), dropdown_font=font(13),
            fg_color=settings.COLORS["card_border"], button_color=settings.COLORS["card_border"],
            button_hover_color=settings.COLORS["card_border"], text_color=settings.COLORS["text"],
            width=160, height=34)
        theme_menu.grid(row=1, column=1, sticky="w", padx=18, pady=6)

        # ----- Active backend detection -----
        is_supabase = bool(getattr(db, "available", False))
        backend_name = "Supabase (PostgreSQL)" if is_supabase else "Supabase (not connected)"
        backend_color = settings.COLORS["primary"] if is_supabase else settings.COLORS["warning"]

        # ----- Data & Storage card -----
        data_card = ctk.CTkFrame(self, fg_color=settings.COLORS["card_bg"], corner_radius=14,
                                 border_width=1, border_color=settings.COLORS["card_border"])
        data_card.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))
        data_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(data_card, text="Data & Storage", font=font(16, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 8))

        ctk.CTkLabel(data_card, text="Backend", font=font(13),
                     text_color=settings.COLORS["text_muted"]).grid(row=1, column=0, sticky="w", padx=18, pady=4)
        ctk.CTkLabel(data_card, text=backend_name,
                     font=font(13), text_color=backend_color).grid(row=1, column=1, sticky="w", padx=18, pady=4)

        ctk.CTkLabel(data_card, text="Connection", font=font(13),
                     text_color=settings.COLORS["text_muted"]).grid(row=2, column=0, sticky="w", padx=18, pady=4)
        conn_text = settings.SUPABASE_URL if is_supabase else "Supabase not connected"
        conn_color = settings.COLORS["accent"] if is_supabase else settings.COLORS["text_muted"]
        ctk.CTkLabel(data_card, text=conn_text, font=font(12),
                     text_color=conn_color, anchor="w").grid(row=2, column=1, sticky="w", padx=18, pady=4)

        ctk.CTkLabel(data_card, text="Statistics", font=font(13),
                     text_color=settings.COLORS["text_muted"]).grid(row=3, column=0, sticky="w", padx=18, pady=4)
        try:
            stats = db.dashboard_stats()
            stat_text = (f"{stats['total_products']} products · {stats['total_orders']} orders · "
                         f"{len(db.get_customers())} customers")
        except Exception:
            stat_text = "Unable to load statistics"
        ctk.CTkLabel(data_card, text=stat_text,
                     font=font(13), text_color=settings.COLORS["text"]).grid(row=3, column=1, sticky="w", padx=18, pady=4)

        # ----- Supabase status card -----
        sup_card = ctk.CTkFrame(self, fg_color=settings.COLORS["card_bg"], corner_radius=14,
                                border_width=1, border_color=settings.COLORS["card_border"])
        sup_card.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 20))
        sup_card.grid_columnconfigure(0, weight=1)
        status_text = ("✔ Connected to Supabase" if is_supabase
                       else "Supabase not connected — check your .env configuration")
        status_color = settings.COLORS["primary"] if is_supabase else settings.COLORS["warning"]
        ctk.CTkLabel(sup_card, text="Supabase Integration", font=font(16, "bold"),
                     text_color=settings.COLORS["text"]).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 6))
        ctk.CTkLabel(sup_card, text=status_text, font=font(13, "semibold"),
                     text_color=status_color).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 4))
        ctk.CTkLabel(sup_card, text=(
            "Products, categories, orders and customers sync with the public web app.\n"
            "Sensitive credentials are read from environment variables — never hard-coded.\n"
            "Run the attached supabase_migration.sql in the Supabase SQL Editor to enable\n"
            "RLS policies and the product-images storage bucket."),
            font=font(12), text_color=settings.COLORS["text_muted"], justify="left", anchor="w").grid(
            row=2, column=0, sticky="w", padx=18, pady=(0, 16))

    def _change_theme(self, choice):
        ctk.set_appearance_mode(choice)
