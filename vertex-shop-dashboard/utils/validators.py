"""
Validation helpers for forms and input fields.

Each function returns (is_valid: bool, error_message: str).
"""
import re


def validate_required(value) -> tuple:
    """A non-empty value is required."""
    if value is None or not str(value).strip():
        return False, "This field is required."
    return True, ""


def validate_product_name(value) -> tuple:
    s = str(value or "").strip()
    if not s:
        return False, "Product name is required."
    if len(s) < 2:
        return False, "Product name must be at least 2 characters."
    if len(s) > 120:
        return False, "Product name must be 120 characters or fewer."
    return True, ""


def validate_description(value) -> tuple:
    s = str(value or "").strip()
    if len(s) > 1000:
        return False, "Description must be 1000 characters or fewer."
    return True, ""


def validate_price(value) -> tuple:
    s = str(value or "").strip()
    if not s:
        return False, "Price is required."
    try:
        num = float(s.replace(",", ""))
    except ValueError:
        return False, "Price must be a valid number."
    if num < 0:
        return False, "Price cannot be negative."
    return True, ""


def validate_category(value) -> tuple:
    s = str(value or "").strip()
    if not s:
        return False, "Please select a category."
    return True, ""


def validate_category_name(value) -> tuple:
    s = str(value or "").strip()
    if not s:
        return False, "Category name is required."
    if len(s) < 2:
        return False, "Category name must be at least 2 characters."
    if len(s) > 60:
        return False, "Category name must be 60 characters or fewer."
    return True, ""


def validate_phone(value) -> tuple:
    s = str(value or "").strip()
    if not s:
        return False, "Phone number is required."
    # Accept digits, spaces, +, - ; between 7 and 15 characters.
    if not re.fullmatch(r"^[0-9+\s-]{7,15}$", s):
        return False, "Enter a valid phone number (e.g. 080 1234 5678)."
    return True, ""


def validate_email(value) -> tuple:
    s = str(value or "").strip()
    if not s:
        return True, ""  # email is optional
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", s):
        return False, "Enter a valid email address."
    return True, ""


def validate_customer_name(value) -> tuple:
    s = str(value or "").strip()
    if not s:
        return False, "Customer name is required."
    if len(s) < 2:
        return False, "Customer name must be at least 2 characters."
    return True, ""


def validate_search(value) -> tuple:
    # Search is always allowed (empty = no filter).
    return True, ""
