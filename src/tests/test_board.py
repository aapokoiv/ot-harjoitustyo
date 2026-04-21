import unittest
from board import Board
from piece import Pawn, Rook

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

    def test_kingside_castling(self):
        self.board.set_piece(7, 5, None)
        self.board.set_piece(7, 6, None)
        self.board.move_piece((7, 4), (7, 6))
        self.assertEqual(str(self.board.get_piece(7, 6)), "wK")
        self.assertEqual(str(self.board.get_piece(7, 5)), "wR")
        self.assertTrue(getattr(self.board.get_piece(7, 6), "has_moved", False))
        self.assertTrue(getattr(self.board.get_piece(7, 5), "has_moved", False))

    def test_queenside_castling(self):
        self.board.set_piece(7, 1, None)
        self.board.set_piece(7, 2, None)
        self.board.set_piece(7, 3, None)
        self.board.move_piece((7, 4), (7, 2))
        self.assertEqual(str(self.board.get_piece(7, 2)), "wK")
        self.assertEqual(str(self.board.get_piece(7, 3)), "wR")
        self.assertTrue(getattr(self.board.get_piece(7, 2), "has_moved", False))
        self.assertTrue(getattr(self.board.get_piece(7, 3), "has_moved", False))

    def test_en_passant_capture(self):
        self.board.set_piece(4, 4, Pawn("b"))
        self.board.move_piece((6, 3), (4, 3))
        self.assertEqual(self.board.en_passant_target, (5, 3))
        self.board.move_piece((4, 4), (5, 3))
        self.assertEqual(str(self.board.get_piece(5, 3)), "bP")
        self.assertIsNone(self.board.get_piece(4, 4))

    def test_pending_promotion_set(self):
        self.board.grid = [[None for _ in range(8)] for _ in range(8)]
        pawn = Pawn("w")
        self.board.set_piece(1, 0, pawn)
        self.board.move_piece((1, 0), (0, 0))

        self.assertIsNotNone(self.board.pending_promotion)
        self.assertEqual(self.board.pending_promotion[0], 0)
        self.assertEqual(self.board.pending_promotion[1], 0)
        self.assertEqual(self.board.pending_promotion[2], "w")
        self.assertEqual(str(self.board.get_piece(0, 0)), "wP")

    def test_promote_method(self):
        self.board.grid = [[None for _ in range(8)] for _ in range(8)]
        self.board.set_piece(1, 0, Pawn("w"))
        self.board.move_piece((1, 0), (0, 0))

        success = self.board.promote("R")

        self.assertTrue(success)
        self.assertIsInstance(self.board.get_piece(0, 0), Rook)
        self.assertEqual(self.board.get_piece(0, 0).color, "w")
        self.assertIsNone(self.board.pending_promotion)
