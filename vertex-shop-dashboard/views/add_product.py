"""
Add / Edit Product form view.

Used both to create a new product and to edit an existing one.
Includes a file picker for selecting a product image from the computer.

When Supabase is configured, the selected image is uploaded to the
`product-images` storage bucket and the returned public URL is stored on
the product. Otherwise the image is copied to the local uploads folder.
"""
import customtkinter as ctk
from tkinter import filedialog

import config.settings as settings
from database.database import db
from database.supabase_client import get_supabase_client
from models.product import Product
from utils import validators, helpers
from views.widgets import font, make_button, PageHeader, Toast


class AddProductView(ctk.CTkFrame):
    def __init__(self, parent, app, product: Product = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.product = product  # None => add mode; else edit mode
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        is_edit = product is not None
        action_btn = make_button(
            self, "← Back", command=lambda: self.app.show_view("products"),
            border=True, fg_color=settings.COLORS["accent"], width=100, height=34, font_size=12)

        header = PageHeader(
            self,
            ("Edit Product" if is_edit else "Add Product"),
            subtitle=("Update the details of this product on your menu."
                      if is_edit else "Create a new product and add it to your menu."),
            action_button=action_btn,
        )
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        # Form container
        form_card = ctk.CTkFrame(self, fg_color=settings.COLORS["card_bg"],
                                 corner_radius=14, border_width=1,
                                 border_color=settings.COLORS["card_border"])
        form_card.grid(row=1, column=0, sticky="nesw", padx=24, pady=(0, 12))
        form_card.grid_columnconfigure(0, weight=1, uniform="f")
        form_card.grid_columnconfigure(1, weight=1, uniform="f")

        self.toast = Toast(self)

        # Keep references to entry widgets
        self.name_entry = self._label_and_entry(form_card, "Product Name", 0, "e.g. Chocolate Cake")
        self.desc_text = self._label_and_text(form_card, "Description", 1, "e.g. Fresh homemade chocolate cake")
        self.category_menu = self._label_and_category(form_card, "Category", 2)
        self.price_entry = self._label_and_entry(form_card, "Price (₦)", 3, "e.g. 8000")

        # Image selection
        img_lbl = ctk.CTkLabel(form_card, text="Product Image", font=font(13, "semibold"),
                               text_color=settings.COLORS["text"], anchor="w")
        img_lbl.grid(row=4, column=0, padx=(24, 8), pady=(14, 6), sticky="w")
        self.image_path = ""
        self.image_preview = ctk.CTkLabel(form_card, text="No image selected", width=180,
                                          height=120, fg_color=settings.COLORS["card_border"],
                                          corner_radius=10, text_color=settings.COLORS["text_muted"])
        self.image_preview.grid(row=5, column=0, padx=(24, 8), pady=(0, 8), sticky="w")
        choose_btn = make_button(form_card, "Choose Image", command=self._choose_image,
                                 border=True, fg_color=settings.COLORS["accent"],
                                 width=140, height=34, font_size=12)
        choose_btn.grid(row=5, column=1, padx=8, pady=(0, 8), sticky="w")

        # Availability
        avail_lbl = ctk.CTkLabel(form_card, text="Availability", font=font(13, "semibold"),
                                 text_color=settings.COLORS["text"], anchor="w")
        avail_lbl.grid(row=4, column=1, padx=(8, 24), pady=(14, 6), sticky="w")
        self.available_var = ctk.StringVar(value="Available")
        avail_menu = ctk.CTkOptionMenu(
            form_card, variable=self.available_var, values=["Available", "Unavailable"],
            font=font(13), dropdown_font=font(13), fg_color=settings.COLORS["card_border"],
            button_color=settings.COLORS["card_border"], button_hover_color=settings.COLORS["card_border"],
            text_color=settings.COLORS["text"], width=200, height=38)
        avail_menu.grid(row=5, column=1, padx=8, pady=(0, 8), sticky="w")

        # Error label
        self.error_label = ctk.CTkLabel(self, text="", font=font(12),
                                        text_color=settings.COLORS["danger"])
        self.error_label.grid(row=2, column=0, padx=24, sticky="w")

        # Submit button
        submit = make_button(self, ("Save Changes" if is_edit else "ADD PRODUCT"),
                             command=self._submit, width=220, height=44, font_size=15)
        submit.grid(row=3, column=0, padx=24, pady=(8, 24), sticky="w")

        # Pre-fill if editing
        if is_edit:
            self._populate(product)

    # ------------------------------------------------------------------
    # Form building helpers
    # ------------------------------------------------------------------
    def _label_and_entry(self, parent, label, row, placeholder):
        lbl = ctk.CTkLabel(parent, text=label, font=font(13, "semibold"),
                           text_color=settings.COLORS["text"], anchor="w")
        lbl.grid(row=row, column=0, padx=(24, 8), pady=(14, 0), sticky="w")
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, font=font(13),
                             fg_color=settings.COLORS["card_border"], border_width=0,
                             height=40, text_color=settings.COLORS["text"])
        entry.grid(row=row + 1, column=0, padx=(24, 8), pady=(6, 4), sticky="ew")
        return entry

    def _label_and_text(self, parent, label, row, placeholder):
        lbl = ctk.CTkLabel(parent, text=label, font=font(13, "semibold"),
                           text_color=settings.COLORS["text"], anchor="w")
        lbl.grid(row=row, column=0, padx=(24, 8), pady=(10, 0), sticky="w")
        text = ctk.CTkTextbox(parent, height=70, font=font(13),
                              fg_color=settings.COLORS["card_border"], border_width=0,
                              text_color=settings.COLORS["text"])
        text.grid(row=row + 1, column=0, columnspan=2, padx=(24, 24), pady=(6, 4), sticky="ew")
        text.insert("1.0", placeholder)  # placeholder-ish
        text.bind("<FocusIn>", lambda e: self._clear_placeholder(e, text, placeholder))
        return text

    def _clear_placeholder(self, event, widget, placeholder):
        if widget.get("1.0", "end-1c").strip() == placeholder:
            widget.delete("1.0", "end")

    def _label_and_category(self, parent, label, row):
        lbl = ctk.CTkLabel(parent, text=label, font=font(13, "semibold"),
                           text_color=settings.COLORS["text"], anchor="w")
        lbl.grid(row=row, column=0, padx=(24, 8), pady=(10, 0), sticky="w")
        categories = db.get_category_names()
        var = ctk.StringVar(value=categories[0] if categories else "Meals")
        menu = ctk.CTkOptionMenu(
            parent, variable=var, values=categories if categories else ["Meals"],
            font=font(13), dropdown_font=font(13), fg_color=settings.COLORS["card_border"],
            button_color=settings.COLORS["card_border"], button_hover_color=settings.COLORS["card_border"],
            text_color=settings.COLORS["text"], width=200, height=38)
        menu.grid(row=row + 1, column=0, padx=(24, 8), pady=(6, 4), sticky="w")
        return var

    # ------------------------------------------------------------------
    def _choose_image(self):
        path = filedialog.askopenfilename(
            title="Select Product Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.webp *.bmp"), ("All files", "*.*")],
        )
        if path:
            self.image_path = path
            img = helpers.load_image_pil(path, (180, 120))
            if img:
                from customtkinter import CTkImage
                self.image_preview.configure(image=CTkImage(light_image=img, dark_image=img),
                                             text="", width=180, height=120)
            else:
                self.image_preview.configure(text="Unable to load image")
            self.toast.show("Image selected", color=settings.COLORS["accent"])

    def _populate(self, product: Product):
        self.name_entry.insert(0, product.name)
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", product.description)
        self.category_menu.set(product.category)
        self.price_entry.insert(0, str(int(product.price)))
        self.available_var.set("Available" if product.available else "Unavailable")
        if product.image:
            self.image_path = product.image
            img = helpers.load_image_pil(helpers.resolve_image_path(product.image), (180, 120))
            if img:
                from customtkinter import CTkImage
                self.image_preview.configure(image=CTkImage(light_image=img, dark_image=img),
                                             text="", width=180, height=120)

    # ------------------------------------------------------------------
    def _get_desc(self):
        # The textbox may still contain the placeholder text.
        val = self.desc_text.get("1.0", "end-1c").strip()
        if val == "e.g. Fresh homemade chocolate cake":
            return ""
        return val

    def _upload_image_to_supabase(self, client, file_path: str) -> str:
        """Upload an image to the Supabase 'product-images' bucket and return
        the public URL. Requires the bucket + RLS policy from the SQL migration."""
        import uuid
        from pathlib import Path

        src = Path(file_path)
        if not src.exists():
            return ""
        ext = src.suffix.lower() or ".png"
        object_name = f"{uuid.uuid4().hex}{ext}"

        try:
            with open(src, "rb") as f:
                data = f.read()
        except Exception:
            return ""

        try:
            client.storage.from_("product-images").upload(object_name, data)
        except Exception as exc:
            print("Supabase image upload failed:", exc)
            return ""

        # Build the public URL.
        try:
            res = client.storage.from_("product-images").get_public_url(object_name)
            if res:
                return res
        except Exception:
            pass
        base = settings.SUPABASE_URL.rstrip("/")
        return f"{base}/storage/v1/object/public/product-images/{object_name}"

    def _submit(self):
        name = self.name_entry.get().strip()
        desc = self._get_desc()
        category = self.category_menu.get()
        price = self.price_entry.get().strip()

        # Validate
        errors = []
        ok, msg = validators.validate_product_name(name)
        if not ok:
            errors.append(msg)
        ok, msg = validators.validate_description(desc)
        if not ok:
            errors.append(msg)
        ok, msg = validators.validate_category(category)
        if not ok:
            errors.append(msg)
        ok, msg = validators.validate_price(price)
        if not ok:
            errors.append(msg)

        if errors:
            self.error_label.configure(text="  •  ".join(errors))
            return
        self.error_label.configure(text="")

        price_val = float(price.replace(",", ""))
        available = self.available_var.get() == "Available"

        # Store image. If Supabase is active, upload to the product-images
        # bucket and store the returned public URL. Otherwise copy to the
        # local uploads folder.
        stored_image = ""
        if self.image_path:
            client = get_supabase_client()
            if client is not None:
                # Edit without re-choosing an image keeps the existing one.
                if self.product and self.image_path == self.product.image:
                    stored_image = self.image_path
                else:
                    stored_image = self._upload_image_to_supabase(client, self.image_path)
            else:
                if self.product and self.image_path.startswith(str(settings.UPLOAD_DIR)):
                    stored_image = self.image_path
                else:
                    stored_image = helpers.copy_image_to_upload(self.image_path)

        if self.product:  # edit mode
            db.update_product(
                self.product.id, name, desc, category, price_val,
                image=stored_image if stored_image else None,
                available=available,
            )
            self.app.toast_global(f"Product '{name}' updated")
        else:  # add mode
            db.add_product(name, desc, category, price_val,
                           image=stored_image, available=available)
            self.app.toast_global(f"Product '{name}' added")

        self.app.show_view("products")
