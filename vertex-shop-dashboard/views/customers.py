# Assuming a basic structure for views/customers.py
# This diff updates the _select_customer() method to use the new get_customer_orders signature.

import customtkinter as ctk
from database.database import db

# ... other imports and class definition ...

class CustomersView(ctk.CTkFrame):
    # ... existing methods ...

    def _select_customer(self, customer):
        # ... existing logic ...
        # Update this line:
        customer.orders = db.get_customer_orders(customer_id=customer.customer_id, phone=customer.phone, name=customer.name)
        # ... rest of the method ...