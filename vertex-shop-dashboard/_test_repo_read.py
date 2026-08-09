"""
Data-layer read test.

Confirms the Supabase repository can read real orders, order items, and
customers from the production Supabase project using the anon key. A mock
admin session flag is set so `_require_admin()` passes, but the actual HTTP
requests still use the anon (publishable) key and are subject to RLS.

Run:  python _test_repo_read.py
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database.supabase_client as supabase_auth
from database.supabase_repository import SupabaseDatabase
from database.supabase_client import get_supabase_client

# Bypass the admin gate for the read test (uses anon key + RLS).
supabase_auth._admin_user = {
    "id": "00000000-0000-0000-0000-000000000000",
    "email": "admin@vertexshop.com",
    "app_role": "admin",
}


def main():
    try:
        client = get_supabase_client()
        repo = SupabaseDatabase(client)
        print("=== repository.available:", repo.available)

        print("\n--- get_orders() ---")
        orders = repo.get_orders()
        print(f"Order count: {len(orders)}")
        for o in orders[:10]:
            print(f"  {o.order_no} | {o.customer_name} | {o.phone if hasattr(o,'phone') else 'n/a'} | "
                  f"{o.total_naira} | {o.status} | items={len(o.items)}")
            for it in o.items:
                print(f"      - {it.name} x{it.quantity} @ {it.price} = {it.subtotal}")

        print("\n--- recent_orders(5) ---")
        recent = repo.recent_orders(5)
        for o in recent:
            print(f"  {o.order_no} | {o.customer_name} | {o.total_naira} | {o.status} | items={len(o.items)}")

        print("\n--- get_customers() ---")
        customers = repo.get_customers()
        print(f"Customer count: {len(customers)}")
        for c in customers[:10]:
            print(f"  {c.name} | {c.phone} | {c.email} | orders={c.order_count} | spent={c.total_spent}")

        print("\n--- dashboard_stats() ---")
        stats = repo.dashboard_stats()
        print(stats)

        print("\n[TEST] REPO READ SUCCESS")
        return 0
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
