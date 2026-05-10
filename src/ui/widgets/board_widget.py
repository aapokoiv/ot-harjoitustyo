import tkinter as tk

from ui import theme


class BoardWidget(tk.Frame):
    """Tk widget that renders a chess board and optional highlights.

    Attributes:
        piece_images (dict[str, tk.PhotoImage]): Images keyed by piece string.
        click_callback (Callable | None): Handler called with clicked coordinates.
        empty_square_image (tk.PhotoImage): Transparent placeholder image.
        buttons (list[list[tk.Button]]): Button grid representing board squares.
    """

    def __init__(self, master, *, piece_images, click_callback=None):
        """Create the board widget."""
        super().__init__(master, bg=theme.COLOR_BORDER, bd=theme.BOARD_BORDER)
        self.piece_images = piece_images
        self.click_callback = click_callback
        self.empty_square_image = tk.PhotoImage(width=theme.BOARD_SQUARE_SIZE, height=theme.BOARD_SQUARE_SIZE)
        self.buttons = []

        board_frame = tk.Frame(self, bg=theme.COLOR_BORDER)
        board_frame.pack()
        for row in range(8):
            button_row = []
            for col in range(8):
                button = tk.Button(
                    board_frame,
                    font=theme.BOARD_FONT,
                    borderwidth=0,
                    highlightthickness=0,
                    compound="center",
                    command=lambda current_row=row, current_col=col: self._handle_click(current_row, current_col),
                )
                button.grid(row=row, column=col, padx=0, pady=0, ipadx=0, ipady=0)
                button_row.append(button)
            self.buttons.append(button_row)

    def _handle_click(self, row, col):
        if self.click_callback is not None:
            self.click_callback(row, col)

    def render(
        self,
        board,
        *,
        selected=None,
        highlighted_moves=None,
        highlighted_squares=None,
    ):
        """Render a board position and highlight state into the button grid."""
        highlighted_moves = highlighted_moves or set()
        highlighted_squares = highlighted_squares or set()
        for row in range(8):
            for col in range(8):
                button = self.buttons[row][col]
                piece = board.get_piece(row, col)
                piece_key = str(piece) if piece else ""
                image = self.piece_images.get(piece_key)

                if piece is None:
                    button.config(image=self.empty_square_image, text="")
                elif image is not None:
                    button.config(image=image, text="")
                else:
                    button.config(image=self.empty_square_image, text=piece_key)

                color = theme.COLOR_LIGHT if (row + col) % 2 == 0 else theme.COLOR_DARK
                if (row, col) in highlighted_squares:
                    color = theme.COLOR_LAST_MOVE
                if (row, col) in highlighted_moves:
                    color = theme.COLOR_MOVE
                if selected == (row, col):
                    color = theme.COLOR_SELECTED
                button.config(bg=color, activebackground=color)
