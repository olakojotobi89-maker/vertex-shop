import io

path = r"D:/Vertex shop/vertex-shop-dashboard/database/supabase_repository.py"

with io.open(path, "r", encoding="utf-8-sig") as f:
    content = f.read()

# Fix the broken tail of _order_from_sb: the closing paren and order.items
old = '            created_at=r.get("created_at", ""),\n)\n        order.items = items or []\n        return order'
new = '            created_at=r.get("created_at", ""),\n        )\n        order.items = items or []\n        return order'

if old in content:
    content = content.replace(old, new)
    print("Fixed _order_from_sb tail.")
else:
    print("WARNING: _order_from_sb tail pattern not found.")

with io.open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done.")
