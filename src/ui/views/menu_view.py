import tkinter as tk
from tkinter import messagebox

from ui import theme
from ui.widgets.game_list import GameList


class MenuView(tk.Frame):
    """Main menu view for creating games and opening saved ones.

    Attributes:
        app: Application controller used for navigation and actions.
        clock_enabled_var (tk.BooleanVar): Whether the new game uses a clock.
        increment_var (tk.IntVar): Increment seconds for timed games.
        custom_minutes_var (tk.StringVar): Base time input in minutes.
    """

    PRESET_MINUTES = [1, 3, 5, 10, 15]

    def __init__(self, master, *, app):
        """Build the menu view."""
        super().__init__(master, bg=theme.COLOR_BG, padx=theme.SPACE_XL, pady=theme.SPACE_XL)
        self.app = app
        self.clock_enabled_var = tk.BooleanVar(value=False)
        self.increment_var = tk.IntVar(value=0)
        self.custom_minutes_var = tk.StringVar(value="5")

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_setup_panel()
        self._build_recent_panel()

    def _build_setup_panel(self):
        panel = tk.Frame(self, bg=theme.COLOR_PANEL, bd=1, relief="solid")
        panel.grid(row=0, column=0, sticky="ns", padx=(0, theme.SPACE_LG))

        tk.Label(panel, text="New Game", bg=theme.COLOR_PANEL, fg=theme.COLOR_TEXT, font=theme.FONT_TITLE).pack(
            anchor="w", padx=theme.SPACE_LG, pady=(theme.SPACE_LG, theme.SPACE_MD)
        )

        tk.Checkbutton(
            panel,
            text="Use clock",
            variable=self.clock_enabled_var,
            bg=theme.COLOR_PANEL,
            anchor="w",
            command=self._update_clock_controls,
        ).pack(fill="x", padx=theme.SPACE_LG)

        tk.Label(panel, text="Preset minutes", bg=theme.COLOR_PANEL, fg=theme.COLOR_TEXT, font=theme.FONT_SUBTITLE).pack(
            anchor="w", padx=theme.SPACE_LG, pady=(theme.SPACE_LG, theme.SPACE_SM)
        )

        preset_row = tk.Frame(panel, bg=theme.COLOR_PANEL)
        preset_row.pack(fill="x", padx=theme.SPACE_LG)
        self.preset_buttons = []
        for minutes in self.PRESET_MINUTES:
            button = tk.Button(preset_row, text=str(minutes), width=4, command=lambda value=minutes: self._set_minutes(value))
            button.pack(side="left", padx=(0, theme.SPACE_XS))
            self.preset_buttons.append(button)

        tk.Label(panel, text="Custom minutes", bg=theme.COLOR_PANEL, fg=theme.COLOR_TEXT, font=theme.FONT_SMALL).pack(
            anchor="w", padx=theme.SPACE_LG, pady=(theme.SPACE_LG, theme.SPACE_XS)
        )
        self.custom_entry = tk.Entry(panel, textvariable=self.custom_minutes_var, width=12)
        self.custom_entry.pack(anchor="w", padx=theme.SPACE_LG)

        tk.Label(panel, text="Increment seconds", bg=theme.COLOR_PANEL, fg=theme.COLOR_TEXT, font=theme.FONT_SMALL).pack(
            anchor="w", padx=theme.SPACE_LG, pady=(theme.SPACE_LG, theme.SPACE_XS)
        )
        self.increment_spinbox = tk.Spinbox(panel, from_=0, to=60, textvariable=self.increment_var, width=8)
        self.increment_spinbox.pack(anchor="w", padx=theme.SPACE_LG)

        tk.Button(panel, text="Create Game", command=self._create_game).pack(
            fill="x", padx=theme.SPACE_LG, pady=(theme.SPACE_XL, theme.SPACE_MD)
        )
        tk.Button(panel, text="Open History", command=self.app.open_history).pack(
            fill="x", padx=theme.SPACE_LG, pady=(0, theme.SPACE_MD)
        )
        tk.Button(panel, text="Quit", command=self.app.quit_app).pack(
            fill="x", padx=theme.SPACE_LG, pady=(0, theme.SPACE_LG)
        )

        self._update_clock_controls()

    def _build_recent_panel(self):
        panel = tk.Frame(self, bg=theme.COLOR_PANEL, bd=1, relief="solid")
        panel.grid(row=0, column=1, sticky="nsew")
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        tk.Label(panel, text="Recent Games", bg=theme.COLOR_PANEL, fg=theme.COLOR_TEXT, font=theme.FONT_TITLE).grid(
            row=0, column=0, sticky="w", padx=theme.SPACE_LG, pady=(theme.SPACE_LG, theme.SPACE_MD)
        )

        self.game_list = GameList(panel, on_continue=self.app.continue_game, on_review=self.app.open_review)
        self.game_list.grid(row=1, column=0, sticky="nsew", padx=theme.SPACE_SM, pady=(0, theme.SPACE_SM))

    def _set_minutes(self, minutes):
        self.custom_minutes_var.set(str(minutes))

    def _update_clock_controls(self):
        state = "normal" if self.clock_enabled_var.get() else "disabled"
        self.custom_entry.config(state=state)
        self.increment_spinbox.config(state=state)
        for button in self.preset_buttons:
            button.config(state=state)

    def _create_game(self):
        if self.clock_enabled_var.get():
            try:
                custom_minutes = int(self.custom_minutes_var.get())
            except ValueError:
                messagebox.showerror("Invalid time", "Custom time must be a whole number of minutes.")
                return

            if custom_minutes <= 0:
                messagebox.showerror("Invalid time", "Clock time must be greater than zero.")
                return

        initial_seconds = custom_minutes * 60 if self.clock_enabled_var.get() else None
        self.app.create_game(
            clock_enabled=self.clock_enabled_var.get(),
            initial_seconds=initial_seconds,
            increment_seconds=int(self.increment_var.get()),
        )

    def refresh(self):
        """Reload the recent games list from storage."""
        games = self.app.service.list_games(limit=8)
        self.game_list.set_games(games)

    def on_show(self):
        """Refresh the view when it becomes visible."""
        self.refresh()

    def on_hide(self):
        return
