import unittest

from persistence.storage import SQLiteStorage

class TestSQLiteStorage(unittest.TestCase):
    def setUp(self):
        self.storage = SQLiteStorage(db_path=":memory:")
        self.addCleanup(self.storage.close)

    def test_create_game_persists_clock_fields_and_get_game_returns_row(self):
        game_id = self.storage.create_game(
            "start-fen",
            clock_enabled=True,
            initial_seconds=300,
            increment_seconds=2,
            white_time_ms=300000,
            black_time_ms=299000,
        )

        game = self.storage.get_game(game_id)

        self.assertEqual(game["initial_fen"], "start-fen")
        self.assertEqual(game["clock_enabled"], 1)
        self.assertEqual(game["initial_seconds"], 300)
        self.assertEqual(game["increment_seconds"], 2)
        self.assertEqual(game["white_time_ms"], 300000)
        self.assertEqual(game["black_time_ms"], 299000)
        self.assertEqual(game["status"], "ongoing")
        self.assertEqual(game["move_count"], 0)

    def test_store_move_assigns_incrementing_ply_and_latest_snapshot(self):
        game_id = self.storage.create_game("start-fen")

        first_move_id = self.storage.store_move(
            game_id,
            {
                "start": (6, 4),
                "end": (4, 4),
                "piece": "P",
                "fen_after": "fen-1",
                "elapsed_ms": 500,
            },
        )
        second_move_id = self.storage.store_move(
            game_id,
            {
                "start": (1, 4),
                "end": (3, 4),
                "piece": "P",
                "fen_after": "fen-2",
                "promotion": None,
            },
        )

        moves = self.storage.get_moves(game_id)
        snapshot = self.storage.get_latest_snapshot(game_id)

        self.assertEqual(first_move_id, 1)
        self.assertEqual(second_move_id, 2)
        self.assertEqual([move["ply"] for move in moves], [1, 2])
        self.assertEqual(moves[0]["from_row"], 6)
        self.assertEqual(moves[0]["to_row"], 4)
        self.assertEqual(moves[0]["elapsed_ms"], 500)
        self.assertEqual(snapshot, {"ply": 2, "fen": "fen-2"})

    def test_finish_game_update_clock_and_list_games_filter_ongoing(self):
        ongoing_game_id = self.storage.create_game("ongoing-fen")
        finished_game_id = self.storage.create_game("finished-fen")

        self.storage.update_game_clock(
            ongoing_game_id,
            white_time_ms=111000,
            black_time_ms=112000,
        )
        self.storage.finish_game(
            finished_game_id,
            result_type="checkmate",
            winner="b",
            final_fen="final-fen",
        )

        ongoing_game = self.storage.get_game(ongoing_game_id)
        finished_game = self.storage.get_game(finished_game_id)
        all_games = self.storage.list_games(limit=10)
        finished_games = self.storage.list_games(limit=10, include_ongoing=False)

        self.assertEqual(ongoing_game["white_time_ms"], 111000)
        self.assertEqual(ongoing_game["black_time_ms"], 112000)
        self.assertEqual(finished_game["status"], "finished")
        self.assertEqual(finished_game["result_type"], "checkmate")
        self.assertEqual(finished_game["winner"], "b")
        self.assertEqual(finished_game["final_fen"], "final-fen")
        self.assertEqual(len(all_games), 2)
        self.assertEqual(len(finished_games), 1)
        self.assertEqual(finished_games[0]["id"], finished_game_id)

    def test_close_clears_connection(self):
        self.storage.close()

        self.assertIsNone(self.storage.conn)
