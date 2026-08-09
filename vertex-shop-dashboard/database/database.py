"""
Vertex Shop Admin Dashboard - Data layer.

The dashboard uses Supabase as its ONLY backend. SQLite and demo data have
been removed. The views use the repository methods exposed by the singleton
`db` below, which is a `SupabaseDatabase` instance.

If Supabase is unavailable, the app raises a clear error — it does NOT
silently fall back to SQLite or generate demo data.
"""
from .supabase_client import get_supabase_client
from .supabase_repository import SupabaseDatabase


def _build_active_database():
    """Build the Supabase-backed repository.

    Raises RuntimeError if Supabase cannot be reached so the UI can show a
    clear error instead of silently using a local/demo database.
    """
    client = get_supabase_client()  # raises RuntimeError if not configured
    repo = SupabaseDatabase(client)
    if not repo.available:
        raise RuntimeError(
            "Supabase connection failed. Please check your configuration."
        )
    return repo


# Singleton instance used across the app.
db = _build_active_database()
