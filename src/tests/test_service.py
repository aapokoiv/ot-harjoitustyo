import unittest
from unittest.mock import patch

from persistence.service import MoveStorageService


class FakeStorage:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.calls = []

    def create_game(self, *args, **kwargs):
        self.calls.append(("create_game", args, kwargs))
        return 11

    def store_move(self, *args, **kwargs):
        self.calls.append(("store_move", args, kwargs))
        return 22

    def finish_game(self, *args, **kwargs):
        self.calls.append(("finish_game", args, kwargs))

    def update_game_clock(self, *args, **kwargs):
        self.calls.append(("update_game_clock", args, kwargs))

    def list_games(self, *args, **kwargs):
        self.calls.append(("list_games", args, kwargs))
        return [{"id": 1}]

    def get_game(self, *args, **kwargs):
        self.calls.append(("get_game", args, kwargs))
        return {"id": 1}

    def get_moves(self, *args, **kwargs):
        self.calls.append(("get_moves", args, kwargs))
        return [{"ply": 1}]

    def get_latest_snapshot(self, *args, **kwargs):
        self.calls.append(("get_latest_snapshot", args, kwargs))
        return {"ply": 1, "fen": "fen"}

    def close(self):
        self.calls.append(("close", (), {}))


class TestMoveStorageService(unittest.TestCase):
    def setUp(self):
        storage_patcher = patch("persistence.service.SQLiteStorage", FakeStorage)
        self.addCleanup(storage_patcher.stop)
        storage_patcher.start()
        self.service = MoveStorageService(db_path=":memory:")

    def test_start_game_delegates_all_clock_fields_to_storage(self):
        game_id = self.service.start_game(
            "start-fen",
            clock_enabled=True,
            initial_seconds=300,
            increment_seconds=2,
            white_time_ms=300000,
            black_time_ms=299000,
        )

        self.assertEqual(game_id, 11)
        self.assertEqual(self.service.storage.calls[-1],("create_game",("start-fen",),
                {
                    "clock_enabled": True,
                    "initial_seconds": 300,
                    "increment_seconds": 2,
                    "white_time_ms": 300000,
                    "black_time_ms": 299000,
                },),)

    def test_save_move_uses_kwargs_as_move_data_when_dict_not_given(self):
        move_id = self.service.save_move(
            5,
            start=(6, 4),
            end=(4, 4),
            piece="P",
            fen_after="fen",
        )

        self.assertEqual(move_id, 22)
        self.assertEqual(
            self.service.storage.calls[-1],("store_move",(),
                {
                    "game_id": 5,
                    "move_data": {
                        "start": (6, 4),
                        "end": (4, 4),
                        "piece": "P",
                        "fen_after": "fen",
                    },
                },),)

    def test_read_methods_and_close_delegate_to_storage(self):
        self.assertEqual(self.service.list_games(limit=5, include_ongoing=False), [{"id": 1}])
        self.assertEqual(self.service.get_game(7), {"id": 1})
        self.assertEqual(self.service.get_moves(7), [{"ply": 1}])
        self.assertEqual(self.service.get_latest_snapshot(7), {"ply": 1, "fen": "fen"})

        self.service.close()

        self.assertEqual(self.service.storage.calls[-1], ("close", (), {}))
