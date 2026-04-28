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

        grid = board.grid
        en_passant_target = getattr(board, "en_passant_target", None)

        direction = -1 if self.color == "w" else 1
        start_row = 6 if self.color == "w" else 1

        new_row = row + direction
        if 0 <= new_row < 8 and grid[new_row][col] is None:
            moves.append((new_row, col))
            new_row2 = row + 2 * direction
            if row == start_row and 0 <= new_row2 < 8 and grid[new_row2][col] is None:
                moves.append((new_row2, col))

        for diag in [-1, 1]:
            new_col = col + diag
            if 0 <= new_col < 8 and 0 <= new_row < 8:
                target = grid[new_row][new_col]
                if target is not None and target.color != self.color:
                    moves.append((new_row, new_col))
                if en_passant_target is not None and (new_row, new_col) == en_passant_target:
                    moves.append((new_row, new_col))

        return moves



class Knight(Piece):
    symbol = "N"
    def get_moves(self, pos, board):
        moves = []
        row, col = pos

        grid = board.grid

        directions = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
        for d in directions:
            new_row = row + d[0]
            new_col = col + d[1]
            if 0 <= new_col < 8 and 0 <= new_row < 8:
                target = grid[new_row][new_col]
                if target is None or (target and target.color != self.color):
                    moves.append((new_row, new_col))

        return moves

class Bishop(Piece):
    symbol = "B"
    def get_moves(self, pos, board):
        moves = []
        row, col = pos

        grid = board.grid

        directions = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
        for d in directions:
            new_row = row + d[0]
            new_col = col + d[1]
            while 0 <= new_row < 8 and 0 <= new_col < 8:
                target = grid[new_row][new_col]
                if target is None:
                    moves.append((new_row, new_col))
                    new_row += d[0]
                    new_col += d[1]
                    continue
                if target.color != self.color:
                    moves.append((new_row, new_col))
                    break

                break

        return moves

class Rook(Piece):
    symbol = "R"
    has_moved = False

    def get_moves(self, pos, board):
        moves = []
        row, col = pos

        grid = board.grid

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for d in directions:
            new_row = row + d[0]
            new_col = col + d[1]
            while 0 <= new_row < 8 and 0 <= new_col < 8:
                target = grid[new_row][new_col]
                if target is None:
                    moves.append((new_row, new_col))
                    new_row += d[0]
                    new_col += d[1]
                    continue
                if target.color != self.color:
                    moves.append((new_row, new_col))
                    break

                break

        return moves

class Queen(Piece):
    symbol = "Q"
    def get_moves(self, pos, board):
        moves = []
        row, col = pos

        grid = board.grid

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (-1, -1), (1, -1)]
        for d in directions:
            new_row = row + d[0]
            new_col = col + d[1]
            while 0 <= new_row < 8 and 0 <= new_col < 8:
                target = grid[new_row][new_col]
                if target is None:
                    moves.append((new_row, new_col))
                    new_row += d[0]
                    new_col += d[1]
                    continue
                if target.color != self.color:
                    moves.append((new_row, new_col))
                    break

                break

        return moves

class King(Piece):
    symbol = "K"
    has_moved = False
    def get_moves(self, pos, board):
        moves = []
        row, col = pos

        grid = board.grid

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (-1, -1), (1, -1)]
        for d in directions:
            new_row = row + d[0]
            new_col = col + d[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = grid[new_row][new_col]
                if target is None or target.color != self.color:
                    moves.append((new_row, new_col))

        if not self.has_moved:
            rook = grid[row][7]
            if (rook is not None and rook.color == self.color and isinstance(rook, Rook)
                    and not getattr(rook, "has_moved")):
                if grid[row][5] is None and grid[row][6] is None:
                    moves.append((row, 6))

            rook_q = grid[row][0]
            if (rook_q is not None and rook_q.color == self.color and isinstance(rook_q, Rook)
                    and not getattr(rook_q, "has_moved")):
                if grid[row][1] is None and grid[row][2] is None and grid[row][3] is None:
                    moves.append((row, 2))

        return moves
