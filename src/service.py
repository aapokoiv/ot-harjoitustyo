from storage import SQLiteStorage


class MoveStorageService:
    def __init__(self, db_path: str = "data/chess.db"):
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

    def close(self):
        self.storage.close()
