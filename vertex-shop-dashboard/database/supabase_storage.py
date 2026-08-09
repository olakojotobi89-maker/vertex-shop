"""
Supabase Storage helpers for product images.

Uploads an image to the `product-images` bucket and returns the public URL.
Errors are propagated (NOT swallowed) so the UI can show the actual reason.
"""
import uuid
from pathlib import Path
import httpx # Not directly used for passing, but useful for context if needed
import config.settings as settings
from database.supabase_client import get_supabase_client, is_admin_authenticated # Removed get_supabase_http_client as it's not needed for Storage methods


# Allowed image extensions (case-insensitive).
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def validate_image_file(file_path: str) -> Path:
    """
    Validate a selected image file. Returns the Path if valid.
    Raises ValueError with a clear message if invalid.
    """
    if not file_path:
        raise ValueError("No image file selected.")
    src = Path(file_path)
    if not src.exists() or not src.is_file():
        raise ValueError(f"Image file not found: {file_path}")
    ext = src.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    # Basic size guard (50 MB).
    max_bytes = 50 * 1024 * 1024
    if src.stat().st_size > max_bytes:
        raise ValueError("Image is too large (max 50 MB).")
    return src


def upload_product_image(file_path: str) -> str:
    """
    Upload an image to the 'product-images' bucket and return the public URL.

    Requires an authenticated admin session (with app_role=admin in the JWT).
    Raises RuntimeError with the ACTUAL error if the upload fails.
    """
    src = validate_image_file(file_path)
    
    if not is_admin_authenticated():
        raise RuntimeError(
            "You must be signed in as an administrator to upload product images."
        )

    client = get_supabase_client()
    bucket = settings.STORAGE_BUCKET

    ext = src.suffix.lower() or ".png"
    object_name = f"{uuid.uuid4().hex}{ext}"

    try:
        with open(src, "rb") as f:
            data = f.read()
    except Exception as exc:
        raise RuntimeError(f"Could not read image file: {exc}") from exc

    # Upload to Supabase Storage. Do NOT swallow errors.
    try:
        # The supabase-py client needs the content-type to be set for the
        # file to be viewable in the browser instead of being downloaded.
        import mimetypes
        content_type, _ = mimetypes.guess_type(str(src)) # Convert Path to string for mimetypes.
        file_options = {"content-type": content_type or "application/octet-stream"}
        client.storage.from_(bucket).upload(object_name, data, file_options=file_options)
    except Exception as exc:
        detail = getattr(exc, "message", None) or str(exc)
        raise RuntimeError(f"Product image upload failed: {detail}") from exc

    # Build the public URL.
    try:
        public_url = client.storage.from_(bucket).get_public_url(object_name)
        if public_url:
            return public_url
    except Exception as exc:
        # Fall back to constructing the standard public URL manually.
        base = settings.SUPABASE_URL.rstrip("/")
        return f"{base}/storage/v1/object/public/{bucket}/{object_name}"

    base = settings.SUPABASE_URL.rstrip("/")
    return f"{base}/storage/v1/object/public/{bucket}/{object_name}"


def delete_product_image(object_name: str):
    """
    Delete an image from the 'product-images' bucket. Best-effort.
    Propagates real errors so the UI can show them.
    """
    if not object_name:
        return
    if not is_admin_authenticated():
        raise RuntimeError(
            "You must be signed in as an administrator to delete product images."
        )
    client = get_supabase_client()
    try:
        client.storage.from_(settings.STORAGE_BUCKET).remove([object_name])
    except Exception as exc:
        detail = getattr(exc, "message", None) or str(exc)
        raise RuntimeError(f"Product image delete failed: {detail}") from exc
    

def extract_object_name(public_url: str) -> str:
    """Extract the storage object name from a public URL (if it is one)."""
    if not public_url:
        return ""
    marker = f"/#_object/{settings.STORAGE_BUCKET}/"
    marker2 = f"/object/public/{settings.STORAGE_BUCKET}/"
    if marker in public_url:
        return public_url.split(marker, 1)[1]
    if marker2 in public_url:
        return public_url.split(marker2, 1)[1]
    return ""
