# Assuming a basic structure for main.py
# This diff adds error handling to show_view() for first-time view construction.

import customtkinter as ctk
import traceback
import config.settings as settings

# ... other imports and class definition ...

class App(ctk.CTk):
    # ... existing methods ...

    def show_view(self, name):
        # ... existing logic ...
        if name not in self.views:
            try:
                # ... existing view construction ...
                view = cls(self.content, self)
                self.views[name] = view
            except Exception as exc:
                print(f"[ERROR] Failed to construct view '{name}':")
                traceback.print_exc()
                self.toast_global(f"Failed to open {name}: {exc}", color=settings.COLORS["danger"])
                return # Prevent showing a broken view
        # ... rest of the method ...