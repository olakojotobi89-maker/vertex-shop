-- =================================================================
-- MIGRATION: ENABLE CUSTOMER ORDER TRACKING
--
-- This migration adds the necessary Row Level Security (RLS)
-- policies to allow authenticated customers to read their own
-- orders, order items, and customer profile, without being able
-- to see data belonging to other customers.
--
-- IT IS SAFE TO RUN THIS MIGRATION. It only adds new policies
-- and does not remove or alter existing admin policies.
-- =================================================================

-- STEP 1: Create a helper function in the `auth` schema to securely
-- get the `id` from the `public.customers` table corresponding to the
-- currently authenticated user. This is more efficient than subqueries
-- inside RLS policies.
CREATE OR REPLACE FUNCTION auth.customer_id()
RETURNS uuid
LANGUAGE sql
STABLE -- Use STABLE as it performs a read and is consistent within a transaction.
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT id FROM customers WHERE auth_user_id = auth.uid() LIMIT 1;
$$;


-- STEP 2: Enable RLS on tables if not already enabled.
-- This is idempotent and safe to run even if RLS is already on.
ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;


-- STEP 3: Add SELECT policies for authenticated customers.

-- Policy: Allow users to read their OWN customer profile.
DROP POLICY IF EXISTS "Allow authenticated customer to read their own profile" ON public.customers;
CREATE POLICY "Allow authenticated customer to read their own profile"
ON public.customers FOR SELECT
TO authenticated
USING (auth_user_id = auth.uid());

-- Policy: Allow users to read their OWN orders.
DROP POLICY IF EXISTS "Allow authenticated customer to read their own orders" ON public.orders;
CREATE POLICY "Allow authenticated customer to read their own orders"
ON public.orders FOR SELECT
TO authenticated
USING (customer_id = auth.customer_id());

-- Policy: Allow users to read order_items belonging to their OWN orders.
DROP POLICY IF EXISTS "Allow authenticated customer to read their own order items" ON public.order_items;
CREATE POLICY "Allow authenticated customer to read their own order items"
ON public.order_items FOR SELECT
TO authenticated
USING (
  order_id IN (
    SELECT id FROM public.orders WHERE customer_id = auth.customer_id()
  )
);