"""
Helper functions: formatting, date utils, image loading, status helpers.

These are UI-agnostic helpers used across views.
"""
from datetime import datetime
from pathlib import Path

import config.settings as settings


def format_naira(amount: float) -> str:
    """Format a number as a Naira string, e.g. 8500 -> ₦8,500."""
    try:
        return f"₦{float(amount or 0):,.0f}"
    except (ValueError, TypeError):
        return "₦0"


def format_date(iso: str, fmt: str = "%d %b %Y, %I:%M %p") -> str:
    """Format an ISO datetime string into a friendly label."""
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime(fmt)
    except (ValueError, TypeError):
        return iso


def format_date_short(iso: str) -> str:
    return format_date(iso, "%d %b %Y")


def today_date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def status_badge_color(status: str) -> str:
    """Return the hex colour used for a status badge."""
    return settings.STATUS_COLORS.get(status, "#6B7280")


def load_image_pil(path, size=(80, 80)):
    """
    Load an image file into a PIL.Image resized to `size`.
    Returns None if the file cannot be loaded.
    """
    from PIL import Image  # imported lazily to keep helpers light

    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        img = Image.open(p).convert("RGB")
        img.thumbnail(size)
        return img
    except Exception:
        return None


def load_placeholder_icon(size=(80, 80)):
    """Return a neutral placeholder image when no product image exists."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", size, (45, 52, 63))
    draw = ImageDraw.Draw(img)
    draw.ellipse((size[0] // 2 - 18, size[1] // 2 - 18,
                  size[0] // 2 + 18, size[1] // 2 + 18),
                 fill=(110, 120, 135))
    return img


def copy_image_to_upload(src_path: str) -> str:
    """
    Copy a chosen image into the local uploads folder and return the
    stored relative filename. Retained only for backwards-compatibility;
    the dashboard now uploads images to Supabase Storage.
    """
    import shutil
    import uuid

    if not src_path:
        return ""

    src = Path(src_path)
    if not src.exists():
        return ""

    ext = src.suffix.lower()
    if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
        ext = ".png"

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = settings.UPLOAD_DIR / filename
    try:
        shutil.copyfile(src, dest)
    except Exception:
        return ""

    # Store the path relative to the uploads dir so it survives moves.
    return str(dest)


def load_image_from_url(url, size=(80, 80)):
    """Load an image from a URL into a PIL.Image resized to `size`.

    Returns None if the URL cannot be fetched or decoded.
    """
    if not url:
        return None
    if not (url.startswith("http://") or url.startswith("https://")):
        return None
    try:
        import io
        import urllib.request
        from PIL import Image

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.thumbnail(size)
        return img
    except Exception:
        return None


def load_product_image(stored, size=(80, 80)):
    """Load a product image that may be a local path or a Supabase URL."""
    if not stored:
        return None
    img = load_image_pil(stored, size)
    if img is not None:
        return img
    return load_image_from_url(stored, size)


def resolve_image_path(stored: str):
    """Resolve a stored image filename/path to an absolute path."""
    if not stored:
        return ""
    p = Path(stored)
    if p.exists():
        return str(p)
    # Try under the uploads dir
    candidate = settings.UPLOAD_DIR / stored
    if candidate.exists():
        return str(candidate)
    return stored


def truncate(text: str, length: int = 40) -> str:
    if text is None:
        return ""
    text = str(text)
    return text[:length] + ("…" if len(text) > length else "")
