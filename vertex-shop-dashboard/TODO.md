# Vertex Shop Dashboard — Supabase Migration TODO

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
- [ ] 9. Add `views/login.py` (admin login gate)
- [ ] 10. Update `main.py` (require admin login)
- [ ] 11. Fix `views/add_product.py` (real image upload, show errors)
- [ ] 12. Update `views/notifications.py` (Supabase Realtime, remove fake orders)
- [ ] 13. Update `views/settings.py` (connection test: Supabase/Database/Storage)
- [ ] 14. Update `js/shop.js` (order customer_id references customers.id)
- [ ] 15. Write corrected `supabase_migration.sql`
- [ ] 16. Smoke-test imports & application boot
