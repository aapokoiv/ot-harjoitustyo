from storage import SQLiteStorage


class MoveStorageService:
    def __init__(self, db_path: str | None = None):
        """Service exposing storage operations used by the Game class.

        Args:
            db_path (str | None): Path to the SQLite database file.
                If None, CHESS_DB_PATH or the project default is used.
        """
        self.storage = SQLiteStorage(db_path=db_path)

    def start_game(self, initial_fen: str) -> int:
        return self.storage.create_game(initial_fen)

    def save_move(
        self,
        game_id: int,
        *,
        start: tuple[int, int],
        end: tuple[int, int],
        piece: str,
        fen_after: str,
        promotion: str | None = None,
    ) -> int:
        return self.storage.store_move(
            game_id=game_id,
            start=start,
            end=end,
            piece=piece,
            fen_after=fen_after,
            promotion=promotion,
        )

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

    def close(self):
        self.storage.close()
