import tkinter as tk

from ui import theme
from ui.widgets.game_list import GameList


class HistoryView(tk.Frame):
    """View listing saved games with simple status filtering."""

    def __init__(self, master, *, app):
        """Build the history view."""
        super().__init__(master, bg=theme.COLOR_BG, padx=theme.SPACE_XL, pady=theme.SPACE_XL)
        self.app = app
        self.filter_var = tk.StringVar(value="all")

        self._build_layout()
        self.refresh()

    def _build_layout(self):
        outer = tk.Frame(self, bg=theme.COLOR_BG)
        outer.pack(fill="both", expand=True)
        outer.rowconfigure(1, weight=1)
        outer.columnconfigure(0, weight=1)

        top = tk.Frame(outer, bg=theme.COLOR_PANEL, bd=1, relief="solid")
        top.grid(row=0, column=0, sticky="ew", pady=(0, theme.SPACE_LG))
        tk.Label(top, text="Game History", bg=theme.COLOR_PANEL, font=theme.FONT_TITLE).pack(
            anchor="w", padx=theme.SPACE_LG, pady=(theme.SPACE_MD, theme.SPACE_SM)
        )

        filters = tk.Frame(top, bg=theme.COLOR_PANEL)
        filters.pack(anchor="w", padx=theme.SPACE_LG, pady=(0, theme.SPACE_MD))
        for label, value in (("All", "all"), ("Ongoing", "ongoing"), ("Finished", "finished")):
            tk.Radiobutton(
                filters,
                text=label,
                value=value,
                variable=self.filter_var,
                command=self.refresh,
                bg=theme.COLOR_PANEL,
            ).pack(side="left", padx=(0, theme.SPACE_MD))

        self.game_list = GameList(outer, on_continue=self.app.continue_game, on_review=self.app.open_review)
        self.game_list.grid(row=1, column=0, sticky="nsew")

        controls = tk.Frame(outer, bg=theme.COLOR_PANEL, bd=1, relief="solid")
        controls.grid(row=2, column=0, sticky="ew", pady=(theme.SPACE_LG, 0))
        tk.Button(controls, text="Back", command=self.app.go_back).pack(side="right", padx=theme.SPACE_MD, pady=theme.SPACE_MD)
        tk.Button(controls, text="Quit", command=self.app.quit_app).pack(side="right", pady=theme.SPACE_MD)

    def refresh(self):
        """Reload the game list using the active filter."""
        games = self.app.service.list_games(limit=500)
        filter_value = self.filter_var.get()
        if filter_value != "all":
            games = [game_row for game_row in games if game_row.get("status") == filter_value]
        self.game_list.set_games(games)

    def on_show(self):
        """Refresh the history list when the view becomes visible."""
        self.refresh()

    def on_hide(self):
        return
