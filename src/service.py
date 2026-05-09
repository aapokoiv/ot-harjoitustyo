from storage import SQLiteStorage


class MoveStorageService:
    def __init__(self, db_path: str | None = None):
        """Service exposing storage operations used by the Game class.

        Args:
            db_path (str | None): Path to the SQLite database file.
                If None, CHESS_DB_PATH or the project default is used.
        """
        self.storage = SQLiteStorage(db_path=db_path)

    def start_game(
        self,
        initial_fen: str,
        *,
        clock_enabled: bool = False,
        initial_seconds: int | None = None,
        increment_seconds: int = 0,
        white_time_ms: int | None = None,
        black_time_ms: int | None = None,
    ) -> int:
        return self.storage.create_game(
            initial_fen,
            clock_enabled=clock_enabled,
            initial_seconds=initial_seconds,
            increment_seconds=increment_seconds,
            white_time_ms=white_time_ms,
            black_time_ms=black_time_ms,
        )

    def save_move(self, game_id: int, move_data: dict | None = None, **kwargs) -> int:
        if move_data is None:
            move_data = kwargs
        return self.storage.store_move(game_id=game_id, move_data=move_data)

    def finish_game(
        self,
        game_id: int,
        *,
        result_type: str,
        winner: str | None,
        final_fen: str,
    ):
        self.storage.finish_game(
            game_id=game_id,
            result_type=result_type,
            winner=winner,
            final_fen=final_fen,
        )

    def update_game_clock(self, game_id: int, *, white_time_ms: int, black_time_ms: int):
        self.storage.update_game_clock(
            game_id,
            white_time_ms=white_time_ms,
            black_time_ms=black_time_ms,
        )
    def list_games(
        self,
        *,
        limit: int = 50,
        include_ongoing: bool = True,
        sort_desc: bool = True,
    ):
        return self.storage.list_games(
            limit=limit,
            include_ongoing=include_ongoing,
            sort_desc=sort_desc,
        )

    def get_game(self, game_id: int):
        return self.storage.get_game(game_id)

    def get_moves(self, game_id: int):
        return self.storage.get_moves(game_id)

    def get_latest_snapshot(self, game_id: int):
        return self.storage.get_latest_snapshot(game_id)

    def close(self):
        self.storage.close()
