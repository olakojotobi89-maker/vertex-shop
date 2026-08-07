# Vertex Shop — Stage 1 (Public Web App)

Mobile-first HTML/CSS/JS demo of the Vertex Shop ordering platform.

## Structure

```
vertex-shop/
├── index.html      Registration page
├── login.html      Login page
├── shop.html       Main shopping / ordering page
├── css/style.css   Shared design system + all page styles
├── js/auth.js      Registration & login logic (localStorage demo)
├── js/shop.js      Product catalog, cart, checkout logic
└── src/            Put your logo file here as `logo.png`
```

## Running it

No build step needed — open `index.html`, `login.html`, or `shop.html`
directly in a browser, or serve the folder with any static server, e.g.:

```
npx serve .
```

## Add your logo

Drop a file named `logo.png` into `src/`. All three pages already
reference `src/logo.png`; until it exists, a circular "VS" badge is
shown automatically as a fallback.

## Connecting Supabase later

Both `js/auth.js` and `js/shop.js` are structured so the Supabase
integration only touches a few functions:

- `js/auth.js` → `VertexAuth.registerUser()` and `VertexAuth.loginUser()`
  (swap the localStorage calls for `supabaseClient.auth.signUp` /
  `signInWithPassword`).
- `js/shop.js` → `loadProducts()` (swap the static `PRODUCTS` array for
  a `supabaseClient.from('products').select('*')` call) and the
  order-submit handler inside the checkout form listener (swap the
  localStorage write for an insert into an `orders` table).

Everything else — rendering, the cart, categories, search, and the
checkout modal — reads from those functions' return values, so no
other code needs to change when Supabase is wired in.

## Demo data note

Registration/login accounts, cart contents, and placed orders are all
stored in the browser's `localStorage` for this stage, purely so the
three pages work together end-to-end. None of this is shared across
devices or persisted anywhere real yet — that's the job of the
upcoming Supabase + Python admin dashboard stage.
