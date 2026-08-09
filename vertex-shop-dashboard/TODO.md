# Vertex Shop Dashboard — Supabase Orders Fix TODO

## Progress Tracking

- [x] 0. Investigate codebase & identify root causes
- [x] 1. Plan approved by user
- [x] 2. Create `.env` with publishable Supabase credentials
- [x] 3. Install `supabase` + `python-dotenv` packages
- [x] 4. Update `requirements.txt`
- [x] 5. Rewrite `database/supabase_client.py` (admin auth, JWT role check)
- [x] 6. Add `database/supabase_storage.py` (image upload helper, no silent errors)
- [x] 7. Rewrite `database/database.py` (remove SQLite + seeding; Supabase only)
- [x] 8. Update `database/supabase_repository.py` (RLS-aware, raise on unavailable)
- [x] 9. Add `views/login.py` (admin login gate)
- [x] 10. Update `main.py` (require admin login)
- [x] 11. Fix `views/add_product.py` (real image upload, show errors)
- [x] 12. Update `views/notifications.py` (Supabase Realtime, remove fake orders)
- [x] 13. Update `views/settings.py` (connection test: Supabase/Database/Storage)
- [x] 14. Update `js/shop.js` (order customer_id references customers.id)
- [x] 15. Write corrected `supabase_migration.sql`
- [x] 16. Smoke-test imports & application boot

## Round 2 — Fix dashboard reading of real Supabase orders

- [x] 17. Normalize order status constants in `config/settings.py` to lowercase DB values
- [x] 18. Make order/order-item reads run under the admin-authenticated session in `database/supabase_repository.py`
- [x] 19. Set `Order` model default status to `pending` in `models/order.py`
- [x] 20. Remove stale "Local SQLite (demo mode)" wording in `views/settings.py`
- [x] 21. Verify: dashboard authenticates as admin and reads real orders from public.orders / public.order_items
- [x] 22. Verify: no demo/SQLite orders displayed; status workflow + update still works
