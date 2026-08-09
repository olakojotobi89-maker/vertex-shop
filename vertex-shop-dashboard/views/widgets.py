"""
Reusable UI widgets for a consistent, professional look across all views.

These helpers build on CustomTkinter to create cards, tables, status badges,
dialogs and buttons with a shared visual language.
"""
import customtkinter as ctk
from PIL import Image

import config.settings as settings
from utils import helpers


# ===========================================================================
# Styling constants
# ===========================================================================
FONT = "Segoe UI"
FONT_SEMIBOLD = "Segoe UI Semibold"
FONT_BOLD = "Segoe UI Bold"


def font(size=13, weight="normal"):
    return (FONT_SEMIBOLD if weight == "semibold" else FONT_BOLD if weight == "bold" else FONT, size)


def make_button(parent, text, command=None, color=None, fg_color=None,
                width=120, height=36, font_size=13, corner_radius=8,
                border=False, border_color=None, text_color=None):
    """Create a consistent primary/secondary button."""
    fg = fg_color or settings.COLORS["primary"]
    hover = settings.COLORS["primary_hover"]
    if border:
        return ctk.CTkButton(
            parent, text=text, command=command, width=width, height=height,
            corner_radius=corner_radius, font=font(font_size, "semibold"),
            fg_color="transparent", border_width=1, border_color=border_color or fg,
            hover_color=settings.COLORS["card_border"],
            text_color=text_color or fg,
        )
    return ctk.CTkButton(
        parent, text=text, command=command, width=width, height=height,
        corner_radius=corner_radius, font=font(font_size, "semibold"),
        fg_color=fg, hover_color=hover, text_color=text_color or "#FFFFFF",
    )


def make_card(parent, padx=0, pady=0, fill="both", expand=True, min_height=0):
    """A 'card' container with a distinct background/border."""
    card = ctk.CTkFrame(parent, fg_color=settings.COLORS["card_bg"],
                        corner_radius=14, border_width=1,
                        border_color=settings.COLORS["card_border"])
    card.grid_columnconfigure(0, weight=1)
    card.pack(fill=fill, expand=expand, padx=padx, pady=pady)
    if min_height:
        card.configure(height=min_height)
    return card


def make_row_grid(parent, total_cols=4, padx=12, pady=6):
    for i in range(total_cols):
        parent.grid_columnconfigure(i, weight=1)


# ===========================================================================
# Stat/dashboard card
# ===========================================================================
class StatCard(ctk.CTkFrame):
    """A summary statistic card (icon, label, value)."""

    def __init__(self, parent, label, value, icon="", accent=None, **kwargs):
        super().__init__(parent, fg_color=settings.COLORS["card_bg"],
                         corner_radius=14, border_width=1,
                         border_color=settings.COLORS["card_border"])
        self.grid_columnconfigure(1, weight=1)
        accent = accent or settings.COLORS["primary"]

        # Icon badge
        icon_frame = ctk.CTkFrame(self, width=44, height=44, corner_radius=12,
                                  fg_color=_with_alpha(accent))
        icon_frame.pack_propagate(False)
        icon_frame.grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=16, sticky="nw")
        icon_label = ctk.CTkLabel(icon_frame, text=icon, font=font(20, "bold"),
                                  text_color=accent)
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Label + value
        lbl = ctk.CTkLabel(self, text=label.upper(), font=font(11, "semibold"),
                           text_color=settings.COLORS["text_muted"])
        lbl.grid(row=0, column=1, padx=(0, 16), pady=(16, 0), sticky="w")
        val = ctk.CTkLabel(self, text=str(value), font=font(24, "bold"),
                           text_color=settings.COLORS["text"])
        val.grid(row=1, column=1, padx=(0, 16), pady=(0, 16), sticky="w")


def _with_alpha(hex_color, alpha=0.16):
    """Return a translucent version of a hex color blended on dark bg."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    # blend the status/accent color toward the card background
    bg = (30, 35, 43)
    nr = round(r * 0.30 + bg[0] * 0.70)
    ng = round(g * 0.30 + bg[1] * 0.70)
    nb = round(b * 0.30 + bg[2] * 0.70)
    return f"#{nr:02x}{ng:02x}{nb:02x}"


# ===========================================================================
# Status badge
# ===========================================================================
class StatusBadge(ctk.CTkFrame):
    """Colored pill representing an order/product status."""

    def __init__(self, parent, status, **kwargs):
        color = helpers.status_badge_color(status)
        super().__init__(parent, fg_color=_with_alpha(color),
                         corner_radius=10,
                         height=26)
        self.pack_propagate(False)
        dot = ctk.CTkFrame(self, width=8, height=8, corner_radius=4,
                           fg_color=color)
        dot.place(relx=0.18, rely=0.5, anchor="center")
        lbl = ctk.CTkLabel(self, text=status, font=font(11, "semibold"),
                           text_color=color)
        lbl.pack(padx=18, pady=3)


# ===========================================================================
# Page header
# ===========================================================================
class PageHeader(ctk.CTkFrame):
    def __init__(self, parent, title, subtitle="", action_button=None):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.title_lbl = ctk.CTkLabel(self, text=title, font=font(22, "bold"),
                                 text_color=settings.COLORS["text"], anchor="w")
        self.title_lbl.grid(row=0, column=0, sticky="w")
        if subtitle:
            self.sub_lbl = ctk.CTkLabel(self, text=subtitle, font=font(13),
                                   text_color=settings.COLORS["text_muted"], anchor="w")
            self.sub_lbl.grid(row=1, column=0, sticky="w", pady=(4, 0))
        else:
            self.sub_lbl = None # Ensure it's initialized even if no subtitle
        if action_button:
            action_button.grid(row=0, column=1, rowspan=2, sticky="e")

    def set_title(self, title):
        self.title_lbl.configure(text=title)

    def set_subtitle(self, subtitle):
        if not self.sub_lbl: # Create if it didn't exist before
            self.sub_lbl = ctk.CTkLabel(self, text=subtitle, font=font(13),
                                        text_color=settings.COLORS["text_muted"], anchor="w")
            self.sub_lbl.grid(row=1, column=0, sticky="w", pady=(4, 0))
        else:
            self.sub_lbl.configure(text=subtitle)


# ===========================================================================
# Search bar
# ===========================================================================
class SearchBar(ctk.CTkFrame):
    def __init__(self, parent, placeholder="Search...", command=None, width=320):
        super().__init__(parent, fg_color=settings.COLORS["card_bg"],
                         corner_radius=10, border_width=1,
                         border_color=settings.COLORS["card_border"])
        self.command = command
        self.entry = ctk.CTkEntry(
            self, placeholder_text=placeholder, font=font(13),
            fg_color="transparent", border_width=0, width=width, height=36,
            placeholder_text_color=settings.COLORS["text_muted"],
        )
        self.entry.pack(side="left", padx=(12, 6), fill="x", expand=True)
        self.result = ctk.CTkLabel(self, text="", font=font(12),
                                   text_color=settings.COLORS["text_muted"])
        self.result.pack(side="right", padx=(6, 12))
        if command:
            self.entry.bind("<KeyRelease>", lambda e: self._trigger())
            self.entry.bind("<Return>", lambda e: self._trigger())

    def _trigger(self):
        if self.command:
            self.command(self.entry.get())

    def get(self):
        return self.entry.get()

    def set_result(self, text):
        self.result.configure(text=text)


# ===========================================================================
# Simple confirm dialog
# ===========================================================================
def confirm_dialog(parent, message, title="Are you sure?", accent="#EF4444",
                   confirm_text="Delete"):
    """
    Show a modal confirmation dialog. Returns True if the user confirms.
    Blocks the caller until closed.
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("380x190")
    dialog.resizable(False, False)
    dialog.grab_set()
    dialog.transient(parent)
    result = {"confirmed": False}

    dialog.grid_columnconfigure(0, weight=1)
    title_lbl = ctk.CTkLabel(dialog, text=title, font=font(18, "bold"),
                             text_color=settings.COLORS["text"])
    title_lbl.pack(pady=(26, 6), padx=20)
    msg_lbl = ctk.CTkLabel(dialog, text=message, font=font(13),
                           text_color=settings.COLORS["text_muted"],
                           wraplength=330, justify="center")
    msg_lbl.pack(padx=24, pady=(0, 18))

    btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_row.pack(pady=(0, 22))

    def on_cancel():
        result["confirmed"] = False
        dialog.destroy()

    def on_confirm():
        result["confirmed"] = True
        dialog.destroy()

    make_button(btn_row, "Cancel", command=on_cancel, fg_color=settings.COLORS["card_border"],
                text_color=settings.COLORS["text"], width=120).pack(side="left", padx=8)
    make_button(btn_row, confirm_text, command=on_confirm, fg_color=accent,
                width=120).pack(side="left", padx=8)

    # Center over parent
    dialog.update_idletasks()
    try:
        x = parent.winfo_rootx() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
    except Exception:
        pass

    parent.wait_window(dialog)
    return result["confirmed"]


# ===========================================================================
# Toast / notification snackbar
# ===========================================================================
class Toast(ctk.CTkLabel):
    """A short-lived message that appears at the bottom of a window."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="", font=font(13, "semibold"),
                         text_color="#FFFFFF", fg_color="#232933",
                         corner_radius=10, padx=18, pady=10, **kwargs)
        self._after_id = None
        self.place(relx=0.5, rely=0.97, anchor="s")
        self.place_forget()

    def show(self, message, duration=2400, color="#22C55E"):
        if self._after_id:
            self.after_cancel(self._after_id)
        self.configure(text="  " + message, fg_color=color)
        self.place(relx=0.5, rely=0.97, anchor="s")
        self._after_id = self.after(duration, self._hide)

    def _hide(self):
        self.place_forget()
        self._after_id = None


# ===========================================================================
# Naira currency entry
# ===========================================================================
class NairaEntry(ctk.CTkFrame):
    """A formatted currency entry for Nigerian Naira (₦)."""

    def __init__(self, parent, placeholder_text="", **kwargs):
        super().__init__(parent, fg_color=settings.COLORS["card_border"],
                         border_width=0, height=40, corner_radius=8, **kwargs)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.symbol = ctk.CTkLabel(self, text="₦", font=font(15, "semibold"),
                                   text_color=settings.COLORS["text_muted"])
        self.symbol.grid(row=0, column=0, padx=(12, 5))

        self.entry = ctk.CTkEntry(
            self, font=font(14), border_width=0,
            text_color=settings.COLORS["text"], placeholder_text=placeholder_text,
            fg_color=settings.COLORS["card_border"]  # Use a visible background
        )
        self.entry.grid(row=0, column=1, sticky="ew")

        self.entry.bind("<KeyRelease>", self._on_key_release)

    def _on_key_release(self, event=None):
        """Format the number with commas as the user types."""
        current_text = self.entry.get().replace(",", "")
        if not current_text.isdigit():
            # Allow backspace/delete to clear the field
            if not current_text:
                return
            # Remove non-digit characters
            current_text = "".join(filter(str.isdigit, current_text))

        if current_text:
            formatted_text = f"{int(current_text):,}"
            if self.entry.get() != formatted_text:
                cursor_pos = self.entry.index(ctk.INSERT)
                self.entry.delete(0, ctk.END)
                self.entry.insert(0, formatted_text)
                self.entry.icursor(cursor_pos)

    def get_amount(self) -> str:
        return self.entry.get().replace(",", "")

    def set_amount(self, amount: float):
        self.entry.insert(0, f"{int(amount):,}")
