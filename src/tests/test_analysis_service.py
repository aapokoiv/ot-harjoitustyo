import unittest
from unittest.mock import patch

from persistence.analysis_service import StockfishAnalysisService


class FakeStorageService:
    def __init__(self, db_path=":memory:"):
        self.storage = type("Storage", (), {"db_path": db_path})()


class FakeMoveStorageService:
    game_row = None
    needs_analysis = True
    moves = []
    instances = []

    def __init__(self, db_path=None):
        self.db_path = db_path
        self.saved_analyses = []
        self.closed = False
        FakeMoveStorageService.instances.append(self)

    def get_game(self, _game_id):
        return self.game_row

    def game_needs_analysis(self, _game_id):
        return self.needs_analysis

    def get_moves(self, _game_id):
        return self.moves

    def save_move_analysis(self, move_id, **kwargs):
        self.saved_analyses.append((move_id, kwargs))

    def close(self):
        self.closed = True


class TestStockfishAnalysisService(unittest.TestCase):
    def setUp(self):
        FakeMoveStorageService.game_row = None
        FakeMoveStorageService.needs_analysis = True
        FakeMoveStorageService.moves = []
        FakeMoveStorageService.instances = []

    def test_analyze_game_returns_cached_when_moves_are_already_analyzed(self):
        FakeMoveStorageService.game_row = {"status": "finished", "initial_fen": "start-fen"}
        FakeMoveStorageService.needs_analysis = False

        with patch.object(
            StockfishAnalysisService,
            "_resolve_stockfish_path",
            return_value=("/tmp/stockfish", ""),
        ), patch("persistence.analysis_service.MoveStorageService", FakeMoveStorageService):
            service = StockfishAnalysisService(FakeStorageService())

            with patch.object(service, "_run_worker") as run_worker:
                result = service.analyze_game(7)

        self.assertEqual(result, {"status": "cached"})
        self.assertFalse(run_worker.called)
        self.assertTrue(FakeMoveStorageService.instances[-1].closed)

    def test_analyze_game_saves_scores_for_each_move(self):
        FakeMoveStorageService.game_row = {"status": "finished", "initial_fen": "start-fen"}
        FakeMoveStorageService.moves = [
            {"id": 101, "fen_after": "fen-1"},
            {"id": 102, "fen_after": "fen-2"},
        ]

        with patch.object(
            StockfishAnalysisService,
            "_resolve_stockfish_path",
            return_value=("/tmp/stockfish", ""),
        ), patch("persistence.analysis_service.MoveStorageService", FakeMoveStorageService):
            service = StockfishAnalysisService(FakeStorageService())

            with patch.object(
                service,
                "_run_worker",
                return_value=[
                    {"eval_cp": 10, "eval_mate": None},
                    {"eval_cp": 30, "eval_mate": None},
                    {"eval_cp": 5, "eval_mate": None},
                ],
            ) as run_worker:
                result = service.analyze_game(9)

        saved_analyses = FakeMoveStorageService.instances[-1].saved_analyses

        self.assertEqual(result, {"status": "analyzed", "move_count": 2})
        run_worker.assert_called_once_with(["start-fen", "fen-1", "fen-2"])
        self.assertEqual(
            saved_analyses,
            [
                (101, {"eval_cp": 30, "eval_mate": None, "eval_delta_cp": 20}),
                (102, {"eval_cp": 5, "eval_mate": None, "eval_delta_cp": -25}),
            ],
        )
        self.assertTrue(FakeMoveStorageService.instances[-1].closed)
