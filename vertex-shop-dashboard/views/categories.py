"""
Categories management view.

Allows the administrator to add, edit, and delete product categories.
"""
import customtkinter as ctk

import config.settings as settings
from database.database import db
from utils import validators
from views.widgets import (
    PageHeader, SearchBar, make_button, font, confirm_dialog,
)


class CategoriesView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        add_btn = make_button(self, "+  Add Category", command=self._add_category,
                              width=150, height=38, font_size=14)
        header = PageHeader(self, "Categories",
                            subtitle="Organise your menu into categories.",
                            action_button=add_btn)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        self.search = SearchBar(self, placeholder="Search categories...",
                                command=self._on_search, width=320)
        self.search.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 10))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=settings.COLORS["card_bg"],
                                                 corner_radius=14, border_width=1,
                                                 border_color=settings.COLORS["card_border"])
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.list_frame.grid_columnconfigure(0, weight=1)

        self.refresh()

    def _on_search(self, text):
        self.refresh()

    def refresh(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        search_text = self.search.get().strip().lower()
        categories = db.get_categories()
        if search_text:
            categories = [c for c in categories if search_text in c["name"].lower()]

        if not categories:
            ctk.CTkLabel(self.list_frame, text="No categories found.", font=font(14),
                         text_color=settings.COLORS["text_muted"]).pack(pady=40)
            return

        for cat in categories:
            row = ctk.CTkFrame(self.list_frame, fg_color=settings.COLORS["card_bg"],
                               corner_radius=10, height=54)
            row.pack(fill="x", pady=4)
            row.pack_propagate(False)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(row, text="🏷  " + cat["name"], font=font(14, "semibold"),
                         text_color=settings.COLORS["text"]).grid(row=0, column=0, sticky="w", padx=16)

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.grid(row=0, column=1, sticky="e", padx=10)
            make_button(actions, "Edit", command=lambda cid=cat["id"]: self._edit_category(cid),
                        border=True, fg_color=settings.COLORS["accent"], width=70, height=28, font_size=11).pack(side="left", padx=2)
            make_button(actions, "Delete", command=lambda cid=cat["id"]: self._delete_category(cid),
                        fg_color=settings.COLORS["danger"], width=70, height=28, font_size=11).pack(side="left", padx=2)

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------
    def _add_category(self):
        self._category_dialog(mode="add")

    def _edit_category(self, cat_id):
        self._category_dialog(mode="edit", cat_id=cat_id)

    def _category_dialog(self, mode="add", cat_id=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Category" if mode == "add" else "Edit Category")
        dialog.geometry("380x220")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.columnconfigure(0, weight=1)

        ctk.CTkLabel(dialog, text="Category Name", font=font(13, "semibold"),
                     text_color=settings.COLORS["text"]).pack(pady=(24, 8), padx=24, anchor="w")

        existing = None
        if mode == "edit":
            existing = next((c for c in db.get_categories() if c["id"] == cat_id), None)

        entry = ctk.CTkEntry(dialog, font=font(14), fg_color=settings.COLORS["card_border"],
                             border_width=0, height=40, text_color=settings.COLORS["text"])
        entry.pack(padx=24, fill="x")
        if existing:
            entry.insert(0, existing["name"])

        error = ctk.CTkLabel(dialog, text="", font=font(12), text_color=settings.COLORS["danger"])
        error.pack(pady=(6, 0), padx=24, anchor="w")

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=(18, 22))

        def on_save():
            name = entry.get().strip()
            ok, msg = validators.validate_category_name(name)
            if not ok:
                error.configure(text=msg)
                return
            names = [c["name"].lower() for c in db.get_categories() if c["id"] != cat_id]
            if name.lower() in names:
                error.configure(text="That category already exists.")
                return
            if mode == "add":
                db.add_category(name)
                self.app.toast_global(f"Category '{name}' added")
            else:
                db.update_category(cat_id, name)
                self.app.toast_global(f"Category renamed to '{name}'")
            dialog.destroy()
            self.refresh()

        make_button(btn_row, "Cancel", command=dialog.destroy,
                    fg_color=settings.COLORS["card_border"], text_color=settings.COLORS["text"],
                    width=110).pack(side="left", padx=8)
        make_button(btn_row, "Save", command=on_save, width=110).pack(side="left", padx=8)

    def _delete_category(self, cat_id):
        cat = next((c for c in db.get_categories() if c["id"] == cat_id), None)
        if not cat:
            return
        confirmed = confirm_dialog(self, f"Delete category '{cat['name']}'? Products already using this category will keep their label.",
                                   title="Delete Category?")
        if confirmed:
            db.delete_category(cat_id)
            self.app.toast_global(f"Category '{cat['name']}' deleted", color=settings.COLORS["danger"])
            self.refresh()
