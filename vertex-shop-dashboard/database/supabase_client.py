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
import sys  # Added for diagnostics
import ssl  # Added for diagnostics
import threading
import httpx # Import httpx here for both sync and async clients
import asyncio # For async client

import config.settings as settings

# Load .env from the project root (BEFORE settings resolves env vars).
try:
    from dotenv import load_dotenv
    load_dotenv(settings.BASE_DIR / ".env")
except Exception:
    pass


_sync_client = None
_async_client = None  # New global for async client
_admin_session = None
_sync_http_client = None  # Store the httpx.Client instance for sync
_async_http_client = None  # Store the httpx.AsyncClient instance for async
_admin_user = None
_lock = threading.Lock()


# Helper function to create the httpx client (sync or async)
def _create_httpx_client(is_async: bool):
    print(f"[Supabase Client] Creating custom httpx.{'AsyncClient' if is_async else 'Client'} with http2=False.")
    if is_async:
        return httpx.AsyncClient(
            verify=True,
            follow_redirects=True,
            http2=False,
        )
    else:
        return httpx.Client(
            verify=True,
            follow_redirects=True,
            http2=False,
        )

def _get_common_client_config():
    url = os.environ.get("SUPABASE_URL", settings.SUPABASE_URL)
    key = os.environ.get("SUPABASE_ANON_KEY", settings.SUPABASE_ANON_KEY)
    if not url or not key:
        raise RuntimeError("Supabase credentials are not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY in the .env file.")
    url = url.rstrip("/")
    return url if url.startswith("https://") else f"https://{url}"


def get_supabase_client():
    """
    Return the shared Supabase client (created with the publishable key).

    Raises RuntimeError if the supabase package is missing or credentials
    are not configured. The dashboard does NOT fall back to SQLite.
    """
    global _sync_client, _sync_http_client
    if _sync_client is not None:
        return _sync_client
    
    with _lock:
        # Double-check after acquiring lock
        if _sync_client is not None:
            print("[Supabase Client] Reusing existing synchronous Supabase client (after lock).")
            return _sync_client
        try:
            print("[Supabase Client] Initializing new Supabase client.")
            print(f"[Supabase Client] Python version: {sys.version}")
            from supabase import create_client, Client, ClientOptions
        except ImportError as exc:
            raise RuntimeError(
                "supabase-py is not installed. Run: pip install -r requirements.txt"
            ) from exc

        url, key = _get_common_client_config(), os.environ.get("SUPABASE_ANON_KEY", settings.SUPABASE_ANON_KEY)
        
        print(f"[Supabase Client] Using SUPABASE_URL: {url}")
        print(f"[Supabase Client] Using SUPABASE_ANON_KEY (first 5 chars): {key[:5]}...")
        print(f"[Supabase Client] OpenSSL version: {ssl.OPENSSL_VERSION}")
        
        try:
            # Build a custom httpx client with HTTP/2 disabled.
            #
            # This custom httpx client is now explicitly passed to both the
            # main Supabase client and its internal GoTrue (auth) client
            # to ensure HTTP/1.1 is used for all requests, including auth.
            import httpx
            _sync_http_client = _create_httpx_client(is_async=False)
            
            # The 'auth_client_options' parameter caused a TypeError in this version of supabase-py.
            # The top-level 'httpx_client' should propagate to the internal auth client by default.
            options = ClientOptions(
                httpx_client=_sync_http_client,
            )
            _sync_client = create_client(url, key, options=options)
            print("[Supabase Client] Synchronous Supabase client initialized successfully.")
        except Exception as exc:
            print(f"[Supabase Client] ERROR: Failed to initialise synchronous Supabase client: {exc}")
            import traceback; traceback.print_exc()
            raise RuntimeError(f"Failed to initialise synchronous Supabase client: {exc}") from exc
        return _sync_client


def get_supabase_async_client():
    """
    Return the shared asynchronous Supabase client (created with the publishable key).
    This client is specifically for Realtime features.
    """
    global _async_client, _async_http_client
    if _async_client is not None:
        return _async_client

    with _lock:
        if _async_client is not None:
            print("[Supabase Client] Reusing existing asynchronous Supabase client (after lock).")
            return _async_client
        try:
            print("[Supabase Client] Initializing new asynchronous Supabase client.")
            print(f"[Supabase Client] Python version: {sys.version}")
            from supabase import create_client, Client, ClientOptions
        except ImportError as exc:
            raise RuntimeError(
                "supabase-py is not installed. Run: pip install -r requirements.txt"
            ) from exc

        url, key = _get_common_client_config(), os.environ.get("SUPABASE_ANON_KEY", settings.SUPABASE_ANON_KEY)
        print(f"[Supabase Client] Using SUPABASE_URL: {url} (Async)")
        print(f"[Supabase Client] Using SUPABASE_ANON_KEY (first 5 chars): {key[:5]}... (Async)")
        try:
            _async_http_client = _create_httpx_client(is_async=True)
            options = ClientOptions(httpx_client=_async_http_client, is_async=True)
            _async_client = create_client(url, key, options=options)
            print("[Supabase Client] Asynchronous Supabase client initialized successfully.")
        except Exception as exc:
            print(f"[Supabase Client] ERROR: Failed to initialise asynchronous Supabase client: {exc}")
            import traceback; traceback.print_exc()
            raise RuntimeError(f"Failed to initialise asynchronous Supabase client: {exc}") from exc
        return _async_client


def is_admin_authenticated() -> bool:
    """Return True if the current session is authenticated as an admin."""
    global _admin_user
    return bool(_admin_user and _admin_user.get("app_role") == "admin")


def get_supabase_http_client():
    """Return the configured httpx.Client instance."""
    return _sync_http_client


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

    print(f"[Supabase Auth] Attempting sign-in for email: {email}")
    try:
        res = client.auth.sign_in_with_password({"email": email, "password": password})
        print("[Supabase Auth] sign_in_with_password call completed.")
    except Exception as exc:
        msg = getattr(exc, "message", None) or str(exc)
        print(f"[Supabase Auth] ERROR: Admin sign-in failed during client.auth.sign_in_with_password: {msg}")
        import traceback; traceback.print_exc()
        raise RuntimeError(f"Admin sign-in failed: {msg}") from exc

    session = getattr(res, "session", None)
    user = getattr(res, "user", None)
    if not session or not user:
        raise RuntimeError("Admin sign-in returned no session.")

    # Determine app_role from raw_app_meta_data (JWT claim), NOT user_metadata.
    # The Supabase SDK returns a `User` object (attributes, not a dict),
    # so use getattr() instead of .get().
    app_metadata = getattr(user, "app_metadata", None) or {}
    app_role = app_metadata.get("app_role")

    print(f"[Supabase Auth] User authenticated. App role: {app_role}")
    if app_role != "admin":
        sign_out_admin()
        print(f"[Supabase Auth] Access denied: User {email} is not an admin (app_role={app_role}).")
        raise RuntimeError(
            "Access denied: this account is not an administrator "
            "(missing app_role=admin claim)."
        )
    _admin_session = session
    _admin_user = {
        "id": getattr(user, "id", None),
        "email": getattr(user, "email", None),
        "app_role": app_role,
    }
    return _admin_user
    print(f"[Supabase Auth] Admin {email} successfully signed in.")


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
