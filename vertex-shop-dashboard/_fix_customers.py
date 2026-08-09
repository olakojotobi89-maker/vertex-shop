import io

path = r"D:/Vertex shop/vertex-shop-dashboard/database/supabase_repository.py"

with io.open(path, "r", encoding="utf-8-sig") as f:
    content = f.read()

# Fix 1: _customers_from_orders selects customer_email which does not exist in orders.
old1 = 'resp = self.client.table("orders").select(\n            "id, customer_name, customer_phone, customer_email, total_amount, status, created_at"\n        ).order("created_at", desc=True).execute()'
new1 = 'resp = self.client.table("orders").select(\n            "id, customer_name, customer_phone, total_amount, status, created_at"\n        ).order("created_at", desc=True).execute()'

if old1 in content:
    content = content.replace(old1, new1)
    print("Fixed _customers_from_orders select.")
else:
    print("WARNING: _customers_from_orders select pattern not found.")

# Fix 2: remove customer_email from the grouped dict building (it referenced r.get("customer_email"))
old2 = '                    "email": r.get("customer_email", ""),'
new2 = '                    "email": "",'
if old2 in content:
    content = content.replace(old2, new2)
    print("Fixed _customers_from_orders grouped email.")
else:
    print("WARNING: grouped email pattern not found.")

with io.open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done.")
