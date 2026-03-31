class Piece:
    def __init__(self, color):
        self.color = color

    def get_moves(self, pos, board):
        pass

    symbol = "?"
    def __str__(self):
        return f"{self.color}{self.symbol}"


class Pawn(Piece):
    symbol = "P"
    def get_moves(self, pos, board):
        moves = []
        row, col = pos

        direction = -1 if self.color == "w" else 1
        start_row = 6 if self.color == "w" else 1

        if board[row + direction][col] is None:
            moves.append((row + direction, col))
            if row == start_row and board[row + 2 * direction][col] is None:
                moves.append((row + 2 * direction, col))

        for diag in [-1, 1]:
            new_col = col + diag
            if 0 <= new_col < 8:
                target = board[row + direction][new_col]
                if target is not None and target.color != self.color:
                    moves.append((row + direction, new_col))

        # todo: promotion, en passant

        return moves



class Knight(Piece):
    symbol = "N"
    def get_moves(self, pos, board):
        moves = []
        row, col = pos

        directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
        for dir in directions:
            new_row = row + dir[0]
            new_col = col + dir[1]
            if 0 <= new_col < 8 and 0 <= new_row < 8:
                target = board[new_row][new_col]
                if (target and target.color != self.color) or target == None:
                    moves.append((new_row, new_col))

        return moves

class Bishop(Piece):
    symbol = "B"
    def get_moves(self, pos, board):
        return []

class Rook(Piece):
    symbol = "R"
    def get_moves(self, pos, board):
        return []

class Queen(Piece):
    symbol = "Q"
    def get_moves(self, pos, board):
        return []

class King(Piece):
    symbol = "K"
    def get_moves(self, pos, board):
        return []

