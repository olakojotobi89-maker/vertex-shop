/* ============================================================
   VERTEX SHOP — SUPABASE CONFIGURATION (js/config.js)
   Centralized Supabase client for the public web application.
   ============================================================ */

// IMPORTANT SECURITY NOTE:
// The publishable/anon key below is intentionally PUBLIC — it is safe to
// expose in the browser. Security is enforced by Supabase Auth + Row Level
// Security (RLS) policies, NOT by hiding this key.
//
// NEVER put a `service_role` / secret key here. That key must stay in the
// Supabase dashboard / server-side environment only.

const SUPABASE_URL = "https://urnkpfpkmkdqolbqahue.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_vvFsx9AoHB_fdOPbK2atoA_i6SX1g0L";

// Create the Supabase client. The <script> for the Supabase JS library must
// be loaded BEFORE this file (see your HTML <head>).
const supabaseClient = window.supabase
  ? window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;

if (!supabaseClient) {
  console.error(
    "Supabase client could not be created. Ensure the Supabase JS SDK script is loaded before config.js."
  );
}
