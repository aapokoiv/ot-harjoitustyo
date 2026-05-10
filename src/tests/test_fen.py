import unittest

from chess.board import Board
from chess.piece import King, Rook


class TestFen(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board.set_starting_position()

    def test_to_fen_starting_position(self):
        fen = self.board.to_fen("w")
        self.assertEqual(fen, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    def test_from_fen_sets_expected_pieces(self):
        board = Board.from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")

        self.assertEqual(str(board.get_piece(0, 4)), "bK")
        self.assertEqual(str(board.get_piece(7, 4)), "wK")
        self.assertIsNone(board.get_piece(3, 3))

    def test_from_fen_applies_castling_rights_has_moved_flags(self):
        board = Board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w Kq - 0 1")

        self.assertIsInstance(board.get_piece(7, 4), King)
        self.assertFalse(board.get_piece(7, 4).has_moved)
        self.assertIsInstance(board.get_piece(7, 7), Rook)
        self.assertFalse(board.get_piece(7, 7).has_moved)
        self.assertIsInstance(board.get_piece(7, 0), Rook)
        self.assertTrue(board.get_piece(7, 0).has_moved)

        self.assertIsInstance(board.get_piece(0, 4), King)
        self.assertFalse(board.get_piece(0, 4).has_moved)
        self.assertIsInstance(board.get_piece(0, 0), Rook)
        self.assertFalse(board.get_piece(0, 0).has_moved)
        self.assertIsInstance(board.get_piece(0, 7), Rook)
        self.assertTrue(board.get_piece(0, 7).has_moved)

    def test_from_fen_sets_en_passant_target(self):
        board = Board.from_fen("8/8/8/8/8/8/8/8 w - e3 0 1")
        self.assertEqual(board.en_passant_target, (5, 4))

    def test_fen_roundtrip_preserves_state(self):
        original_fen = "r3k2r/ppp2ppp/8/3pP3/8/8/PPP2PPP/R3K2R b KQkq e6 4 10"

        board = Board.from_fen(original_fen)
        generated_fen = board.to_fen("b", halfmove_clock=4, fullmove_number=10)

        self.assertEqual(generated_fen, original_fen)

    def test_from_fen_invalid_field_count_raises(self):
        with self.assertRaises(ValueError):
            Board.from_fen("8/8/8/8/8/8/8/8 w - - 0")

    def test_from_fen_invalid_rank_count_raises(self):
        with self.assertRaises(ValueError):
            Board.from_fen("8/8/8/8/8/8/8 w - - 0 1")

    def test_from_fen_invalid_rank_width_raises(self):
        with self.assertRaises(ValueError):
            Board.from_fen("9/8/8/8/8/8/8/8 w - - 0 1")

    def test_from_fen_invalid_en_passant_target_raises(self):
        with self.assertRaises(ValueError):
            Board.from_fen("8/8/8/8/8/8/8/8 w - z9 0 1")
