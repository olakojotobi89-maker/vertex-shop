"""
Headless construction test for all dashboard views.

Instantiates the main app and drives the lazy view factory for every
sidebar section to confirm each constructs without a traceback. A mock
admin session is injected so `_require_admin()` does not block view
construction (real data reads still run against Supabase with the anon key
and are RLS-limited; the goal here is to confirm view construction and
navigation do not throw).

Run:  python _test_views_construct.py
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

import config.settings as settings
import database.supabase_client as supabase_auth
from main import VertexShopApp

VIEWS = ["dashboard", "products", "orders", "customers", "categories", "settings"]


def main():
    # Inject a mock admin session so order/customer repository reads are not
    # blocked by `_require_admin()` during view construction.
    supabase_auth._admin_user = {
        "id": "00000000-0000-0000-0000-000000000000",
        "email": "admin@vertexshop.com",
        "app_role": "admin",
    }
    supabase_auth._admin_session = None  # no real token; reads rely on anon key

    errors = []
    app = VertexShopApp()
    # Bypass the login gate by building layout directly.
    app.login_view.destroy()
    app.logged_in = True
    app._build_layout()
    app.notifications.start = lambda: None  # avoid realtime in headless test

    for name in VIEWS:
        try:
            app.show_view(name)
            print(f"[TEST] OK constructed/refreshed view: {name}")
        except Exception:
            print(f"[TEST] FAILED view: {name}")
            traceback.print_exc()
            errors.append(name)

    # Also exercise navigation repeatedly between views.
    try:
        for i in range(3):
            for name in VIEWS:
                app.show_view(name)
        print("[TEST] OK repeated navigation across all views")
    except Exception:
        print("[TEST] FAILED during repeated navigation")
        traceback.print_exc()
        errors.append("navigation")

    app.destroy()

    if errors:
        print(f"\n[TEST] ERRORS: {errors}")
        sys.exit(1)
    print("\n[TEST] ALL VIEWS CONSTRUCTED SUCCESSFULLY")


if __name__ == "__main__":
    main()
