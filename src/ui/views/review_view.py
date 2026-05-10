import tkinter as tk

from chess.board import Board
from chess.fen import parse_fen
from ui import theme
from ui.helpers import build_move_rows, game_row_result_text
from ui.widgets.board_widget import BoardWidget


class ReviewView(tk.Frame):
    """Read-only review view for stepping through a saved game.

    Attributes:
        app: Application controller used for navigation and storage access.
        game_id (int): Identifier of the reviewed game.
        game_row (dict): Persisted metadata for the game.
        moves (list[dict]): Persisted move rows for the game.
        snapshots (list[str]): FEN snapshots for each reviewable position.
        current_index (int): Index of the currently displayed snapshot.
    """

    def __init__(self, master, *, app, game_id):
        """Build the review view for ``game_id``."""
        super().__init__(master, bg=theme.COLOR_BG, padx=theme.SPACE_XL, pady=theme.SPACE_XL)
        self.app = app
        self.game_id = game_id
        self.game_row = self.app.service.get_game(game_id)
        self.moves = self.app.service.get_moves(game_id)
        self.snapshots = [self.game_row["initial_fen"]]
        self.snapshots.extend(move["fen_after"] for move in self.moves)
        self.current_index = len(self.snapshots) - 1

        self.status_var = tk.StringVar()
        self.position_var = tk.StringVar()
        self.board = None
        self.turn = "w"

        self._build_layout()
        self._load_snapshot(self.current_index)
        self._refresh()

    def _build_layout(self):
        outer = tk.Frame(self, bg=theme.COLOR_BG)
        outer.pack(fill="both", expand=True)
        outer.rowconfigure(1, weight=1)
        outer.columnconfigure(0, weight=1)

        top = tk.Frame(outer, bg=theme.COLOR_PANEL, bd=1, relief="solid")
        top.grid(row=0, column=0, sticky="ew", pady=(0, theme.SPACE_LG))
        tk.Label(top, textvariable=self.status_var, bg=theme.COLOR_PANEL, font=theme.FONT_TITLE).pack(
            anchor="w", padx=theme.SPACE_LG, pady=(theme.SPACE_MD, theme.SPACE_SM)
        )
        tk.Label(top, textvariable=self.position_var, bg=theme.COLOR_PANEL, fg=theme.COLOR_MUTED, font=theme.FONT_SMALL).pack(
            anchor="w", padx=theme.SPACE_LG, pady=(0, theme.SPACE_MD)
        )

        center = tk.Frame(outer, bg=theme.COLOR_BG)
        center.grid(row=1, column=0, sticky="nsew")
        center.columnconfigure(0, weight=1)

        board_wrap = tk.Frame(center, bg=theme.COLOR_BG)
        board_wrap.grid(row=0, column=0, sticky="nsew")
        self.board_widget = BoardWidget(board_wrap, piece_images=self.app.piece_images)
        self.board_widget.pack(anchor="center", pady=theme.SPACE_MD)

        side = tk.Frame(center, bg=theme.COLOR_PANEL, bd=1, relief="solid", width=260)
        side.grid(row=0, column=1, sticky="ns", padx=(theme.SPACE_LG, 0))
        side.pack_propagate(False)
        tk.Label(side, text="Moves", bg=theme.COLOR_PANEL, font=theme.FONT_SUBTITLE).pack(
            anchor="w", padx=theme.SPACE_MD, pady=(theme.SPACE_MD, theme.SPACE_SM)
        )
        self.move_listbox = tk.Listbox(side, width=24, height=24, font=theme.FONT_MONO)
        self.move_listbox.pack(fill="both", expand=True, padx=theme.SPACE_MD, pady=(0, theme.SPACE_MD))

        controls = tk.Frame(outer, bg=theme.COLOR_PANEL, bd=1, relief="solid")
        controls.grid(row=2, column=0, sticky="ew", pady=(theme.SPACE_LG, 0))
        tk.Button(controls, text="|<", command=self.go_to_start).pack(side="left", padx=(theme.SPACE_MD, theme.SPACE_SM), pady=theme.SPACE_MD)
        tk.Button(controls, text="<", command=self.previous_position).pack(side="left", padx=(0, theme.SPACE_SM), pady=theme.SPACE_MD)
        tk.Button(controls, text=">", command=self.next_position).pack(side="left", padx=(0, theme.SPACE_SM), pady=theme.SPACE_MD)
        tk.Button(controls, text=">|", command=self.go_to_end).pack(side="left", padx=(0, theme.SPACE_MD), pady=theme.SPACE_MD)
        tk.Button(controls, text="Back", command=self.app.go_back).pack(side="right", padx=theme.SPACE_MD, pady=theme.SPACE_MD)
        tk.Button(controls, text="Quit", command=self.app.quit_app).pack(side="right", pady=theme.SPACE_MD)

        for row in build_move_rows(self.moves):
            self.move_listbox.insert(tk.END, row)

    def _load_snapshot(self, index):
        fen_state = parse_fen(self.snapshots[index], Board)
        self.board = fen_state["board"]
        self.turn = fen_state["side_to_move"]

    def _refresh(self):
        self.board_widget.render(self.board)
        self.status_var.set(f"Game #{self.game_id} | {game_row_result_text(self.game_row)}")
        self.position_var.set(f"Position {self.current_index} / {len(self.snapshots) - 1}")
        selection_index = self.current_index - 1
        self.move_listbox.selection_clear(0, tk.END)
        if selection_index >= 0:
            row_index = selection_index // 2
            self.move_listbox.selection_set(row_index)
            self.move_listbox.see(row_index)

    def go_to_start(self):
        """Jump to the starting position."""
        self.current_index = 0
        self._load_snapshot(self.current_index)
        self._refresh()

    def go_to_end(self):
        """Jump to the final recorded position."""
        self.current_index = len(self.snapshots) - 1
        self._load_snapshot(self.current_index)
        self._refresh()

    def previous_position(self):
        """Move one snapshot backward if possible."""
        if self.current_index == 0:
            return
        self.current_index -= 1
        self._load_snapshot(self.current_index)
        self._refresh()

    def next_position(self):
        """Move one snapshot forward if possible."""
        if self.current_index >= len(self.snapshots) - 1:
            return
        self.current_index += 1
        self._load_snapshot(self.current_index)
        self._refresh()

    def on_show(self):
        """Refresh the displayed snapshot when the view becomes visible."""
        self._refresh()

    def on_hide(self):
        return
