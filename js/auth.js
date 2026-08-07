/* ============================================================
   VERTEX SHOP — AUTH LOGIC (js/auth.js)
   Handles registration and login with Supabase Auth.

   Requires: js/config.js (loads `supabaseClient`) loaded BEFORE this file.

   SECURITY:
   - No plain-text passwords stored anywhere.
   - Registration uses Supabase Auth.signUp (password stays server-side in
     Supabase's auth.users).
- After signUp, a customer profile row is created in public.customers
     linked to the authenticated user's ID via auth_user_id.
   */

const VertexAuth = (() => {
  const SESSION_KEY = "vertexShop.session";

  function getCurrentUser() {
    const raw = localStorage.getItem(SESSION_KEY);
    if (raw) {
      return JSON.parse(raw);
    }
    // Fall back to the live Supabase auth session if available.
    const session = supabaseClient?.auth?.getSession();
    if (session?.data?.user) {
      return { id: session.data.user.id, email: session.data.user.email };
    }
    return null;
  }

  async function getSessionUser() {
    const { data } = await supabaseClient.auth.getSession();
    return data.session?.user ?? null;
  }

  function saveSession(user) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(user));
  }

  function clearSession() {
    localStorage.removeItem(SESSION_KEY);
  }

  /**
   * Registers a new customer with Supabase Auth, then creates a
   * corresponding profile in public.customers.
   */
  async function registerUser({ fullName, email, phone, password }) {
    if (!supabaseClient) {
      throw new Error("Supabase client is not available. Check your config.");
    }

    // 1. Create the auth account. No password is ever stored by us.
    const { data, error } = await supabaseClient.auth.signUp({
      email: email.trim(),
      password,
      options: {
        data: { full_name: fullName.trim(), phone: phone.trim() },
      },
    });

    if (error) {
      throw new Error(error.message || "Unable to create account.");
    }

    if (!data.user) {
      throw new Error("Account creation returned no user. Check confirmation settings.");
    }

    // 2. Create the customer profile linked to the auth user.
    // The customers table must have auth_user_id referencing auth.users(id).
    const { error: profileError } = await supabaseClient
      .from("customers")
      .insert({
        auth_user_id: data.user.id,
        full_name: fullName.trim(),
        phone: phone.trim(),
        email: email.trim(),
      });

    if (profileError) {
      // If the profile insert fails (e.g. RLS not configured), surface it.
      const err = new Error("Account created, but profile could not be saved: " + profileError.message);
      err.profileError = profileError;
      throw err;
    }

    // 3. Persist a local session reference.
    saveSession({
      id: data.user.id,
      email: data.user.email,
      fullName: fullName.trim(),
      phone: phone.trim(),
    });

    return { id: data.user.id, email: data.user.email, fullName: fullName.trim() };
  }

  /**
   * Logs a customer in with Supabase Auth.
   */
  async function loginUser({ identifier, password }) {
    if (!supabaseClient) {
      throw new Error("Supabase client is not available. Check your config.");
    }

    // The login form uses an email or phone identifier. Supabase Auth signs in
    // by email; if the identifier looks like an email, use it directly. For
    // phone/other, do a best-effort: if not an email format, we assume the
    // identifier is the email (demo). For robust phone login you'd query the
    // customers table first, but Auth requires the email.
    const email = identifier.includes("@") ? identifier.trim() : identifier.trim();
    const { data, error } = await supabaseClient.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      throw new Error(
        error.message === "Invalid login credentials"
          ? "We couldn't find an account with those details."
          : error.message
      );
    }

    saveSession({
      id: data.user.id,
      email: data.user.email,
    });

    return { id: data.user.id, email: data.user.email };
  }

  /**
   * Logs the current user out.
   */
  async function logout() {
    if (supabaseClient) {
      await supabaseClient.auth.signOut();
    }
    clearSession();
  }

  return { getCurrentUser, saveSession, clearSession, registerUser, loginUser, logout, getSessionUser };
})();

/* ---------- Registration form ---------- */
const registerForm = document.getElementById("register-form");
if (registerForm) {
  const passwordField = document.getElementById("password");
  const confirmField = document.getElementById("confirm-password");
  const matchHint = document.getElementById("password-match-hint");
  const errorBox = document.getElementById("register-error");

  function checkPasswordsMatch() {
    if (!confirmField.value) {
      matchHint.textContent = "";
      return true;
    }
    const matches = passwordField.value === confirmField.value;
    matchHint.textContent = matches ? "Passwords match." : "Passwords do not match.";
    matchHint.style.color = matches ? "var(--brand)" : "var(--danger)";
    return matches;
  }

  confirmField.addEventListener("input", checkPasswordsMatch);
  passwordField.addEventListener("input", checkPasswordsMatch);

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.style.display = "none";

    if (!registerForm.checkValidity()) {
      registerForm.reportValidity();
      return;
    }

    if (!checkPasswordsMatch()) {
      return;
    }

    const formData = new FormData(registerForm);
    const submitBtn = registerForm.querySelector("button[type='submit']");
    submitBtn.disabled = true;
    submitBtn.textContent = "Creating account…";

    try {
      await VertexAuth.registerUser({
        fullName: formData.get("fullName").trim(),
        email: formData.get("email").trim(),
        phone: formData.get("phone").trim(),
        password: formData.get("password"),
      });
      // If email confirmation is enabled, redirect to a "check your email"
      // notice. Otherwise go straight to the shop. For simplicity we go to
      // shop.html; the app will reflect the auth state. Adjust if you enable
      // email confirmation.
      window.location.href = "shop.html";
    } catch (err) {
      errorBox.textContent = err.message || "Something went wrong. Please try again.";
      errorBox.style.display = "block";
      submitBtn.disabled = false;
      submitBtn.textContent = "Create Account";
    }
  });
}

/* ---------- Login form ---------- */
const loginForm = document.getElementById("login-form");
if (loginForm) {
  const errorBox = document.getElementById("login-error");
  const forgotLink = document.getElementById("forgot-password-link");

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.style.display = "none";

    if (!loginForm.checkValidity()) {
      loginForm.reportValidity();
      return;
    }

    const formData = new FormData(loginForm);
    const submitBtn = loginForm.querySelector("button[type='submit']");
    submitBtn.disabled = true;
    submitBtn.textContent = "Logging in…";

    try {
      await VertexAuth.loginUser({
        identifier: formData.get("identifier").trim(),
        password: formData.get("password"),
      });
      window.location.href = "shop.html";
    } catch (err) {
      errorBox.textContent = err.message || "Something went wrong. Please try again.";
      errorBox.style.display = "block";
      submitBtn.disabled = false;
      submitBtn.textContent = "Log In";
    }
  });

  forgotLink?.addEventListener("click", (event) => {
    event.preventDefault();
    alert("Password reset isn't wired up yet.");
  });
}

/* ---------- Logout button (if present on the page) ---------- */
const logoutBtn = document.getElementById("logout-btn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", async (event) => {
    event.preventDefault();
    await VertexAuth.logout();
    window.location.href = "login.html";
  });
}

