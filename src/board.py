from piece import Pawn, Knight, Bishop, Rook, Queen, King

# Use uppercase for module-level constants
BOARD_ROWS = 8
BOARD_COLS = 8

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)] # [0][0] = a8
        self.en_passant_target = None

    def get_piece(self, row, col):
        return self.grid[row][col]

    def set_piece(self, row, col, piece):
        self.grid[row][col] = piece

    def move_piece(self, start, end):
        piece = self.get_piece(start[0], start[1])
        if piece is None:
            raise TypeError("Can't move a non-existent piece")

        if end == self.en_passant_target and isinstance(piece, Pawn):
            self.set_piece(start[0], end[1], None)  # Remove the captured piece separately

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
            self.handle_promotion(end[0], end[1], piece)


    def handle_promotion(self, row, col, piece):
        self.grid[row][col] = Queen(f"{piece.color}")

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
        self.grid = [[None for _ in range(8)] for _ in range(8)]

        ### AI generated code starting
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
        ### AI generated code ending
