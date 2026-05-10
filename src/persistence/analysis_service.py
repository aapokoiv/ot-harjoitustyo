import json
import os
from pathlib import Path
import subprocess
import sys
from dotenv import load_dotenv
from persistence.service import MoveStorageService

load_dotenv()

DEFAULT_ANALYSIS_TIME_MS = 150
DEFAULT_STOCKFISH_PATH = (
    Path(__file__).resolve().parents[2] / "engine" / "stockfish-ubuntu-x86-64-avx2"
)
STOCKFISH_PATH_ENV = "STOCKFISH_PATH"

class StockfishAnalysisService:
    """Analyze finished games with Stockfish and persist move evaluations."""

    def __init__(
        self,
        storage_service,
        *,
        movetime_ms: int = DEFAULT_ANALYSIS_TIME_MS,
    ):
        self.db_path = storage_service.storage.db_path
        self.stockfish_path, self.stockfish_unavailable_reason = self._resolve_stockfish_path()
        self.movetime_ms = movetime_ms
        self.worker_path = Path(__file__).with_name("engine_worker.py")

    def analyze_game(self, game_id: int):
        """Analyze a finished game once and save evaluations for each move."""
        if not self.stockfish_path:
            return {
                "status": "unavailable",
                "reason": self.stockfish_unavailable_reason,
            }

        service = MoveStorageService(db_path=self.db_path)
        try:
            game_row = service.get_game(game_id)
            if game_row is None:
                return {"status": "missing"}
            if game_row.get("status") != "finished":
                return {"status": "skipped"}
            if not service.game_needs_analysis(game_id):
                return {"status": "cached"}

            moves = service.get_moves(game_id)
            if not moves:
                return {"status": "skipped"}

            positions = [game_row["initial_fen"]]
            positions.extend(move["fen_after"] for move in moves)
            scores = self._run_worker(positions)

            for index, move in enumerate(moves, start=1):
                current = scores[index]
                previous = scores[index - 1]
                service.save_move_analysis(
                    move["id"],
                    eval_cp=current.get("eval_cp"),
                    eval_mate=current.get("eval_mate"),
                    eval_delta_cp=self._compute_delta_cp(previous, current),
                )

            return {"status": "analyzed", "move_count": len(moves)}
        finally:
            service.close()

    ### AI code starting
    @staticmethod
    def _resolve_stockfish_path() -> tuple[str | None, str]:
        configured_path = os.getenv(STOCKFISH_PATH_ENV)
        if configured_path:
            resolved_path = Path(configured_path).expanduser()
            if StockfishAnalysisService._is_usable_engine_path(resolved_path):
                return str(resolved_path), ""
            return (
                None,
                f"{STOCKFISH_PATH_ENV} points to a missing or non-executable file: {resolved_path}",
            )

        if StockfishAnalysisService._is_usable_engine_path(DEFAULT_STOCKFISH_PATH):
            return str(DEFAULT_STOCKFISH_PATH), ""

        return (
            None,
            f"No usable Stockfish engine found. Checked bundled path: {DEFAULT_STOCKFISH_PATH}",
        )

    @staticmethod
    def _is_usable_engine_path(path: Path) -> bool:
        return path.is_file() and os.access(path, os.X_OK)

    def _run_worker(self, positions: list[str]):
        payload = {
            "stockfish_path": self.stockfish_path,
            "movetime_ms": self.movetime_ms,
            "positions": positions,
        }
        completed = subprocess.run(
            [sys.executable, str(self.worker_path)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
        )
        response = json.loads(completed.stdout)
        return response["results"]
    ### AI code ending

    @staticmethod
    def _compute_delta_cp(previous_score: dict, current_score: dict) -> int | None:
        previous_cp = previous_score.get("eval_cp")
        current_cp = current_score.get("eval_cp")
        if previous_cp is None or current_cp is None:
            return None
        if (
            previous_score.get("eval_mate") is not None
            or current_score.get("eval_mate") is not None
        ):
            return None
        return current_cp - previous_cp
