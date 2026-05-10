import unittest

from logic.game import Game
from logic.piece import Bishop, King, Knight, Pawn, Queen, Rook


class FakeStorageService:
    def __init__(self):
        self.saved_moves = []
        self.finished_games = []

    def start_game(self, _initial_fen):
        return 1

    def save_move(self, *args, **kwargs):
        self.saved_moves.append({"args": args, "kwargs": kwargs})
        return 1

    def finish_game(self, *args, **kwargs):
        self.finished_games.append({"args": args, "kwargs": kwargs})


class TestGame(unittest.TestCase):
    def setUp(self):
        self.storage_service = FakeStorageService()
        self.game = Game(storage_service=self.storage_service)
        self.game.board.grid = [[None for _ in range(8)] for _ in range(8)]
        self.game.turn = "w"
        self.game.board.set_piece(0, 4, King("b"))
        self.game.board.set_piece(7, 4, King("w"))
        self.game.board.set_piece(7, 7, Rook("w"))
        self.game.board.set_piece(7, 0, Rook("w"))

    def test_castling_not_allowed_while_in_check(self):
        self.game.board.set_piece(0, 4, Rook("b"))

        piece, legal_moves = self.game.click_board(7, 4)

        self.assertNotIn((7, 6), legal_moves)
        self.assertNotIn((7, 2), legal_moves)
        self.assertFalse(self.game.make_move((7, 4), (7, 6)))
        self.assertFalse(self.game.make_move((7, 4), (7, 2)))

    def test_kingside_castling_not_allowed_through_attacked_square(self):
        self.game.board.set_piece(0, 5, Rook("b"))

        piece, legal_moves = self.game.click_board(7, 4)

        self.assertNotIn((7, 6), legal_moves)
        self.assertFalse(self.game.make_move((7, 4), (7, 6)))

    def test_queenside_castling_not_allowed_through_attacked_square(self):
        self.game.board.set_piece(0, 3, Rook("b"))

        piece, legal_moves = self.game.click_board(7, 4)

        self.assertNotIn((7, 2), legal_moves)
        self.assertFalse(self.game.make_move((7, 4), (7, 2)))

    def test_make_move_returns_false_for_illegal_move(self):
        self.assertFalse(self.game.make_move((7, 7), (5, 6)))
        self.assertEqual(str(self.game.board.get_piece(7, 7)), "wR")
        self.assertIsNone(self.game.board.get_piece(5, 6))
        self.assertEqual(self.game.turn, "w")
        self.assertEqual(len(self.storage_service.saved_moves), 0)

    def test_make_move_capture_saves_move_and_switches_turn(self):
        self.game.board.set_piece(5, 7, Rook("b"))

        self.assertTrue(self.game.make_move((7, 7), (5, 7)))

        self.assertEqual(str(self.game.board.get_piece(5, 7)), "wR")
        self.assertEqual(self.game.turn, "b")
        self.assertEqual(self.game.halfmove_clock, 0)
        self.assertEqual(self.game.fullmove_number, 1)
        self.assertEqual(len(self.storage_service.saved_moves), 1)

    def test_make_move_en_passant_counts_as_capture(self):
        self.game.board.grid = [[None for _ in range(8)] for _ in range(8)]
        self.game.board.set_piece(7, 4, King("w"))
        self.game.board.set_piece(0, 4, King("b"))
        self.game.board.set_piece(3, 4, Pawn("w"))
        self.game.board.set_piece(3, 5, Pawn("b"))
        self.game.board.en_passant_target = (2, 5)
        self.game.halfmove_clock = 7

        self.assertTrue(self.game.make_move((3, 4), (2, 5)))

        self.assertEqual(str(self.game.board.get_piece(2, 5)), "wP")
        self.assertIsNone(self.game.board.get_piece(3, 5))
        self.assertEqual(self.game.halfmove_clock, 0)
        self.assertEqual(self.game.turn, "b")
        self.assertEqual(len(self.storage_service.saved_moves), 1)

    def test_make_move_promotion_pending_does_not_switch_turn(self):
        self.game.board.grid = [[None for _ in range(8)] for _ in range(8)]
        self.game.board.set_piece(7, 4, King("w"))
        self.game.board.set_piece(0, 4, King("b"))
        self.game.board.set_piece(1, 0, Pawn("w"))

        self.assertTrue(self.game.make_move((1, 0), (0, 0)))

        self.assertEqual(self.game.turn, "w")
        self.assertIsNotNone(self.game.board.pending_promotion)
        self.assertIsNotNone(self.game.last_move_context)
        self.assertEqual(self.game.last_move_context["start"], (1, 0))
        self.assertEqual(self.game.last_move_context["end"], (0, 0))
        self.assertEqual(self.game.last_move_context["piece"], "P")
        self.assertEqual(len(self.storage_service.saved_moves), 0)

    def test_complete_promotion_returns_false_without_pending_promotion(self):
        self.assertFalse(self.game.complete_promotion("Q"))
        self.assertEqual(self.game.turn, "w")
        self.assertEqual(len(self.storage_service.saved_moves), 0)

    def test_complete_promotion_returns_false_for_invalid_piece_type(self):
        self.game.board.set_piece(7, 4, King("w"))
        self.game.board.set_piece(0, 4, King("b"))
        self.game.board.set_piece(1, 0, Pawn("w"))
        self.assertTrue(self.game.make_move((1, 0), (0, 0)))

        self.assertFalse(self.game.complete_promotion("X"))
        self.assertIsNotNone(self.game.board.pending_promotion)
        self.assertEqual(self.game.turn, "w")
        self.assertEqual(len(self.storage_service.saved_moves), 0)

    def test_complete_promotion_switches_turn_and_saves_promotion(self):
        self.game.board.set_piece(7, 4, King("w"))
        self.game.board.set_piece(0, 4, King("b"))
        self.game.board.set_piece(1, 0, Pawn("w"))
        self.assertTrue(self.game.make_move((1, 0), (0, 0)))

        self.assertTrue(self.game.complete_promotion("q"))

        self.assertIsInstance(self.game.board.get_piece(0, 0), Queen)
        self.assertEqual(self.game.turn, "b")
        self.assertIsNone(self.game.board.pending_promotion)
        self.assertIsNone(self.game.last_move_context)
        self.assertEqual(len(self.storage_service.saved_moves), 1)
        self.assertEqual(self.storage_service.saved_moves[0]["kwargs"]["promotion"], "Q")

    def test_switch_turn_without_context_only_switches_turn(self):
        self.game.turn = "w"
        self.game.halfmove_clock = 5
        self.game.fullmove_number = 9
        self.game.last_move_context = None

        self.game.switch_turn()

        self.assertEqual(self.game.turn, "b")
        self.assertEqual(self.game.halfmove_clock, 5)
        self.assertEqual(self.game.fullmove_number, 9)
        self.assertEqual(len(self.storage_service.saved_moves), 0)

    def test_switch_turn_resets_halfmove_clock_after_capture(self):
        self.game.turn = "w"
        self.game.halfmove_clock = 6
        self.game.fullmove_number = 2
        self.game.last_move_context = {
            "start": (7, 7),
            "end": (5, 7),
            "piece": "R",
            "promotion": None,
            "is_pawn_move": False,
            "is_capture": True,
        }

        self.game.switch_turn()

        self.assertEqual(self.game.turn, "b")
        self.assertEqual(self.game.halfmove_clock, 0)
        self.assertEqual(self.game.fullmove_number, 2)
        self.assertIsNone(self.game.last_move_context)

    def test_switch_turn_increments_halfmove_clock_after_quiet_move(self):
        self.game.turn = "w"
        self.game.halfmove_clock = 6
        self.game.fullmove_number = 2
        self.game.last_move_context = {
            "start": (7, 7),
            "end": (7, 6),
            "piece": "R",
            "promotion": None,
            "is_pawn_move": False,
            "is_capture": False,
        }

        self.game.switch_turn()

        self.assertEqual(self.game.turn, "b")
        self.assertEqual(self.game.halfmove_clock, 7)
        self.assertEqual(self.game.fullmove_number, 2)

    def test_switch_turn_increments_fullmove_number_after_black_move(self):
        self.game.turn = "b"
        self.game.halfmove_clock = 10
        self.game.fullmove_number = 4
        self.game.last_move_context = {
            "start": (0, 0),
            "end": (0, 1),
            "piece": "R",
            "promotion": None,
            "is_pawn_move": False,
            "is_capture": False,
        }

        self.game.switch_turn()

        self.assertEqual(self.game.turn, "w")
        self.assertEqual(self.game.halfmove_clock, 11)
        self.assertEqual(self.game.fullmove_number, 5)

    def test_draw_by_fifty_move_rule_is_detected_automatically(self):
        self.game.board.grid = [[None for _ in range(8)] for _ in range(8)]
        self.game.board.set_piece(7, 4, King("w"))
        self.game.board.set_piece(0, 4, King("b"))
        self.game.board.set_piece(7, 0, Rook("w"))
        self.game.board.set_piece(0, 7, Rook("b"))
        self.game.turn = "w"
        self.game.halfmove_clock = 99
        self.game.result = None
        self.game.board.position_counts = {}
        self.game._record_current_position()

        self.assertTrue(self.game.make_move((7, 0), (6, 0)))

        self.assertEqual(self.game.result, {"type": "fifty_move_rule"})
        self.assertEqual(len(self.storage_service.finished_games), 1)
        self.assertEqual(
            self.storage_service.finished_games[0]["kwargs"]["result_type"],
            "fifty_move_rule",
        )

    def test_draw_by_threefold_repetition_is_detected_automatically(self):
        self.game.board.grid = [[None for _ in range(8)] for _ in range(8)]
        self.game.board.set_piece(7, 4, King("w"))
        self.game.board.set_piece(0, 4, King("b"))
        self.game.board.set_piece(7, 6, Knight("w"))
        self.game.board.set_piece(0, 6, Knight("b"))
        self.game.turn = "w"
        self.game.result = None
        self.game.halfmove_clock = 0
        self.game.fullmove_number = 1
        self.game.board.position_counts = {}
        self.game._record_current_position()

        cycle = [
            ((7, 6), (5, 5)),
            ((0, 6), (2, 5)),
            ((5, 5), (7, 6)),
            ((2, 5), (0, 6)),
        ]

        for _ in range(2):
            for start, end in cycle:
                self.assertTrue(self.game.make_move(start, end))

        self.assertEqual(self.game.result, {"type": "threefold_repetition"})
        self.assertEqual(len(self.storage_service.finished_games), 1)
        self.assertEqual(
            self.storage_service.finished_games[0]["kwargs"]["result_type"],
            "threefold_repetition",
        )

    def test_draw_by_insufficient_material_is_detected(self):
        self.game.board.grid = [[None for _ in range(8)] for _ in range(8)]
        self.game.board.set_piece(7, 4, King("w"))
        self.game.board.set_piece(0, 4, King("b"))
        self.game.turn = "w"
        self.game.result = None
        self.game.board.position_counts = {}
        self.game._record_current_position()

        self.game._update_turn_state()

        self.assertEqual(self.game.result, {"type": "insufficient_material"})

if __name__ == "__main__":
    unittest.main()
