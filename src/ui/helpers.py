from datetime import datetime
from pathlib import Path
import tkinter as tk


ASSET_DIR = Path(__file__).resolve().parent.parent.parent / "assets"

PIECE_FILE_MAP = {
    "wK": "Chess_klt60.png",
    "bK": "Chess_kdt60.png",
    "wQ": "Chess_qlt60.png",
    "bQ": "Chess_qdt60.png",
    "wR": "Chess_rlt60.png",
    "bR": "Chess_rdt60.png",
    "wB": "Chess_blt60.png",
    "bB": "Chess_bdt60.png",
    "wN": "Chess_nlt60.png",
    "bN": "Chess_ndt60.png",
    "wP": "Chess_plt60.png",
    "bP": "Chess_pdt60.png",
}


def load_piece_images():
    """Load available chess piece images from the assets directory.

    Returns:
        dict[str, tk.PhotoImage]: Mapping from piece keys such as ``"wK"`` to
            Tk image objects.
    """
    images = {}
    for piece_key, filename in PIECE_FILE_MAP.items():
        file_path = ASSET_DIR / filename
        if file_path.exists():
            images[piece_key] = tk.PhotoImage(file=str(file_path))
    return images


def format_timestamp(value):
    """Format a database timestamp for display in the UI."""
    if not value:
        return "Unknown"
    try:
        timestamp = datetime.fromisoformat(str(value))
    except ValueError:
        return str(value)
    return timestamp.strftime("%Y-%m-%d %H:%M")


def format_clock_ms(milliseconds):
    """Format milliseconds into a short chess-clock display string."""
    if milliseconds is None:
        return "--:--"
    total_seconds = max(milliseconds / 1000, 0)
    if total_seconds >= 60:
        minutes = int(total_seconds // 60)
        seconds = total_seconds - (minutes * 60)
        return f"{minutes:02d}:{seconds:04.1f}"
    return f"{total_seconds:0.1f}s"


def format_time_control(clock_enabled, initial_seconds, increment_seconds):
    """Return a human-readable summary of a game's time control."""
    if not clock_enabled:
        return "Untimed"
    base_minutes = int(initial_seconds or 0) // 60
    increment = int(increment_seconds or 0)
    return f"{base_minutes}+{increment}"


def result_text(result):
    """Convert a game result dictionary into user-facing text."""
    if result is None:
        return "In progress"
    result_type = result.get("type")
    if result_type == "checkmate":
        winner = "White" if result.get("winner") == "w" else "Black"
        return f"Checkmate, {winner} wins"
    if result_type == "timeout":
        winner = "White" if result.get("winner") == "w" else "Black"
        return f"Timeout, {winner} wins"
    mapping = {
        "stalemate": "Stalemate",
        "threefold_repetition": "Draw by repetition",
        "fifty_move_rule": "Draw by 50-move rule",
        "insufficient_material": "Draw by insufficient material",
    }
    return mapping.get(result_type, str(result_type).replace("_", " ").title())


def game_row_result_text(game_row):
    """Return display text for a persisted game row's result."""
    if game_row.get("status") == "ongoing":
        return "Ongoing"
    return result_text({
        "type": game_row.get("result_type"),
        "winner": game_row.get("winner"),
    })


def build_move_rows(moves):
    """Group move records into numbered rows for listbox display."""
    rows = []
    for index in range(0, len(moves), 2):
        white_move = moves[index]
        black_move = moves[index + 1] if index + 1 < len(moves) else None
        move_number = index // 2 + 1
        white_san = white_move.get("san") or ""
        black_san = black_move.get("san") if black_move is not None else ""
        rows.append(f"{move_number:>2}. {white_san:<8} {black_san}".rstrip())
    return rows
