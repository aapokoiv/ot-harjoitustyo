import tkinter as tk
from tkinter import messagebox
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

        self.status_var = tk.StringVar()
        self.status_var.set(f"Turn: {self.game.turn}")
        status = tk.Label(self.root, textvariable=self.status_var)
        status.grid(row=0, column=0, columnspan=8, sticky="we")

        board_frame = tk.Frame(self.root)
        board_frame.grid(row=1, column=0, columnspan=8)

        self.buttons = [[None for _ in range(8)] for _ in range(8)]
        for r in range(8):
            for c in range(8):
                b = tk.Button(board_frame, width=6, height=3, command=lambda row=r, col=c: self.on_square_click(row, col))
                b.grid(row=r, column=c)
                self.buttons[r][c] = b

        restart_btn = tk.Button(self.root, text="Restart", command=self.restart)
        restart_btn.grid(row=2, column=0, columnspan=4, sticky="we")

        quit_btn = tk.Button(self.root, text="Quit", command=self.root.quit)
        quit_btn.grid(row=2, column=4, columnspan=4, sticky="we")

        self.refresh_board()

    def on_square_click(self, row, col):
        if self.selected == (row, col):
            self.selected = None
            self.highlighted_moves = set()
            self.refresh_board()
            return

        if (row, col) in self.highlighted_moves:
            start = self.selected
            success = self.game.make_move(start, (row, col))
            if not success:
                messagebox.showinfo("Invalid move", "That move is not valid")
            elif self.game.board.pending_promotion is not None:
                choice = self.show_promotion_dialog()
                self.game.complete_promotion(choice)
            self.selected = None
            self.highlighted_moves = set()
            self.refresh_board()
            return

        piece, moves = self.game.click_board(row, col)
        if piece is not None and piece.color == self.game.turn:
            self.selected = (row, col)
            self.highlighted_moves = set(moves)
            self.refresh_board()
            return

        self.selected = None
        self.highlighted_moves = set()
        self.refresh_board()

    def show_promotion_dialog(self):
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

    def refresh_board(self):
        for r in range(8):
            for c in range(8):
                btn = self.buttons[r][c]
                piece = self.game.board.get_piece(r, c)
                text = str(piece) if piece else ""
                btn.config(text=text)

                base = self.LIGHT_COLOR if (r + c) % 2 == 0 else self.DARK_COLOR
                color = base

                if self.selected == (r, c):
                    color = self.SELECT_COLOR
                elif (r, c) in self.highlighted_moves:
                    color = self.MOVE_COLOR

                btn.config(bg=color, activebackground=color)

        self.status_var.set(f"Turn: {self.game.turn}")

    def restart(self):
        self.game = Game()
        self.selected = None
        self.highlighted_moves = set()
        self.refresh_board()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ui = ChessUI()
    ui.run()
