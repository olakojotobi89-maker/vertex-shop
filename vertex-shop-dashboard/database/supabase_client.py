"""
Supabase client initialisation.

Reads credentials from environment variables (never hard-coded). Uses the
Supabase anon/publishable key for normal CRUD operations. The service-role
key is NEVER used by the desktop app for routine operations; when elevated
privileges / admin writes are required, use a dedicated admin user session
with RLS granting admin access via a custom app_role claim.

SECURITY:
- Credentials come from environment variables or a .env file (loaded via
  python-dotenv). Never commit real secrets.
- The public web app only ever receives the publishable key.
"""
import os

import config.settings as settings

# Load .env from the project root (BEFORE settings resolves env vars).
# python-dotenv is optional; if it is not installed we simply rely on the
# process environment variables.
try:
    from dotenv import load_dotenv
    load_dotenv(settings.BASE_DIR / ".env")
except Exception:
    pass


def get_supabase_client():
    """
    Build and return an authenticated Supabase client.

    Returns None if credentials are missing or the supabase package is not
    installed (the app then falls back to the local SQLite layer).
    """
    try:
        from supabase import create_client, Client
    except ImportError:
        print("supabase-py not installed. Run: pip install supabase python-dotenv")
        return None

    url = os.environ.get("SUPABASE_URL", settings.SUPABASE_URL)
    key = os.environ.get("SUPABASE_ANON_KEY", settings.SUPABASE_ANON_KEY)

    if not url or not key:
        print("Supabase credentials not configured. Falling back to local data.")
        return None

    try:
        client: Client = create_client(url, key)
        return client
    except Exception as exc:
        print(f"Failed to initialise Supabase client: {exc}")
        return None
