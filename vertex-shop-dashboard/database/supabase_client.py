"""
Supabase client initialisation and admin authentication.

The dashboard uses the publishable/anon key to create a Supabase client.
Admin operations (product/category writes and storage uploads) REQUIRE the
client to be signed in as an authenticated user whose JWT carries an
`app_role` of `admin` (set via `raw_app_meta_data`, not `user_metadata`).

SECURITY:
- Credentials come from environment variables or the .env file (loaded via
  python-dotenv). Never commit real secrets.
- Only the PUBLISHABLE key is stored. The service-role key is NEVER used.
- The admin password is never stored locally; it is only used transiently
  to obtain a Supabase Auth session.
"""
import os
import threading

import config.settings as settings

# Load .env from the project root (BEFORE settings resolves env vars).
try:
    from dotenv import load_dotenv
    load_dotenv(settings.BASE_DIR / ".env")
except Exception:
    pass


_client = None
_admin_session = None
_admin_user = None
_lock = threading.Lock()


def get_supabase_client():
    """
    Return the shared Supabase client (created with the publishable key).

    Raises RuntimeError if the supabase package is missing or credentials
    are not configured. The dashboard does NOT fall back to SQLite.
    """
    global _client
    if _client is not None:
        return _client
    with _lock:
        if _client is not None:
            return _client
        try:
            from supabase import create_client, Client
        except ImportError as exc:
            raise RuntimeError(
                "supabase-py is not installed. Run: pip install -r requirements.txt"
            ) from exc

        url = os.environ.get("SUPABASE_URL", settings.SUPABASE_URL)
        key = os.environ.get("SUPABASE_ANON_KEY", settings.SUPABASE_ANON_KEY)

        if not url or not key:
            raise RuntimeError(
                "Supabase credentials are not configured. Please set SUPABASE_URL "
                "and SUPABASE_ANON_KEY in the .env file."
            )

        url = url.rstrip("/")
        url = url if url.startswith("https://") else f"https://{url}"

        try:
            _client = create_client(url, key)
        except Exception as exc:
            raise RuntimeError(f"Failed to initialise Supabase client: {exc}") from exc
        return _client


def is_admin_authenticated() -> bool:
    """Return True if the current session is authenticated as an admin."""
    global _admin_user
    return bool(_admin_user and _admin_user.get("app_role") == "admin")


def get_admin_user() -> dict:
    """Return the current admin user dict (or None)."""
    return _admin_user


def sign_in_admin(email: str, password: str) -> dict:
    """
    Authenticate an administrator via Supabase Auth.

    Verifies that the authenticated user carries the `app_role=admin` claim
    in raw_app_meta_data (JWT). Raises RuntimeError if sign-in fails or the
    user is not an admin. The password is never stored.
    """
    global _admin_session, _admin_user
    client = get_supabase_client()

    try:
        res = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as exc:
        msg = getattr(exc, "message", None) or str(exc)
        raise RuntimeError(f"Admin sign-in failed: {msg}") from exc

    session = getattr(res, "session", None)
    user = getattr(res, "user", None)
    if not session or not user:
        raise RuntimeError("Admin sign-in returned no session.")

    # Determine app_role from raw_app_meta_data (JWT claim), NOT user_metadata.
    app_metadata = user.get("app_metadata") or {}
    raw_app_meta = app_metadata.get("raw_app_meta_data") or {}
    app_role = raw_app_meta.get("app_role") or app_metadata.get("app_role")

    if app_role != "admin":
        sign_out_admin()
        raise RuntimeError(
            "Access denied: this account is not an administrator "
            "(missing app_role=admin claim)."
        )

    _admin_session = session
    _admin_user = {
        "id": user.get("id"),
        "email": user.get("email"),
        "app_role": app_role,
    }
    return _admin_user


def sign_out_admin():
    """Sign out the current admin session (if any)."""
    global _admin_session, _admin_user
    try:
        if _admin_session:
            get_supabase_client().auth.sign_out()
    except Exception:
        pass
    _admin_session = None
    _admin_user = None


def get_admin_session():
    """Return the current admin session object (or None)."""
    return _admin_session
