from piece import Pawn, Knight, Bishop, Rook, Queen, King

BOARD_ROWS = 8
BOARD_COLS = 8

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)] # [0][0] = a8
        self.en_passant_target = None
        self.pending_promotion = None

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
        self.pending_promotion = (row, col, piece.color)

    def promote(self, piece_type):
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

    def is_square_attacked(self, row, col, by_color):
        grid = self.grid

        pawn_row = row + 1 if by_color == "w" else row - 1
        if 0 <= pawn_row < 8:
            for dc in (-1, 1):
                pawn_col = col + dc
                if 0 <= pawn_col < 8:
                    piece = grid[pawn_row][pawn_col]
                    if isinstance(piece, Pawn) and piece.color == by_color:
                        return True

        knight_offsets = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
        for dr, dc in knight_offsets:
            knight_row = row + dr
            knight_col = col + dc
            if 0 <= knight_row < 8 and 0 <= knight_col < 8:
                piece = grid[knight_row][knight_col]
                if isinstance(piece, Knight) and piece.color == by_color:
                    return True

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                king_row = row + dr
                king_col = col + dc
                if 0 <= king_row < 8 and 0 <= king_col < 8:
                    piece = grid[king_row][king_col]
                    if isinstance(piece, King) and piece.color == by_color:
                        return True

        orthogonal = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for dr, dc in orthogonal:
            r = row + dr
            c = col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                piece = grid[r][c]
                if piece is None:
                    r += dr
                    c += dc
                    continue
                if piece.color == by_color and isinstance(piece, (Rook, Queen)):
                    return True
                break

        diagonal = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
        for dr, dc in diagonal:
            r = row + dr
            c = col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                piece = grid[r][c]
                if piece is None:
                    r += dr
                    c += dc
                    continue
                if piece.color == by_color and isinstance(piece, (Bishop, Queen)):
                    return True
                break
        return False
