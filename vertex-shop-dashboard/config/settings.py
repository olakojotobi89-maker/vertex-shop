"""
Vertex Shop Admin Dashboard - Application settings and constants.

This module centralises configuration so that switching the data layer to
Supabase later only requires changing a few values here / in database.py.

SECURITY NOTE:
    No Supabase secret/service-role keys are stored here. When Supabase is
    integrated, sensitive credentials MUST be read from environment
    variables (e.g. os.environ) or a local .env file, never hard-coded.
"""
import os
import pathlib

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Project root = parent of the config folder (vertex-shop-dashboard/)
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

# Where the SQLite database file lives.
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "vertex_shop.db"
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"

# Product images uploaded by the admin are copied here (local storage).
# When Supabase Storage is integrated, this folder is replaced by a bucket.
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# A default placeholder image used when a product has no image.
PLACEHOLDER_IMAGE = os.environ.get("VS_PLACEHOLDER_IMAGE", "")

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------
APP_NAME = "Vertex Shop"
APP_TITLE = "Vertex Shop - Admin Dashboard"
APP_VERSION = "1.0.0"
COMPANY = "Vertex Shop"

# ---------------------------------------------------------------------------
# Supabase configuration (the ONLY backend for the dashboard).
# ---------------------------------------------------------------------------
# Credentials are read from environment variables / the .env file (loaded in
# database/supabase_client.py via python-dotenv). Only the PUBLISHABLE/anon
# key is used here. The service-role key is NEVER used by this app.
#   SUPABASE_URL
#   SUPABASE_ANON_KEY
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

# Supabase Storage bucket used for product images.
STORAGE_BUCKET = "product-images"

# ---------------------------------------------------------------------------
# Order status workflow (in order of progress)
# ---------------------------------------------------------------------------
ORDER_STATUSES = [
    "Pending",
    "Confirmed",
    "Preparing",
    "Ready",
    "Out for Delivery",
    "Delivered",
    "Cancelled",
]

# Statuses that are considered "active" (not finished/cancelled).
ACTIVE_STATUSES = [
    "Pending",
    "Confirmed",
    "Preparing",
    "Ready",
    "Out for Delivery",
]

COMPLETED_STATUS = "Delivered"
CANCELLED_STATUS = "Cancelled"

# ---------------------------------------------------------------------------
# Visual theme
# ---------------------------------------------------------------------------
APPEARANCE_MODE = "dark"  # "dark", "light", or "system"
COLOR_THEME = "green"     # CustomTkinter built-in accent

# Custom palette (used for cards, accents, badges)
COLORS = {
    "sidebar_bg": "#1B1F27",
    "content_bg": "#14171C",
    "card_bg": "#1E232B",
    "card_border": "#2A313B",
    "primary": "#22C55E",
    "primary_hover": "#16A34A",
    "accent": "#3B82F6",
    "danger": "#EF4444",
    "warning": "#F59E0B",
    "text": "#EAECEF",
    "text_muted": "#8A93A3",
    "white": "#FFFFFF",
}

# Status -> badge colour mapping for order status labels.
STATUS_COLORS = {
    "Pending": "#F59E0B",
    "Confirmed": "#3B82F6",
    "Preparing": "#8B5CF6",
    "Ready": "#14B8A6",
    "Out for Delivery": "#06B6D4",
    "Delivered": "#22C55E",
    "Cancelled": "#EF4444",
}

# ---------------------------------------------------------------------------
# Delivery fee (matches the public web app)
# ---------------------------------------------------------------------------
DELIVERY_FEE = 800

# Supported pickup locations (matches the public web app)
PICKUP_LOCATIONS = [
    "Vertex Shop - Wuse II Station",
    "Vertex Shop - Garki Station",
    "Vertex Shop - Jabi Station",
]

# ---------------------------------------------------------------------------
# Realtime settings
# ---------------------------------------------------------------------------
# New-order notifications are driven by Supabase Realtime on public.orders.
# No simulated/demo orders are ever generated.
REALTIME_ORDERS_CHANNEL = "realtime:vertex-orders"
