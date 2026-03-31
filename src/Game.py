from Board import Board

class Game:
    def __init__(self):
        self.board = Board()
        self.turn = "w"
        self.board.set_starting_position()

    def make_move(self, start, end):
        piece = self.board.get_piece(start[0], start[1])
        if not piece:
            return False
        if piece.color != self.turn:
            return False

        moves = piece.get_moves((start[0], start[1]), self.board.grid)

        if end not in moves:
            return False

        self.board.move_piece(start, end)

        self.switch_turn()
        return True

    def click_board(self, row, col):
        piece = self.board.get_piece(row, col)
        moves = []
        if piece:
            moves = piece.get_moves((row, col), self.board.grid)
        return piece, moves

    def switch_turn(self):
        self.turn = "b" if self.turn == "w" else "w"

