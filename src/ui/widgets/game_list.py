import tkinter as tk

from ui import theme
from ui.helpers import format_time_control, format_timestamp, game_row_result_text


class GameList(tk.Frame):
    """Scrollable list widget for saved games."""

    def __init__(self, master, *, on_continue, on_review):
        """Create the list widget with callbacks for row actions."""
        super().__init__(master, bg=theme.COLOR_PANEL)
        self.on_continue = on_continue
        self.on_review = on_review

        self.canvas = tk.Canvas(self, bg=theme.COLOR_PANEL, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=theme.COLOR_PANEL)
        self.content_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._resize_content)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _resize_content(self, event):
        self.canvas.itemconfigure(self.content_window, width=event.width)

    def set_games(self, games):
        """Replace the displayed rows with ``games``."""
        for child in self.content.winfo_children():
            child.destroy()

        if not games:
            tk.Label(
                self.content,
                text="No saved games yet.",
                bg=theme.COLOR_PANEL,
                fg=theme.COLOR_MUTED,
                font=theme.FONT_BODY,
            ).pack(anchor="w", padx=theme.SPACE_MD, pady=theme.SPACE_MD)
            return

        for game_row in games:
            self._add_game_row(game_row)

    def _add_game_row(self, game_row):
        card = tk.Frame(self.content, bg=theme.COLOR_BG, bd=1, relief="solid")
        card.pack(fill="x", padx=theme.SPACE_SM, pady=theme.SPACE_SM)

        header = tk.Frame(card, bg=theme.COLOR_BG)
        header.pack(fill="x", padx=theme.SPACE_MD, pady=(theme.SPACE_MD, theme.SPACE_XS))
        tk.Label(
            header,
            text=f"Game #{game_row['id']}",
            bg=theme.COLOR_BG,
            fg=theme.COLOR_TEXT,
            font=theme.FONT_SUBTITLE,
        ).pack(side="left")
        tk.Label(
            header,
            text=game_row_result_text(game_row),
            bg=theme.COLOR_BG,
            fg=theme.COLOR_ACCENT_ALT,
            font=theme.FONT_SMALL,
        ).pack(side="right")

        metadata = [
            f"Created: {format_timestamp(game_row.get('created_at'))}",
            f"Moves: {game_row.get('move_count', 0)}",
            f"Clock: {format_time_control(game_row.get('clock_enabled'), game_row.get('initial_seconds'), game_row.get('increment_seconds'))}",
        ]
        tk.Label(
            card,
            text=" | ".join(metadata),
            justify="left",
            anchor="w",
            bg=theme.COLOR_BG,
            fg=theme.COLOR_MUTED,
            font=theme.FONT_SMALL,
        ).pack(fill="x", padx=theme.SPACE_MD)

        actions = tk.Frame(card, bg=theme.COLOR_BG)
        actions.pack(fill="x", padx=theme.SPACE_MD, pady=(theme.SPACE_SM, theme.SPACE_MD))
        tk.Button(actions, text="Review", command=lambda game_id=game_row["id"]: self.on_review(game_id)).pack(side="left")
        if game_row.get("status") == "ongoing":
            tk.Button(actions, text="Continue", command=lambda game_id=game_row["id"]: self.on_continue(game_id)).pack(side="left", padx=(theme.SPACE_SM, 0))
