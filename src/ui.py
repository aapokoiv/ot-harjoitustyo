import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from game import Game


class ChessUI:
    LIGHT_COLOR = "#EEEED2"
    DARK_COLOR = "#769656"
    SELECT_COLOR = "#f7ec8e"
    MOVE_COLOR = "#a9d18e"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chess")

        self.game = Game()

        self.selected = None
        self.highlighted_moves = set()
        self.piece_images = self._load_piece_images()
        self.empty_square_image = tk.PhotoImage(width=60, height=60)

        self.status_var = tk.StringVar()
        self.status_var.set(f"Turn: {self.game.turn}")
        status = tk.Label(self.root, textvariable=self.status_var)
        status.grid(row=0, column=0, columnspan=8, sticky="we")

        board_frame = tk.Frame(self.root)
        board_frame.grid(row=1, column=0, columnspan=8)

        self.buttons = [[None for _ in range(8)] for _ in range(8)]
        for r in range(8):
            for c in range(8):
                b = tk.Button(board_frame, command=lambda row=r, col=c: self._on_square_click(row, col))
                b.grid(row=r, column=c)
                self.buttons[r][c] = b

        restart_btn = tk.Button(self.root, text="Restart", command=self._restart)
        restart_btn.grid(row=2, column=0, columnspan=4, sticky="we")

        quit_btn = tk.Button(self.root, text="Quit", command=self._quit_game)
        quit_btn.grid(row=2, column=4, columnspan=4, sticky="we")
        self.root.protocol("WM_DELETE_WINDOW", self._quit_game)

        self._refresh_board()

    def _on_square_click(self, row, col):
        if self.selected == (row, col):
            self.selected = None
            self.highlighted_moves = set()
            self._refresh_board()
            return

        if (row, col) in self.highlighted_moves:
            start = self.selected
            success = self.game.make_move(start, (row, col))
            if not success:
                messagebox.showinfo("Invalid move", "That move is not valid")
            elif self.game.board.pending_promotion is not None:
                choice = self._show_promotion_dialog()
                self.game.complete_promotion(choice)
            self.selected = None
            self.highlighted_moves = set()
            self._refresh_board()
            return

        piece, moves = self.game.click_board(row, col)
        if piece is not None and piece.color == self.game.turn:
            self.selected = (row, col)
            self.highlighted_moves = set(moves)
            self._refresh_board()
            return

        self.selected = None
        self.highlighted_moves = set()
        self._refresh_board()

    def _show_promotion_dialog(self):
        """Show adialog asking user which piece to promote to.

        Returns:
            str: One-letter promotion code, one of 'Q', 'R', 'B', 'N'.
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose Promotion")
        dialog.transient(self.root)
        dialog.grab_set()

        result = tk.StringVar(value="Q")

        label = tk.Label(dialog, text="Promote pawn to:")
        label.pack(padx=16, pady=(12, 8))

        button_frame = tk.Frame(dialog)
        button_frame.pack(padx=16, pady=(0, 12))

        options = [
            ("Queen (Q)", "Q"),
            ("Rook (R)", "R"),
            ("Bishop (B)", "B"),
            ("Knight (N)", "N"),
        ]

        def choose(piece_type):
            result.set(piece_type)
            dialog.destroy()

        for text, piece_type in options:
            button = tk.Button(button_frame, text=text, width=12, command=lambda pt=piece_type: choose(pt))
            button.pack(fill="x", pady=2)

        dialog.protocol("WM_DELETE_WINDOW", lambda: choose("Q"))
        self.root.wait_window(dialog)
        return result.get()

    def _refresh_board(self):
        for r in range(8):
            for c in range(8):
                btn = self.buttons[r][c]
                piece = self.game.board.get_piece(r, c)
                piece_key = str(piece) if piece else ""
                image = self.piece_images.get(piece_key)
                if piece is None:
                    btn.config(image=self.empty_square_image, text="")
                elif image is not None:
                    btn.config(image=image, text="")
                else:
                    btn.config(image=self.empty_square_image, text=piece_key, compound="center")

                base = self.LIGHT_COLOR if (r + c) % 2 == 0 else self.DARK_COLOR
                color = base

                if self.selected == (r, c):
                    color = self.SELECT_COLOR
                elif (r, c) in self.highlighted_moves:
                    color = self.MOVE_COLOR

                btn.config(bg=color, activebackground=color)

        self.status_var.set(self._status_text())

    def _status_text(self):
        result = self.game.result
        if result is not None:
            if result["type"] == "checkmate":
                winner = "White" if result.get("winner") == "w" else "Black"
                return f"Checkmate! {winner} wins"

            draw_messages = {
                "stalemate": "Stalemate! Draw",
                "threefold_repetition": "Draw by repetition",
                "fifty_move_rule": "Draw by 50-move rule",
                "insufficient_material": "Draw by insufficient material",
            }
            return draw_messages.get(result["type"], "Draw")

        turn = "White" if self.game.turn == "w" else "Black"
        if self.game.is_current_turn_in_check():
            return f"Turn: {turn} (Check)"
        return f"Turn: {turn}"

### AI generated code starting
    def _load_piece_images(self):
        asset_dir = Path(__file__).resolve().parent.parent / "assets"
        file_map = {
            "wK": "Chess_klt60.png",
            "bK": "Chess_kdt60.png",
            "wQ": "Chess_qlt60.png",
            "bQ": "Chess_qdt60.png",
            "wR": "Chess_rlt60.png",
            "bR": "Chess_rdt60.png",
            "wB": "Chess_blt60.png",
            "bB": "Chess_bdt60.png",
            "wN": "Chess_nlt60.png",
            "bN": "Chess_ndt60.png",
            "wP": "Chess_plt60.png",
            "bP": "Chess_pdt60.png",
        }

        images = {}
        for piece_key, filename in file_map.items():
            file_path = asset_dir / filename
            if file_path.exists():
                images[piece_key] = tk.PhotoImage(file=str(file_path))

        return images
### AI generated code ending

    def _restart(self):
        self.game.pause_clock()
        self.game = Game()
        self.selected = None
        self.highlighted_moves = set()
        self._refresh_board()

    def _quit_game(self):
        self.game.pause_clock()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ui = ChessUI()
    ui.run()
