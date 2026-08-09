"""
Products management view.

Lists all products in a table with search + category filter, and provides
Edit / Delete actions for each row.
"""
import customtkinter as ctk

import config.settings as settings
from database.database import db
from utils import helpers
from views.widgets import (
    PageHeader, SearchBar, StatusBadge, make_button, font, confirm_dialog,
)


class ProductsView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        add_btn = make_button(self, "+  Add Product",
                              command=lambda: self.app.open_add_product(),
                              width=140, height=38, font_size=14)
        header = PageHeader(self, "Products",
                            subtitle="Manage your menu — add, edit and update availability.",
                            action_button=add_btn)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        # Filter bar
        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        filters.grid_columnconfigure(0, weight=1)

        self.search = SearchBar(filters, placeholder="Search products...",
                                command=self._on_search, width=320)
        self.search.grid(row=0, column=0, sticky="w")
        
        self.category_filter_var = ctk.StringVar(value="All")
        self.category_filter_menu = ctk.CTkOptionMenu(filters, variable=self.category_filter_var, values=["All"],
            command=lambda _: self.refresh(), font=font(13), dropdown_font=font(13),
            fg_color=settings.COLORS["card_bg"], button_color=settings.COLORS["card_border"],
            button_hover_color=settings.COLORS["card_border"], text_color=settings.COLORS["text"],
            width=160, height=36)
        self.category_filter_menu.grid(row=0, column=1, padx=(8, 0), sticky="e")

        # Table container (scrollable)
        self.table = ctk.CTkScrollableFrame(self, fg_color=settings.COLORS["card_bg"],
                                            corner_radius=14, border_width=1,
                                            border_color=settings.COLORS["card_border"])
        self.table.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.table.grid_columnconfigure(0, weight=1)

        self.refresh()

    def _on_search(self, text):
        # No need to refresh categories on search, only filter products
        self.refresh()

    def refresh(self):
        # Update category filter options
        categories = ["All"] + db.get_category_names()
        self.category_filter_menu.configure(values=categories)
        # Clear table
        for child in self.table.winfo_children():
            child.destroy()

        search_text = self.search.get().strip()
        category = self.category_filter.get()
        products = db.get_products(search=search_text, category=category)
        
        self.search.set_result(f"{len(products)} product{'s' if len(products) != 1 else ''}")

        if not products:
            ctk.CTkLabel(self.table, text="No products found.", font=font(14),
                         text_color=settings.COLORS["text_muted"]).pack(pady=40)
            return

        # Header row
        header = ctk.CTkFrame(self.table, fg_color=settings.COLORS["card_border"],
                              corner_radius=8, height=40)
        header.pack(fill="x", pady=(0, 6))
        header.pack_propagate(False)
        cols = ["Image", "Product", "Category", "Price", "Availability", "Date Added", "Actions"]
        widths = [0.10, 0.24, 0.14, 0.12, 0.12, 0.14, 0.14]
        for i, (col, w) in enumerate(zip(cols, widths)):
            ctk.CTkLabel(header, text=col, font=font(12, "semibold"),
                         text_color=settings.COLORS["text_muted"],
                         width=int(560 * w), anchor="w").pack(side="left", padx=6, fill="x", expand=True)

        # Product rows
        for p in products:
            row = ctk.CTkFrame(self.table, fg_color=settings.COLORS["card_bg"],
                               corner_radius=8, height=70)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)

            # Image (local path or Supabase Storage URL)
            img = helpers.load_product_image(p.image, (44, 44)) or helpers.load_placeholder_icon((44, 44))
            from customtkinter import CTkImage
            img_lbl = ctk.CTkLabel(row, text="", image=CTkImage(light_image=img, dark_image=img),
                                   fg_color=settings.COLORS["card_border"], corner_radius=6,
                                   width=56, height=56)
            img_lbl.pack(side="left", padx=(10, 6), pady=6)

            ctk.CTkLabel(row, text=p.name, font=font(13, "semibold"),
                         text_color=settings.COLORS["text"], width=130, anchor="w").pack(side="left", padx=6, fill="x", expand=True)
            ctk.CTkLabel(row, text=p.category, font=font(12),
                         text_color=settings.COLORS["text_muted"], width=80, anchor="w").pack(side="left", padx=6, fill="x", expand=True)
            ctk.CTkLabel(row, text=p.price_naira, font=font(13, "semibold"),
                         text_color=settings.COLORS["text"], width=70, anchor="w").pack(side="left", padx=6, fill="x", expand=True)

            # Availability badge
            avail_frame = ctk.CTkFrame(row, fg_color="transparent", width=80)
            avail_frame.pack(side="left", padx=6)
            StatusBadge(avail_frame, p.availability_label).pack()

            ctk.CTkLabel(row, text=helpers.format_date_short(p.created_at), font=font(11),
                         text_color=settings.COLORS["text_muted"], width=80, anchor="w").pack(side="left", padx=6, fill="x", expand=True)

            # Actions
            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.pack(side="left", padx=(6, 10))
            make_button(actions, "Edit", command=lambda pid=p.id: self._edit(pid),
                        border=True, fg_color=settings.COLORS["accent"], width=70, height=28, font_size=11).pack(side="left", padx=2)
            make_button(actions, "Delete", command=lambda pid=p.id: self._delete(pid),
                        fg_color=settings.COLORS["danger"], width=70, height=28, font_size=11).pack(side="left", padx=2)

    def _edit(self, product_id):
        self.app.open_edit_product(product_id)

    def _delete(self, product_id):
        product = db.get_product(product_id)
        if not product:
            return
        confirmed = confirm_dialog(
            self, f"Are you sure you want to delete '{product.name}'?",
            title="Delete Product?", confirm_text="Delete")
        if confirmed:
            db.delete_product(product_id)
            self.app.toast_global(f"Product '{product.name}' deleted", color=settings.COLORS["danger"])
            self.refresh()
