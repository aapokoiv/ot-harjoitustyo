import tkinter as tk

from ui import theme


class PromotionDialog:
    """Modal dialog for choosing a pawn promotion piece.

    Attributes:
        parent: Parent Tk widget.
        piece_images (dict[str, tk.PhotoImage]): Loaded piece images.
        color (str): Promoting side, either "w" or "b".
        result (str): Selected promotion symbol.
    """

    def __init__(self, parent, *, piece_images, color):
        """Prepare the dialog state."""
        self.parent = parent
        self.piece_images = piece_images
        self.color = color
        self.result = "Q"

    def show(self):
        """Open the dialog and return the chosen promotion symbol."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Choose Promotion")
        dialog.configure(bg=theme.COLOR_PANEL)
        dialog.transient(self.parent)
        dialog.grab_set()
        dialog.resizable(False, False)

        container = tk.Frame(dialog, bg=theme.COLOR_PANEL, padx=theme.SPACE_XL, pady=theme.SPACE_XL)
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="Promote pawn to",
            bg=theme.COLOR_PANEL,
            fg=theme.COLOR_TEXT,
            font=theme.FONT_TITLE,
        ).pack(pady=(0, theme.SPACE_MD))

        options = [("Queen", "Q"), ("Rook", "R"), ("Bishop", "B"), ("Knight", "N")]
        button_row = tk.Frame(container, bg=theme.COLOR_PANEL)
        button_row.pack()

        for label, symbol in options:
            piece_key = f"{self.color}{symbol}"
            button = tk.Button(
                button_row,
                text=label,
                image=self.piece_images.get(piece_key),
                compound="top",
                command=lambda choice=symbol: self._choose(dialog, choice),
            )
            button.pack(side="left", padx=theme.SPACE_SM)

        dialog.protocol("WM_DELETE_WINDOW", lambda: self._choose(dialog, "Q"))
        dialog.update_idletasks()
        self._center(dialog)
        self.parent.wait_window(dialog)
        return self.result

    def _choose(self, dialog, choice):
        self.result = choice
        dialog.destroy()

    def _center(self, dialog):
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        dialog.geometry(f"+{x}+{y}")
