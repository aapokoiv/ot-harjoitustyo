import os
from pathlib import Path
import sqlite3


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chess.db"


class SQLiteStorage:
    def __init__(self, db_path: str | None = None):
        resolved_db_path = db_path or os.getenv("CHESS_DB_PATH") or str(DEFAULT_DB_PATH)

        if resolved_db_path != ":memory:":
            Path(resolved_db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = resolved_db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.ensure_schema()

    def _init_db(self):
        schema_path = Path(__file__).with_name("schema.sql")
        schema = schema_path.read_text(encoding="utf-8")
        with self.conn:
            self.conn.executescript(schema)

    def ensure_schema(self):
        self._init_db()

    def close(self):
        if getattr(self, "conn", None) is not None:
            self.conn.close()
            self.conn = None

    def create_game(self, initial_fen: str) -> int:
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO games (initial_fen) VALUES (?)",
                (initial_fen,),
            )
            return cursor.lastrowid

    def finish_game(
        self,
        game_id: int,
        *,
        result_type: str,
        winner: str | None,
        final_fen: str,
    ):
        with self.conn:
            self.conn.execute(
                """
                UPDATE games
                SET result_type = ?,
                    winner = ?,
                    final_fen = ?,
                    ended_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (result_type, winner, final_fen, game_id),
            )

    def store_move(
        self,
        game_id: int,
        *,
        start: tuple[int, int],
        end: tuple[int, int],
        piece: str,
        fen_after: str,
        promotion: str | None = None,
    ) -> int:
        from_row, from_col = start
        to_row, to_col = end
        ply = self._last_ply(game_id) + 1

        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO moves (
                    game_id, ply,
                    from_row, from_col, to_row, to_col,
                    piece, promotion,
                    fen_after
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    game_id,
                    ply,
                    from_row,
                    from_col,
                    to_row,
                    to_col,
                    piece,
                    promotion,
                    fen_after,
                ),
            )
            return cursor.lastrowid

    def _last_ply(self, game_id: int) -> int:
        row = self.conn.execute(
            "SELECT COALESCE(MAX(ply), 0) AS max_ply FROM moves WHERE game_id = ?",
            (game_id,),
        ).fetchone()
        return int(row["max_ply"]) if row is not None else 0
