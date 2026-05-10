import tkinter as tk
from tkinter import messagebox

from ui import theme
from ui.dialogs.promotion_dialog import PromotionDialog
from ui.helpers import build_move_rows, format_clock_ms, format_time_control, result_text
from ui.widgets.board_widget import BoardWidget


class GameView(tk.Frame):
    """Interactive in-game view for playing and tracking one game.

    Attributes:
        app: Application controller used for navigation and shared resources.
        game: Active :class:`chess.game.Game` instance.
        selected (tuple[int, int] | None): Currently selected square.
        highlighted_moves (set[tuple[int, int]]): Legal destinations to highlight.
        last_move (set[tuple[int, int]] | None): Last move squares for UI highlight.
        poll_id (str | None): Tk callback id for the clock polling loop.
    """

    POLL_MS = 200

    def __init__(self, master, *, app, game):
        """Build the game view for an active game."""
        super().__init__(master, bg=theme.COLOR_BG, padx=theme.SPACE_XL, pady=theme.SPACE_XL)
        self.app = app
        self.game = game
        self.selected = None
        self.highlighted_moves = set()
        self.last_move = None
        self.poll_id = None
        self.move_records = self.app.service.get_moves(self.game.game_id) if self.game.game_id is not None else []
        if self.move_records:
            last = self.move_records[-1]
            self.last_move = {(last["from_row"], last["from_col"]), (last["to_row"], last["to_col"])}

        self.status_var = tk.StringVar()
        self.white_clock_var = tk.StringVar()
        self.black_clock_var = tk.StringVar()
        self.meta_var = tk.StringVar()

        self._build_layout()
        self._refresh()

    def _build_layout(self):
        outer = tk.Frame(self, bg=theme.COLOR_BG)
        outer.pack(fill="both", expand=True)
        outer.rowconfigure(1, weight=1)
        outer.columnconfigure(0, weight=1)

        top = tk.Frame(outer, bg=theme.COLOR_PANEL, bd=1, relief="solid")
        top.grid(row=0, column=0, sticky="ew", pady=(0, theme.SPACE_LG))
        tk.Label(top, textvariable=self.status_var, bg=theme.COLOR_PANEL, fg=theme.COLOR_TEXT, font=theme.FONT_TITLE).pack(
            anchor="w", padx=theme.SPACE_LG, pady=(theme.SPACE_MD, theme.SPACE_SM)
        )
        clock_row = tk.Frame(top, bg=theme.COLOR_PANEL)
        clock_row.pack(anchor="w", padx=theme.SPACE_LG, pady=(0, theme.SPACE_SM))
        tk.Label(clock_row, text="White:", bg=theme.COLOR_PANEL, font=theme.FONT_SUBTITLE).pack(side="left")
        tk.Label(clock_row, textvariable=self.white_clock_var, bg=theme.COLOR_PANEL, font=theme.FONT_MONO).pack(side="left", padx=(theme.SPACE_SM, theme.SPACE_LG))
        tk.Label(clock_row, text="Black:", bg=theme.COLOR_PANEL, font=theme.FONT_SUBTITLE).pack(side="left")
        tk.Label(clock_row, textvariable=self.black_clock_var, bg=theme.COLOR_PANEL, font=theme.FONT_MONO).pack(side="left", padx=(theme.SPACE_SM, 0))
        tk.Label(top, textvariable=self.meta_var, bg=theme.COLOR_PANEL, fg=theme.COLOR_MUTED, font=theme.FONT_SMALL).pack(
            anchor="w", padx=theme.SPACE_LG, pady=(0, theme.SPACE_MD)
        )

        center = tk.Frame(outer, bg=theme.COLOR_BG)
        center.grid(row=1, column=0, sticky="nsew")
        center.columnconfigure(0, weight=1)
        center.columnconfigure(1, weight=0)

        board_wrap = tk.Frame(center, bg=theme.COLOR_BG)
        board_wrap.grid(row=0, column=0, sticky="nsew")
        self.board_widget = BoardWidget(board_wrap, piece_images=self.app.piece_images, click_callback=self._on_square_click)
        self.board_widget.pack(anchor="center", pady=theme.SPACE_MD)

        moves_panel = tk.Frame(center, bg=theme.COLOR_PANEL, bd=1, relief="solid", width=260)
        moves_panel.grid(row=0, column=1, sticky="ns", padx=(theme.SPACE_LG, 0))
        moves_panel.pack_propagate(False)
        tk.Label(moves_panel, text="Moves", bg=theme.COLOR_PANEL, fg=theme.COLOR_TEXT, font=theme.FONT_SUBTITLE).pack(
            anchor="w", padx=theme.SPACE_MD, pady=(theme.SPACE_MD, theme.SPACE_SM)
        )
        self.move_listbox = tk.Listbox(moves_panel, width=24, height=24, font=theme.FONT_MONO)
        self.move_listbox.pack(fill="both", expand=True, padx=theme.SPACE_MD, pady=(0, theme.SPACE_MD))

        bottom = tk.Frame(outer, bg=theme.COLOR_PANEL, bd=1, relief="solid")
        bottom.grid(row=2, column=0, sticky="ew", pady=(theme.SPACE_LG, 0))
        tk.Button(bottom, text="History", command=self.app.open_history).pack(side="left", padx=theme.SPACE_MD, pady=theme.SPACE_MD)
        tk.Button(bottom, text="Back to Menu", command=self.app.show_menu).pack(side="right", padx=(theme.SPACE_SM, theme.SPACE_MD), pady=theme.SPACE_MD)
        tk.Button(bottom, text="Quit", command=self.app.quit_app).pack(side="right", padx=(theme.SPACE_MD, 0), pady=theme.SPACE_MD)

    def _on_square_click(self, row, col):
        if self.game.result is not None:
            return

        if self.selected == (row, col):
            self.selected = None
            self.highlighted_moves = set()
            self._refresh_board()
            return

        if (row, col) in self.highlighted_moves:
            start = self.selected
            success = self.game.make_move(start, (row, col))
            if not success:
                messagebox.showinfo("Invalid move", "That move is not valid.", parent=self)
            elif self.game.board.pending_promotion is not None:
                promotion_choice = PromotionDialog(
                    self,
                    piece_images=self.app.piece_images,
                    color=self.game.board.pending_promotion[2],
                ).show()
                self.game.complete_promotion(promotion_choice)
            self.last_move = {start, (row, col)}
            self.selected = None
            self.highlighted_moves = set()
            self._reload_moves()
            self._refresh()
            return

        piece, moves = self.game.click_board(row, col)
        if piece is not None and piece.color == self.game.turn:
            self.selected = (row, col)
            self.highlighted_moves = set(moves)
        else:
            self.selected = None
            self.highlighted_moves = set()
        self._refresh_board()

    def _reload_moves(self):
        if self.game.game_id is None:
            return
        self.move_records = self.app.service.get_moves(self.game.game_id)

    def _schedule_tick(self):
        self.poll_id = self.after(self.POLL_MS, self._tick)

    def _tick(self):
        self.game.handle_clock_tick()
        self._refresh()
        if self.winfo_exists() and self.poll_id is not None:
            self._schedule_tick()

    def _refresh(self):
        self._refresh_board()
        self._refresh_labels()
        self._refresh_moves()

    def _refresh_board(self):
        self.board_widget.render(
            self.game.board,
            selected=self.selected,
            highlighted_moves=self.highlighted_moves,
            highlighted_squares=self.last_move,
        )

    def _refresh_labels(self):
        self.status_var.set(self._status_text())
        clock_display = self.game.get_clock_display()
        if clock_display is None:
            self.white_clock_var.set("--:--")
            self.black_clock_var.set("--:--")
        else:
            self.white_clock_var.set(format_clock_ms(clock_display["w"]))
            self.black_clock_var.set(format_clock_ms(clock_display["b"]))
        self.meta_var.set(
            f"Game #{self.game.game_id} | Moves: {len(self.move_records)} | Clock: {format_time_control(self.game.clock_enabled, self.game.initial_seconds, self.game.increment_seconds)}"
        )

    def _refresh_moves(self):
        rows = build_move_rows(self.move_records)
        self.move_listbox.delete(0, tk.END)
        for row in rows:
            self.move_listbox.insert(tk.END, row)
        if rows:
            self.move_listbox.see(tk.END)

    def _status_text(self):
        if self.game.result is not None:
            return result_text(self.game.result)
        turn = "White" if self.game.turn == "w" else "Black"
        if self.game.is_current_turn_in_check():
            return f"{turn} to move, in check"
        return f"{turn} to move"

    def on_show(self):
        """Resume periodic updates when the view becomes visible."""
        self.game.resume_clock()
        if self.poll_id is None:
            self._schedule_tick()
        self._reload_moves()
        self._refresh()

    def on_hide(self):
        """Stop periodic updates and pause the active clock."""
        if self.poll_id is not None:
            self.after_cancel(self.poll_id)
            self.poll_id = None
        self.game.pause_clock()
