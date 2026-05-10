from persistence.storage import SQLiteStorage

class MoveStorageService:
    """High-level storage API used by game and UI code.

    Attributes:
        storage (SQLiteStorage): Underlying SQLite-backed storage implementation.
    """

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
        """Create and persist a new game row.

        Returns:
            int: Database id of the created game.
        """
        return self.storage.create_game(
            initial_fen,
            clock_enabled=clock_enabled,
            initial_seconds=initial_seconds,
            increment_seconds=increment_seconds,
            white_time_ms=white_time_ms,
            black_time_ms=black_time_ms,
        )

    def save_move(self, game_id: int, move_data: dict | None = None, **kwargs) -> int:
        """Persist a move for a game and return its row id."""
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
        """Mark a game finished and persist its final result."""
        self.storage.finish_game(
            game_id=game_id,
            result_type=result_type,
            winner=winner,
            final_fen=final_fen,
        )

    def update_game_clock(self, game_id: int, *, white_time_ms: int, black_time_ms: int):
        """Persist the latest remaining clock values for a game."""
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
        """Return saved games for history and menu views."""
        return self.storage.list_games(
            limit=limit,
            include_ongoing=include_ongoing,
            sort_desc=sort_desc,
        )

    def get_game(self, game_id: int):
        """Return one game row as a dictionary, or (None) if missing."""
        return self.storage.get_game(game_id)

    def get_moves(self, game_id: int):
        """Return persisted moves for a game ordered by ply."""
        return self.storage.get_moves(game_id)

    def get_latest_snapshot(self, game_id: int):
        """Return the newest stored position snapshot for a game."""
        return self.storage.get_latest_snapshot(game_id)

    def close(self):
        """Close the underlying storage connection."""
        self.storage.close()
