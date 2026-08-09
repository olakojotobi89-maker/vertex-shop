"""
Add / Edit Product form view.

Used both to create a new product and to edit an existing one.
Includes a file picker for selecting a product image from the computer.

When Supabase is configured, the selected image is uploaded to the
`product-images` storage bucket and the returned public URL is stored on
the product. Otherwise the image is copied to the local uploads folder.
"""
import threading
from pathlib import Path
import traceback
import customtkinter as ctk
from tkinter import filedialog

import config.settings as settings
from database.database import db
from database.supabase_client import get_supabase_client
from models.product import Product
from database import supabase_storage
from utils import validators, helpers
from views.widgets import font, make_button, PageHeader, Toast, NairaEntry


class AddProductView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.product: Product = None  # Will be set by configure_for_add/edit
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        action_btn = make_button(
            self, "← Back", command=lambda: self.app.show_view("products"),
            border=True, fg_color=settings.COLORS["accent"], width=100, height=34, font_size=12)

        self.header = PageHeader(
            self,
            "Product Form", # Generic title, will be updated by configure_for_add/edit
            subtitle="Manage product details.", # Generic subtitle
            action_button=action_btn,
        )
        self.header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        # Form container
        form_card = ctk.CTkFrame(self, fg_color=settings.COLORS["card_bg"],
                                 corner_radius=14, border_width=1,
                                 border_color=settings.COLORS["card_border"])
        form_card.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        form_card.grid_columnconfigure((0, 1), weight=1, uniform="form_cols")
        form_card.grid_rowconfigure(5, weight=1) # Allow image preview to expand

        self.toast = Toast(self)

        # --- Column 0: Name, Description, Category, Price ---
        # Product Name
        self._make_label(form_card, "Product Name", row=0, col=0)
        self.name_entry = ctk.CTkEntry(form_card, placeholder_text="e.g. Chocolate Cake", font=font(13),
                                       fg_color=settings.COLORS["card_border"], border_width=0,
                                       height=40, text_color=settings.COLORS["text"])
        self.name_entry.grid(row=1, column=0, columnspan=2, padx=24, pady=(0, 12), sticky="ew")

        # Description
        self._make_label(form_card, "Description", row=2, col=0)
        self.desc_text = ctk.CTkTextbox(form_card, height=100, font=font(13),
                                        fg_color=settings.COLORS["card_border"], border_width=0,
                                        text_color=settings.COLORS["text"])
        self.desc_text.grid(row=3, column=0, columnspan=2, padx=24, pady=(0, 12), sticky="ew")

        # Category
        self._make_label(form_card, "Category", row=4, col=0)
        self.category_var = ctk.StringVar(value="Select Category")  # Initial placeholder
        self.category_menu = ctk.CTkOptionMenu(form_card, variable=self.category_var, values=["(Loading...)"], command=self._on_category_selected,
            font=font(13), dropdown_font=font(13), fg_color=settings.COLORS["card_border"],
            button_color=settings.COLORS["card_border"], button_hover_color=settings.COLORS["card_border"],
            text_color=settings.COLORS["text"], height=40, anchor="w")
        self.category_menu.grid(row=5, column=0, padx=(24, 8), pady=(0, 12), sticky="ew")

        self.no_categories_hint_label = ctk.CTkLabel(form_card, text="No categories found. Go to Categories page to add some.",
                                                     font=font(11), text_color=settings.COLORS["text_muted"], anchor="w")
        # This label will be gridded/ungridded by _update_category_menu

        # Price
        self._make_label(form_card, "Price", row=4, col=1)
        self.price_entry = NairaEntry(form_card, placeholder_text="e.g. 8,000")
        self.price_entry.grid(row=5, column=1, padx=(8, 24), pady=(0, 12), sticky="nsew")

        # Image selection
        self._make_label(form_card, "Product Image (Optional)", row=6, col=0)
        self.image_path = ""
        self.image_filename_label = ctk.CTkLabel(form_card, text="No image selected.", font=font(12),
                                                 text_color=settings.COLORS["text_muted"], anchor="w")
        self.image_filename_label.grid(row=8, column=0, padx=(24, 8), pady=(0, 6), sticky="ew")

        choose_btn = make_button(form_card, "Choose Image...", command=self._choose_image,
                                 border=True, fg_color=settings.COLORS["accent"], height=40)
        choose_btn.grid(row=7, column=0, padx=(24, 8), pady=(0, 6), sticky="ew")

        self.image_preview = ctk.CTkLabel(form_card, text="",
                                          fg_color=settings.COLORS["card_border"],
                                          corner_radius=10)
        self.image_preview.grid(row=9, column=0, padx=(24, 8), pady=(0, 24), sticky="nsew")

        # Availability
        self._make_label(form_card, "Availability", row=6, col=1)
        self.available_var = ctk.StringVar(value="Available")
        avail_menu = ctk.CTkOptionMenu(
            form_card, variable=self.available_var, values=["Available", "Unavailable"],
            font=font(13), dropdown_font=font(13), fg_color=settings.COLORS["card_border"],
            button_color=settings.COLORS["card_border"], button_hover_color=settings.COLORS["card_border"],
            text_color=settings.COLORS["text"], height=40, anchor="w")
        avail_menu.grid(row=7, column=1, padx=(8, 24), pady=(0, 6), sticky="ew")

        # Error label
        self.error_label = ctk.CTkLabel(self, text="", font=font(12),
                                        text_color=settings.COLORS["danger"])
        self.error_label.grid(row=2, column=0, padx=24, pady=(0, 8), sticky="w")

        # Submit button
        self.submit_button = make_button(self, "ADD PRODUCT", # Default text, will be updated
                             command=self._submit, width=220, height=44, font_size=15)
        self.submit_button.grid(row=3, column=0, padx=24, pady=(0, 24), sticky="e")

        # Initial load of categories
        self._update_category_menu() # Ensure categories are fresh

    # ------------------------------------------------------------------
    # Category Menu Management
    # ------------------------------------------------------------------

    def _update_category_menu(self):
        """Fetches categories from DB and updates the option menu."""
        categories = db.get_category_names()
        if not categories:
            self.category_menu.configure(values=["(No categories)"])
            self.category_var.set("(No categories)")
            self.no_categories_hint_label.grid(row=6, column=0, padx=(24, 8), pady=(0, 12), sticky="ew")
        else:
            self.category_menu.configure(values=categories)
            # Only set if current value is a placeholder or not in new categories
            if self.category_var.get() in ["Select Category", "(No categories)"] or self.category_var.get() not in categories:
                self.category_var.set(categories[0]) # Select the first category by default
            self.no_categories_hint_label.grid_forget() # Hide the hint

    def _on_category_selected(self, choice):
        """Callback for when a category is selected from the option menu."""
        # This can be used for any immediate UI updates based on category selection
        pass

    # ------------------------------------------------------------------
    # Configuration for Add/Edit Mode
    # ------------------------------------------------------------------


    def configure_for_add(self):
        """Configures the form for adding a new product."""
        self.product = None
        self.header.set_title("Add Product")
        self.header.set_subtitle("Create a new product and add it to your menu.")
        self.submit_button.configure(text="ADD PRODUCT")

        # Clear all fields
        self.name_entry.delete(0, ctk.END)
        self.desc_text.delete("1.0", ctk.END)
        self.image_path = ""
        self.image_filename_label.configure(text="No image selected.")
        self.image_preview.configure(image=None, text="", fg_color=settings.COLORS["card_border"])
        self.price_entry.set_amount(0)
        self.available_var.set("Available")
        self.error_label.configure(text="")
        self._update_category_menu() # Ensure categories are fresh

    def configure_for_edit(self, product: Product):
        """Configures the form for editing an existing product."""
        self.product = product
        self.header.set_title("Edit Product")
        self.header.set_subtitle(f"Update the details of '{product.name}'.")
        self.submit_button.configure(text="Save Changes")

        self._populate(product)
        self.error_label.configure(text="")
        self._update_category_menu() # Ensure categories are fresh

    # ------------------------------------------------------------------
    # UI Helpers
    # ------------------------------------------------------------------
    def _make_label(self, parent, text, row, col):
        """Helper to create a form field label."""
        label = ctk.CTkLabel(parent, text=text, font=font(13, "semibold"),
                             text_color=settings.COLORS["text"], anchor="w")
        label.grid(row=row, column=col, padx=24, pady=(12, 4), sticky="w")
        return label

    # ------------------------------------------------------------------
    def _choose_image(self):
        path = filedialog.askopenfilename(
            title="Select Product Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")],
        )
        if path:
            self.image_path = path
            self.image_filename_label.configure(text=Path(path).name)
            # Use a placeholder size for the preview
            img = helpers.load_image_pil(path, (280, 200))
            if img:
                from customtkinter import CTkImage
                self.image_preview.configure(image=CTkImage(light_image=img, dark_image=img), fg_color="transparent",
                                             text="")
            else:
                self.image_preview.configure(text="Unable to load image")
            self.toast.show("Image selected", color=settings.COLORS["accent"])

    def _populate(self, product: Product):
        self.name_entry.insert(0, product.name)
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", product.description)
        self.category_var.set(product.category)
        self.price_entry.set_amount(product.price)
        self.available_var.set("Available" if product.available else "Unavailable")
        if product.image:
            self.image_path = product.image
            self.image_filename_label.configure(text=Path(product.image).name)
            img = helpers.load_image_pil(helpers.resolve_image_path(product.image), (280, 200))
            if img:
                from customtkinter import CTkImage
                self.image_preview.configure(image=CTkImage(light_image=img, dark_image=img),
                                             text="")

    def refresh(self):
        """Refreshes the view. For AddProductView, this primarily means updating categories.
        Product-specific data is loaded via configure_for_add/edit."""
        self._update_category_menu()
    
    # ------------------------------------------------------------------
    # Submission Logic
    # ------------------------------------------------------------------
    def _submit(self):
        """Initiates the product submission process in a background thread."""
        # Disable button and show loading state
        self.submit_button.configure(state="disabled", text="Adding product...")
        self.error_label.configure(text="") # Clear previous errors
        print("[ADD PRODUCT] Button clicked. Starting submission thread.")
    
        # Run the actual submission logic in a separate thread
        submit_thread = threading.Thread(target=self._perform_submit_in_thread, daemon=True)
        submit_thread.start()
    
    def _perform_submit_in_thread(self):
        """Performs form validation, image upload, and database operations."""
        button_text_initial = "ADD PRODUCT" if not self.product else "Save Changes"
        try:
            # Retrieve form values
            name = self.name_entry.get().strip()
            desc = self.desc_text.get("1.0", "end-1c").strip()
            category = self.category_var.get()
            price_str = self.price_entry.get_amount() # Retrieve price as string from NairaEntry
    
            available = self.available_var.get() == "Available"
            print(f"[ADD PRODUCT] Form values collected: Name='{name}', Category='{category}', Price='{price_str}', Available={available}")
    
            # --- Validation ---
            errors = []
    
            # Validate product name
            ok, msg = validators.validate_product_name(name)
            if not ok:
                errors.append(msg)
    
            # Validate description (optional, but length check)
            ok, msg = validators.validate_description(desc)
            if not ok:
                errors.append(msg)
    
            # Validate category
            if category == "Select Category" or category == "(No categories)" or not category:
                errors.append("Please select a valid category.")
            else:
                ok, msg = validators.validate_category(category)
                if not ok:
                    errors.append(msg)
    
            # Validate price
            ok, msg = validators.validate_price(price_str)
            if not ok:
                errors.append(msg)
            else:
                try:
                    price_val = float(price_str)
                except ValueError:
                    errors.append("Price must be a valid number.") # Should be caught by validate_price, but good to be safe
    
            if errors:
                print(f"[ADD PRODUCT] Validation failed: {errors}")
                # Update GUI on main thread
                self.app.after(0, lambda: self.error_label.configure(text="  •  ".join(errors)))
                self.app.after(0, lambda: self.submit_button.configure(state="normal", text=button_text_initial))
                return # Stop submission on validation failure
    
            print("[ADD PRODUCT] Validation passed.")
    
            # --- Image Upload ---
            stored_image_url = ""
            current_image_path = self.image_path # This could be a local path or an existing URL
    
            # Check if Supabase client is available for image upload
            if get_supabase_client() is not None:
                # If a new local file was selected OR if it's a new product with an image
                is_new_local_image_selected = current_image_path and Path(current_image_path).exists()
                is_existing_supabase_image = self.product and current_image_path == self.product.image and not Path(current_image_path).exists()
    
                if is_new_local_image_selected:
                    print(f"[ADD PRODUCT] Starting image upload for: {current_image_path}")
                    self.app.after(0, lambda: self.submit_button.configure(text="Uploading image..."))
                    # Upload the new image
                    stored_image_url = supabase_storage.upload_product_image(current_image_path)
                    print(f"[ADD PRODUCT] Image upload completed. URL: {stored_image_url}")
    
                    # If editing and a new image was uploaded, delete the old one if it was from Supabase
                    if self.product and self.product.image and self.product.image != stored_image_url:
                        old_object_name = supabase_storage.extract_object_name(self.product.image)
                        if old_object_name:
                            print(f"[ADD PRODUCT] Deleting old image: {old_object_name}")
                            try:
                                supabase_storage.delete_product_image(old_object_name)
                                print(f"[ADD PRODUCT] Old image {old_object_name} deleted.")
                            except Exception as e:
                                print(f"[ADD PRODUCT] WARNING: Failed to delete old image {old_object_name}: {e}")
    
                elif is_existing_supabase_image:
                    # Editing a product, and the image wasn't changed (it's still the Supabase URL)
                    stored_image_url = self.product.image
                    print("[ADD PRODUCT] Image not changed, keeping existing Supabase URL.")
                else:
                    # No image selected, or image was removed (set to empty string)
                    stored_image_url = ""
                    print("[ADD PRODUCT] No image selected or image removed.")
            else:
                # Supabase client not available, local image handling (if any) or keep existing URL
                # For this project, we assume Supabase is the ONLY backend for images.
                # If Supabase is not configured, image upload is not possible.
                if current_image_path and Path(current_image_path).exists():
                    errors.append("Supabase is not configured. Image upload is not possible.")
                    self.app.after(0, lambda: self.error_label.configure(text="  •  ".join(errors)))
                    self.app.after(0, lambda: self.submit_button.configure(state="normal", text=button_text_initial))
                    return
                else:
                    # No image selected or existing image was a URL (which we can't verify without Supabase)
                    stored_image_url = current_image_path # Keep whatever was there, might be empty or old URL
                    print("[ADD PRODUCT] Supabase client not available. Image handling is limited.")
    
    
            if errors: # Re-check errors after image handling
                print(f"[ADD PRODUCT] Image handling failed with errors: {errors}")
                self.app.after(0, lambda: self.error_label.configure(text="  •  ".join(errors)))
                self.app.after(0, lambda: self.submit_button.configure(state="normal", text=button_text_initial))
                return
    
            # --- Database Operation ---
            print("[ADD PRODUCT] Starting product INSERT/UPDATE.")
            self.app.after(0, lambda: self.submit_button.configure(text="Saving product..."))
    
            if self.product:  # edit mode
                db.update_product(
                    self.product.id,
                    name=name,
                    description=desc,
                    category=category,
                    price=price_val,
                    image=stored_image_url, # Pass the resolved image URL
                    available=available,
                )
                self.app.after(0, lambda: self.app.toast_global(f"Product '{name}' updated"))
                print(f"[ADD PRODUCT] Product '{name}' updated successfully.")
            else:  # add mode
                db.add_product(
                    name=name,
                    description=desc,
                    category=category,
                    price=price_val,
                    image=stored_image_url, # Pass the resolved image URL
                    available=available
                )
                self.app.after(0, lambda: self.app.toast_global(f"Product '{name}' added"))
                print(f"[ADD PRODUCT] Product '{name}' added successfully.")
    
            self.app.after(0, lambda: self.app.show_view("products")) # Navigate back to products view on main thread
    
        except (ValueError, RuntimeError) as exc:
            # Catch specific errors from validators, supabase_storage, or supabase_repository
            error_message = str(exc)
            print(f"[ADD PRODUCT] Operation failed: {error_message}")
            traceback.print_exc()
            self.app.after(0, lambda msg=error_message: self.error_label.configure(text=msg)) # Pass message as default arg
        except Exception as exc:
            # Catch any other unexpected errors during database operation
            error_message = str(exc)
            print(f"[ADD PRODUCT] An unexpected error occurred during submission: {error_message}")
            traceback.print_exc()
            self.app.after(0, lambda msg=error_message: self.error_label.configure(text=f"An unexpected error occurred: {msg}")) # Pass message as default arg
        finally:
            # Always re-enable button and restore text on the main thread
            self.app.after(0, lambda: self.submit_button.configure(state="normal", text=button_text_initial))
            print("[ADD PRODUCT] Submission thread finished.")
