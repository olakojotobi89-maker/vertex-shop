-- Fix for admin RLS policies: Correctly access 'app_role' from 'app_metadata' in JWT.
-- This script should be run in the Supabase SQL editor.

-- Policies for public.orders
DROP POLICY IF EXISTS "orders-admin-read" ON public.orders;
CREATE POLICY "orders-admin-read" ON public.orders FOR SELECT TO authenticated USING ((auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin');

DROP POLICY IF EXISTS "orders-admin-update" ON public.orders;
CREATE POLICY "orders-admin-update" ON public.orders FOR UPDATE TO authenticated USING ((auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin') WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin');

-- Policies for public.order_items
DROP POLICY IF EXISTS "order_items-admin-read" ON public.order_items;
CREATE POLICY "order_items-admin-read" ON public.order_items FOR SELECT TO authenticated USING ((auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin');

-- Policies for public.customers
DROP POLICY IF EXISTS "customers-admin-read" ON public.customers;
CREATE POLICY "customers-admin-read" ON public.customers FOR SELECT TO authenticated USING ((auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin');

-- Policies for public.categories
DROP POLICY IF EXISTS "categories-admin-write" ON public.categories;
CREATE POLICY "categories-admin-write" ON public.categories FOR ALL TO authenticated USING ((auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin') WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin');

-- Policies for public.products
DROP POLICY IF EXISTS "products-admin-write" ON public.products;
CREATE POLICY "products-admin-write" ON public.products FOR ALL TO authenticated USING ((auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin') WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin');

-- Policies for storage.objects (product-images bucket)
-- Note: These policies assume the bucket_id is 'product-images'

-- Allow admin to upload new product images
DROP POLICY IF EXISTS "product-images-admin-upload" ON storage.objects;
CREATE POLICY "product-images-admin-upload" ON storage.objects FOR INSERT TO authenticated WITH CHECK (
  bucket_id = 'product-images' AND (auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin'
);

-- Allow admin to update existing product images
DROP POLICY IF EXISTS "product-images-admin-manage" ON storage.objects;
CREATE POLICY "product-images-admin-manage" ON storage.objects FOR UPDATE TO authenticated USING (
  bucket_id = 'product-images' AND (auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin'
) WITH CHECK (
  bucket_id = 'product-images' AND (auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin'
);

-- Allow admin to delete product images
DROP POLICY IF EXISTS "product-images-admin-delete" ON storage.objects;
CREATE POLICY "product-images-admin-delete" ON storage.objects FOR DELETE TO authenticated USING (
  bucket_id = 'product-images' AND (auth.jwt() -> 'app_metadata' ->> 'app_role') = 'admin'
);