from logic.fen import board_to_fen, board_from_fen
from logic.piece import Pawn, Knight, Bishop, Rook, Queen, King

BOARD_ROWS = 8
BOARD_COLS = 8

class Board:
    """Representation of an 8x8 chess board.

    The board stores pieces in a rows, colums 2D list where [0][0] corresponds
    to a8 in algebraic notation. Public methods of this class provide the
    operations needed by the game logic.

    Attributes:
        grid (list[list[Piece | None]]): Squares indexed by ``[row][col]``.
        en_passant_target (tuple[int, int] | None): Current en passant target square.
        pending_promotion (tuple[int, int, str] | None): Promotion square and color.
        position_counts (dict[str, int]): Repetition counter keyed by reduced FEN.
    """

    def __init__(self):
        """Create an empty board.

        The board is initialised empty; call set_starting_position to place
        pieces for a new game.
        """
        self.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]  # [0][0] = a8
        self.en_passant_target = None
        self.pending_promotion = None
        self.position_counts = {}

    def get_piece(self, row, col):
        """Return the piece at ``(row, col)``, or ``None`` if empty."""
        return self.grid[row][col]

    def set_piece(self, row, col, piece):
        """Place ``piece`` at ``(row, col)``."""
        self.grid[row][col] = piece

    def to_fen(self, side_to_move, halfmove_clock=0, fullmove_number=1):
        """Serialize the board state to Forsyth-Edwards Notation."""
        return board_to_fen(
            board=self,
            side_to_move=side_to_move,
            halfmove_clock=halfmove_clock,
            fullmove_number=fullmove_number,
        )

### AI code starting
    def repetition_key(self, side_to_move):
        """Return the normalized key used for threefold repetition tracking."""
        fen = self.to_fen(side_to_move, 0, 1)
        placement, active_color, castling_rights, en_passant_square, _, _ = fen.split()

        if en_passant_square != "-" and not self.has_en_passant_capture(side_to_move):
            en_passant_square = "-"

        return f"{placement} {active_color} {castling_rights} {en_passant_square}"

    def has_en_passant_capture(self, side_to_move):
        """Return whether ``side_to_move`` can currently capture en passant."""
        target = self.en_passant_target
        if target is None:
            return False

        row, col = target
        capturing_pawn_row = row + 1 if side_to_move == "w" else row - 1

        if not 0 <= capturing_pawn_row < 8:
            return False

        captured_pawn = self.get_piece(capturing_pawn_row, col)
        if not isinstance(captured_pawn, Pawn) or captured_pawn.color == side_to_move:
            return False

        for pawn_col in (col - 1, col + 1):
            if not 0 <= pawn_col < 8:
                continue

            piece = self.get_piece(capturing_pawn_row, pawn_col)
            if isinstance(piece, Pawn) and piece.color == side_to_move:
                return True

        return False
### AI code ending

    @staticmethod
    def from_fen(fen):
        """Create a board from a FEN string."""
        return board_from_fen(
            fen=fen,
            board_cls=Board,
            board_rows=BOARD_ROWS,
        )

    def clone(self):
        """Create a copy of the board for move simulation.

        The returned Board contains new piece instances with the same type and
        color. Mutable piece attributes used by rules. The copy is used in the
        simulation of moves when checking the legal moves.

        Returns:
            Board: A new Board instance representing the same state.
        """
        board_copy = Board()
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.grid[row][col]
                if piece is None:
                    continue

                piece_copy = type(piece)(piece.color)
                if hasattr(piece, "has_moved"):
                    piece_copy.has_moved = getattr(piece, "has_moved")
                board_copy.grid[row][col] = piece_copy

        board_copy.en_passant_target = (
            None
            if self.en_passant_target is None
            else (self.en_passant_target[0], self.en_passant_target[1])
        )
        board_copy.pending_promotion = (
            None
            if self.pending_promotion is None
            else (
                self.pending_promotion[0],
                self.pending_promotion[1],
                self.pending_promotion[2],
            )
        )
        board_copy.position_counts = dict(self.position_counts)
        return board_copy

    def move_piece(self, start, end):
        """Move a piece and update board-side rule state.

        This handles en passant captures, castling rook movement, en passant
        targets and pending promotions.
        """
        piece = self.get_piece(start[0], start[1])
        if piece is None:
            raise TypeError("Can't move a non-existent piece")

        if end == self.en_passant_target and isinstance(piece, Pawn):
            self.set_piece(start[0], end[1], None)

        self.set_piece(start[0], start[1], None)
        self.set_piece(end[0], end[1], piece)

        if hasattr(piece, "has_moved"):
            piece.has_moved = True

        if isinstance(piece, King) and abs(start[1] - end[1]) == 2:
            self._handle_castling(end)

        self.en_passant_target = None
        if isinstance(piece, Pawn) and abs(start[0] - end[0]) == 2:
            if end[0] == 3:
                self.en_passant_target = (2, end[1])
            else:
                self.en_passant_target = (5, end[1])

        if isinstance(piece, Pawn) and (end[0] == 0 or end[0] == 7):
            self._handle_promotion(end[0], end[1], piece)

    def _handle_promotion(self, row, col, piece):
        self.pending_promotion = (row, col, piece.color)

    def promote(self, piece_type):
        """Complete a pending pawn promotion.

        Args:
            piece_type (str): One-letter promotion code, such as ``Q`` or ``N``.

        Returns:
            bool: ``True`` if the promotion succeeded, otherwise ``False``.
        """
        if self.pending_promotion is None:
            return False

        promotion_map = {
            "Q": Queen,
            "R": Rook,
            "B": Bishop,
            "N": Knight,
        }

        piece_class = promotion_map.get(piece_type.upper())
        if piece_class is None:
            return False

        row = self.pending_promotion[0]
        col = self.pending_promotion[1]
        color = self.pending_promotion[2]
        self.grid[row][col] = piece_class(color)
        self.pending_promotion = None
        return True

    def _handle_castling(self, end):
        row = end[0]
        if end[1] == 6:
            rook = self.get_piece(row, 7)
            self.set_piece(row, 7, None)
            self.set_piece(row, 5, rook)
            if rook is not None and hasattr(rook, "has_moved"):
                rook.has_moved = True
        elif end[1] == 2:
            rook = self.get_piece(row, 0)
            self.set_piece(row, 0, None)
            self.set_piece(row, 3, rook)
            if rook is not None and hasattr(rook, "has_moved"):
                rook.has_moved = True

    def set_starting_position(self):
        """Place pieces for the standard starting chess position.

        This mutates the board in-place and is typically called once when a
        new game is created.
        """
        for col in range(8):
            self.grid[1][col] = Pawn("b")
            self.grid[6][col] = Pawn("w")

        self.grid[0][1] = Knight("b")
        self.grid[0][6] = Knight("b")
        self.grid[7][1] = Knight("w")
        self.grid[7][6] = Knight("w")

        self.grid[0][2] = Bishop("b")
        self.grid[0][5] = Bishop("b")
        self.grid[7][2] = Bishop("w")
        self.grid[7][5] = Bishop("w")

        self.grid[0][0] = Rook("b")
        self.grid[0][7] = Rook("b")
        self.grid[7][0] = Rook("w")
        self.grid[7][7] = Rook("w")

        self.grid[0][3] = Queen("b")
        self.grid[7][3] = Queen("w")

        self.grid[0][4] = King("b")
        self.grid[7][4] = King("w")


    def _find_king(self, color):
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.grid[row][col]
                if isinstance(piece, King) and piece.color == color:
                    return (row, col)
        return None

    def is_king_in_check(self, color):
        """Return True if the king of the given color is in check.

        Args:
            color (str): 'w' or 'b' representing the king to check.

        Returns:
            bool: True if the king is attacked by any opposing piece.

        Raises:
            ValueError: If the king cannot be found on the board.
        """
        king_pos = self._find_king(color)
        if king_pos is None:
            raise ValueError(f"King not found for color {color}")

        opponent_color = "b" if color == "w" else "w"
        return self.is_square_attacked(king_pos[0], king_pos[1], opponent_color)

    def is_square_attacked(self, row, col, by_color):
        """Return True if (row, col) is attacked by (by_color)."""
        return (
            self._pawn_attacks(row, col, by_color)
            or self._knight_attacks(row, col, by_color)
            or self._king_attacks(row, col, by_color)
            or self._sliding_attacks(
                row,
                col,
                by_color,
                directions=[(0, 1), (1, 0), (0, -1), (-1, 0)],
                piece_types=(Rook, Queen),
            )
            or self._sliding_attacks(
                row,
                col,
                by_color,
                directions=[(1, 1), (-1, 1), (-1, -1), (1, -1)],
                piece_types=(Bishop, Queen),
            )
        )


    def _pawn_attacks(self, row, col, by_color):
        grid = self.grid
        direction = -1 if by_color == "w" else 1
        pawn_row = row - direction

        if not 0 <= pawn_row < 8:
            return False

        for dc in (-1, 1):
            pawn_col = col + dc
            if 0 <= pawn_col < 8:
                piece = grid[pawn_row][pawn_col]
                if isinstance(piece, Pawn) and piece.color == by_color:
                    return True
        return False


    def _knight_attacks(self, row, col, by_color):
        grid = self.grid
        offsets = [(1, 2), (1, -2), (-1, 2), (-1, -2),
                (2, 1), (2, -1), (-2, 1), (-2, -1)]

        for dr, dc in offsets:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                piece = grid[r][c]
                if isinstance(piece, Knight) and piece.color == by_color:
                    return True
        return False


    def _king_attacks(self, row, col, by_color):
        grid = self.grid

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue

                r, c = row + dr, col + dc
                if not (0 <= r < 8 and 0 <= c < 8):
                    continue

                piece = grid[r][c]
                if isinstance(piece, King) and piece.color == by_color:
                    return True
        return False


    def _sliding_attacks(
        self,
        row,
        col,
        by_color,
        *,
        directions,
        piece_types,
    ):
        grid = self.grid

        for dr, dc in directions:
            r, c = row + dr, col + dc

            while 0 <= r < 8 and 0 <= c < 8:
                piece = grid[r][c]

                if piece is None:
                    r += dr
                    c += dc
                    continue

                if piece.color == by_color and isinstance(piece, piece_types):
                    return True
                break

        return False
