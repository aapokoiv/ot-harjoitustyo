import unittest
from Board import Board
from Piece import Pawn

class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board.set_starting_position()

    def test_starting_position_correct(self):
        self.assertEqual(str(self.board.get_piece(1, 1)), "bP")
        self.assertEqual(str(self.board.get_piece(0, 3)), "bQ")
        self.assertEqual(str(self.board.get_piece(7, 1)), "wN")
        self.assertEqual(str(self.board.get_piece(3, 2)), "None")

    def test_set_piece(self):
        pawn = Pawn("w")
        self.board.set_piece(3, 3, pawn)
        self.assertEqual(self.board.get_piece(3, 3), pawn)

    def test_move_piece(self):
        self.board.move_piece((6, 4), (4, 4))
        self.assertEqual(str(self.board.get_piece(4, 4)), "wP")

