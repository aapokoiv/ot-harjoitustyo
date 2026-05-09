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

    def create_game(
        self,
        initial_fen: str,
        *,
        clock_enabled: bool = False,
        initial_seconds: int | None = None,
        increment_seconds: int = 0,
        white_time_ms: int | None = None,
        black_time_ms: int | None = None,
    ) -> int:
        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO games (
                    initial_fen,
                    clock_enabled,
                    initial_seconds,
                    increment_seconds,
                    white_time_ms,
                    black_time_ms,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    initial_fen,
                    1 if clock_enabled else 0,
                    initial_seconds,
                    increment_seconds,
                    white_time_ms,
                    black_time_ms,
                    "ongoing",
                ),
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
                    ended_at = CURRENT_TIMESTAMP,
                    status = 'finished'
                WHERE id = ?
                """,
                (result_type, winner, final_fen, game_id),
            )
    def update_game_clock(self, game_id: int, *, white_time_ms: int, black_time_ms: int):
        with self.conn:
            self.conn.execute(
                """
                UPDATE games
                SET white_time_ms = ?,
                    black_time_ms = ?
                WHERE id = ?
                """,
                (white_time_ms, black_time_ms, game_id),
            )
    def store_move(self, game_id: int, move_data: dict) -> int:
        start = move_data["start"]
        end = move_data["end"]
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
                    san,
                    white_time_ms, black_time_ms,
                    elapsed_ms,
                    fen_after
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    game_id,
                    ply,
                    from_row,
                    from_col,
                    to_row,
                    to_col,
                    move_data["piece"],
                    move_data.get("promotion"),
                    move_data.get("san"),
                    move_data.get("white_time_ms"),
                    move_data.get("black_time_ms"),
                    move_data.get("elapsed_ms"),
                    move_data["fen_after"],
                ),
            )
            return cursor.lastrowid

    def list_games(
        self,
        *,
        limit: int = 50,
        include_ongoing: bool = True,
        sort_desc: bool = True,
    ):
        order = "DESC" if sort_desc else "ASC"
        status_filter = "" if include_ongoing else "WHERE g.status = 'finished'"
        rows = self.conn.execute(
            f"""
            SELECT
                g.*,
                COALESCE(m.move_count, 0) AS move_count,
                CASE
                    WHEN g.ended_at IS NULL THEN NULL
                    ELSE CAST((julianday(g.ended_at) - julianday(g.created_at)) * 86400 AS INTEGER)
                END AS duration_seconds
            FROM games g
            LEFT JOIN (
                SELECT game_id, COUNT(*) AS move_count
                FROM moves
                GROUP BY game_id
            ) m ON g.id = m.game_id
            {status_filter}
            ORDER BY g.created_at {order}, g.id {order}
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_game(self, game_id: int):
        row = self.conn.execute(
            """
            SELECT
                g.*,
                COALESCE((SELECT COUNT(*) FROM moves WHERE game_id = g.id), 0) AS move_count
            FROM games g
            WHERE g.id = ?
            """,
            (game_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_moves(self, game_id: int):
        rows = self.conn.execute(
            """
            SELECT
                id,
                game_id,
                ply,
                from_row,
                from_col,
                to_row,
                to_col,
                piece,
                promotion,
                san,
                white_time_ms,
                black_time_ms,
                elapsed_ms,
                fen_after,
                created_at
            FROM moves
            WHERE game_id = ?
            ORDER BY ply ASC
            """,
            (game_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_latest_snapshot(self, game_id: int):
        move_row = self.conn.execute(
            """
            SELECT ply, fen_after
            FROM moves
            WHERE game_id = ?
            ORDER BY ply DESC
            LIMIT 1
            """,
            (game_id,),
        ).fetchone()
        if move_row is not None:
            return {
                "ply": int(move_row["ply"]),
                "fen": move_row["fen_after"],
            }
        game_row = self.conn.execute(
            "SELECT initial_fen FROM games WHERE id = ?",
            (game_id,),
        ).fetchone()
        if game_row is None:
            return None
        return {
            "ply": 0,
            "fen": game_row["initial_fen"],
        }

    def _last_ply(self, game_id: int) -> int:
        row = self.conn.execute(
            "SELECT COALESCE(MAX(ply), 0) AS max_ply FROM moves WHERE game_id = ?",
            (game_id,),
        ).fetchone()
        return int(row["max_ply"]) if row is not None else 0
