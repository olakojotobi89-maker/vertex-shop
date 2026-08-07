-- ============================================================================
-- VERTEX SHOP - SUPABASE MIGRATION
-- Run this in the Supabase SQL Editor.
-- Configures RLS policies and the product-images storage bucket.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. STORAGE BUCKET: product-images
-- ----------------------------------------------------------------------------
INSERT INTO storage.buckets (id, name, public)
VALUES ('product-images', 'product-images', true)
ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS "product-images-public-read" ON storage.objects;
CREATE POLICY "product-images-public-read"
ON storage.objects FOR SELECT
USING (bucket_id = 'product-images');

DROP POLICY IF EXISTS "product-images-admin-upload" ON storage.objects;
CREATE POLICY "product-images-admin-upload"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'product-images'
    AND (auth.jwt() ->> 'app_role') = 'admin'
);

DROP POLICY IF EXISTS "product-images-admin-manage" ON storage.objects;
CREATE POLICY "product-images-admin-manage"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'product-images' AND (auth.jwt() ->> 'app_role') = 'admin');

DROP POLICY IF EXISTS "product-images-admin-delete" ON storage.objects;
CREATE POLICY "product-images-admin-delete"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'product-images' AND (auth.jwt() ->> 'app_role') = 'admin');

-- ----------------------------------------------------------------------------
-- 2. CATEGORIES - RLS
-- ----------------------------------------------------------------------------
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "categories-public-read" ON public.categories;
CREATE POLICY "categories-public-read"
ON public.categories FOR SELECT
USING (true);

DROP POLICY IF EXISTS "categories-admin-write" ON public.categories;
CREATE POLICY "categories-admin-write"
ON public.categories FOR ALL
TO authenticated
USING ((auth.jwt() ->> 'app_role') = 'admin')
WITH CHECK ((auth.jwt() ->> 'app_role') = 'admin');

-- ----------------------------------------------------------------------------
-- 3. PRODUCTS - RLS
-- ----------------------------------------------------------------------------
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "products-public-read" ON public.products;
CREATE POLICY "products-public-read"
ON public.products FOR SELECT
USING (true);

DROP POLICY IF EXISTS "products-admin-write" ON public.products;
CREATE POLICY "products-admin-write"
ON public.products FOR ALL
TO authenticated
USING ((auth.jwt() ->> 'app_role') = 'admin')
WITH CHECK ((auth.jwt() ->> 'app_role') = 'admin');

-- ----------------------------------------------------------------------------
-- 4. CUSTOMERS - RLS
-- ----------------------------------------------------------------------------
ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "customers-read-own" ON public.customers;
CREATE POLICY "customers-read-own"
ON public.customers FOR SELECT
TO authenticated
USING (auth.uid() = auth_user_id);

DROP POLICY IF EXISTS "customers-insert-own" ON public.customers;
CREATE POLICY "customers-insert-own"
ON public.customers FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = auth_user_id);

DROP POLICY IF EXISTS "customers-admin-read" ON public.customers;
CREATE POLICY "customers-admin-read"
ON public.customers FOR SELECT
TO authenticated
USING ((auth.jwt() ->> 'app_role') = 'admin');

-- ----------------------------------------------------------------------------
-- 5. ORDERS - RLS
-- ----------------------------------------------------------------------------
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "orders-read-own" ON public.orders;
CREATE POLICY "orders-read-own"
ON public.orders FOR SELECT
TO authenticated
USING (auth.uid() = customer_id);

DROP POLICY IF EXISTS "orders-insert-own" ON public.orders;
CREATE POLICY "orders-insert-own"
ON public.orders FOR INSERT
TO authenticated
WITH CHECK (
    (customer_id IS NULL) OR (auth.uid() = customer_id)
);

DROP POLICY IF EXISTS "orders-admin-read" ON public.orders;
CREATE POLICY "orders-admin-read"
ON public.orders FOR SELECT
TO authenticated
USING ((auth.jwt() ->> 'app_role') = 'admin');

DROP POLICY IF EXISTS "orders-admin-update" ON public.orders;
CREATE POLICY "orders-admin-update"
ON public.orders FOR UPDATE
TO authenticated
USING ((auth.jwt() ->> 'app_role') = 'admin')
WITH CHECK ((auth.jwt() ->> 'app_role') = 'admin');

-- ----------------------------------------------------------------------------
-- 6. ORDER_ITEMS - RLS
-- ----------------------------------------------------------------------------
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "order_items-insert-own" ON public.order_items;
CREATE POLICY "order_items-insert-own"
ON public.order_items FOR INSERT
TO authenticated
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.orders o
        WHERE o.id = order_id AND (o.customer_id IS NULL OR auth.uid() = o.customer_id)
    )
);

DROP POLICY IF EXISTS "order_items-admin-read" ON public.order_items;
CREATE POLICY "order_items-admin-read"
ON public.order_items FOR SELECT
TO authenticated
USING ((auth.jwt() ->> 'app_role') = 'admin');

DROP POLICY IF EXISTS "order_items-read-own" ON public.order_items;
CREATE POLICY "order_items-read-own"
ON public.order_items FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.orders o
        WHERE o.id = order_id AND auth.uid() = o.customer_id
    )
);

-- ----------------------------------------------------------------------------
-- 7. REALTIME - enable orders for the Python dashboard
-- ----------------------------------------------------------------------------
ALTER PUBLICATION supabase_realtime ADD TABLE public.orders;

-- ----------------------------------------------------------------------------
-- 8. ADMIN ROLE SETUP (run after creating the admin account)
-- ----------------------------------------------------------------------------
-- UPDATE auth.users
-- SET raw_app_meta_data = jsonb_set(
--         COALESCE(raw_app_meta_data, '{}'::jsonb),
--         '{app_role}',
--         '"admin"'
--     )
-- WHERE email = 'admin@vertexshop.com';

