from Piece import Pawn, Knight, Bishop, Rook, Queen, King

board_rows = 8
board_cols = 8

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(board_cols)] for _ in range(board_rows)] # [0][0] = a8

    def get_piece(self, row, col):
        return self.grid[row][col]
        
    def set_piece(self, row, col, piece):
        self.grid[row][col] = piece

    def move_piece(self, start, end):
        piece = self.get_piece(start[0], start[1])
        self.set_piece(start[0], start[1], None)
        self.set_piece(end[0], end[1], piece)

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

