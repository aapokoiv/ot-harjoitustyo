from dataclasses import dataclass

from logic.board import Board
from logic.clock import ClockState
from logic.fen import parse_fen
from logic.piece import Bishop, King, Knight, Pawn
from persistence.service import MoveStorageService

def _opponent(color: str):
    return "b" if color == "w" else "w"

def _coords_to_square(coords: tuple[int, int]):
    row, col = coords
    file_char = chr(ord("a") + col)
    rank_char = str(8 - row)
    return f"{file_char}{rank_char}"


@dataclass
class ClockConfig:
    """Configuration and persisted values for the optional game clock.

    Attributes:
        enabled (bool): Whether the game uses a clock.
        initial_seconds (int | None): Base time per side in seconds.
        increment_seconds (int): Increment added after each completed move.
        white_time_ms (int | None): Persisted white clock time in milliseconds.
        black_time_ms (int | None): Persisted black clock time in milliseconds.
    """

    enabled: bool = False
    initial_seconds: int | None = None
    increment_seconds: int = 0
    white_time_ms: int | None = None
    black_time_ms: int | None = None


@dataclass
class PositionState:
    """Mutable position data owned by a game instance.

    Attributes:
        board (Board): Current board state.
        turn (str): Side to move, either ``"w"`` or ``"b"``.
        halfmove_clock (int): Fifty-move rule counter.
        fullmove_number (int): Full-move counter for FEN output.
    """

    board: Board
    turn: str
    halfmove_clock: int
    fullmove_number: int


POSITION_FIELDS = {"board", "turn", "halfmove_clock", "fullmove_number"}
CLOCK_FIELDS = {
    "clock_enabled": "enabled",
    "initial_seconds": "initial_seconds",
    "increment_seconds": "increment_seconds",
    "white_time_ms": "white_time_ms",
    "black_time_ms": "black_time_ms",
}

class Game:
    """Manages the game coordinating board state and move persistence.

    The Game class owns a :class:`Board` and enforces move legality, turn
    progression, clock updates, and persistence of moves via a
    MoveStorageService.

    Attributes:
        storage_service (MoveStorageService): Backend used to store games and moves.
        result (dict | None): Current finished-game result, if any.
        last_move_context (dict | None): Metadata collected while finalizing a move.
        clock_state (ClockState | None): Active chess clock state for timed games.
        game_id (int | None): Persistent database id for the game.
    """
    def __init__(
        self,
        storage_service=None,
        *,
        game_id: int | None = None,
        initial_fen: str | None = None,
        clock_config: ClockConfig | None = None,
        create_storage_row: bool = True,
    ):
        """Create a new game instance.

        Args:
            storage_service (MoveStorageService | None): Service used to persist
                game data. A default instance is created when omitted.
            game_id (int | None): Existing persistent id when loading a saved game.
            initial_fen (str | None): Starting position in FEN form.
            clock_config (ClockConfig | None): Clock configuration for the game.
            create_storage_row (bool): Whether to create a new game row in storage.
        """
        self.storage_service = storage_service or MoveStorageService()
        self.result = None
        self.last_move_context = None
        self._position = self._init_position(initial_fen)
        self._clock = clock_config or ClockConfig()
        self.clock_state = None
        self._init_clock_state()
        self.game_id = game_id
        self._create_storage_row(create_storage_row)
        self._record_current_position()
        self._update_turn_state()
        if self.clock_state is not None and self.result is None:
            self.clock_state.start(self._position.turn)

    @classmethod
    def load_existing(cls, game_id: int, storage_service=None):
        """Load an ongoing game from persistence.

        Args:
            game_id (int): Identifier of the game to continue.
            storage_service (MoveStorageService | None): Storage service to use.

        Returns:
            Game: Reconstructed ongoing game.

        Raises:
            ValueError: If the game does not exist, is finished, or lacks a snapshot.
        """
        service = storage_service or MoveStorageService()
        game_row = service.get_game(game_id)
        if game_row is None:
            raise ValueError(f"Game with id {game_id} not found")
        if game_row.get("status") != "ongoing":
            raise ValueError(f"Game {game_id} is finished and must be opened in review mode")
        moves = service.get_moves(game_id)
        snapshot = service.get_latest_snapshot(game_id)
        if snapshot is None:
            raise ValueError(f"No snapshot found for game {game_id}")
        game = cls(
            storage_service=service,
            game_id=game_id,
            initial_fen=snapshot["fen"],
            clock_config=ClockConfig(
                enabled=bool(game_row.get("clock_enabled", 0)),
                initial_seconds=game_row.get("initial_seconds"),
                increment_seconds=int(game_row.get("increment_seconds") or 0),
                white_time_ms=game_row.get("white_time_ms"),
                black_time_ms=game_row.get("black_time_ms"),
            ),
            create_storage_row=False,
        )
        position_fens = [game_row["initial_fen"]]
        position_fens.extend(move["fen_after"] for move in moves)
        game._restore_position_history(position_fens)
        return game

    def __getattr__(self, name):
        if name in POSITION_FIELDS:
            return getattr(self._position, name)
        if name in CLOCK_FIELDS:
            return getattr(self._clock, CLOCK_FIELDS[name])
        raise AttributeError(f"{type(self).__name__!s} has no attribute {name!r}")

    def __setattr__(self, name, value):
        if name in POSITION_FIELDS and "_position" in self.__dict__:
            setattr(self._position, name, value)
            return
        if name in CLOCK_FIELDS and "_clock" in self.__dict__:
            setattr(self._clock, CLOCK_FIELDS[name], value)
            return
        super().__setattr__(name, value)

    @staticmethod
    def _init_position(initial_fen):
        if initial_fen is None:
            board = Board()
            board.set_starting_position()
            return PositionState(board=board, turn="w", halfmove_clock=0, fullmove_number=1)

        fen_state = parse_fen(initial_fen, Board)
        return PositionState(
            board=fen_state["board"],
            turn=fen_state["side_to_move"],
            halfmove_clock=fen_state["halfmove_clock"],
            fullmove_number=fen_state["fullmove_number"],
        )

    def _init_clock_state(self):
        if not self._clock.enabled:
            return

        self.clock_state = ClockState(
            initial_seconds=int(self._clock.initial_seconds or 0),
            increment_seconds=self._clock.increment_seconds,
        )
        if self._clock.white_time_ms is not None and self._clock.black_time_ms is not None:
            self.clock_state.set_remaining(
                white_time_ms=self._clock.white_time_ms,
                black_time_ms=self._clock.black_time_ms,
            )
        self._sync_clock_times()

    def _create_storage_row(self, create_storage_row):
        if self.game_id is not None or not create_storage_row:
            return

        initial_fen_for_storage = self._position.board.to_fen(
            self._position.turn,
            self._position.halfmove_clock,
            self._position.fullmove_number,
        )
        if self._clock.enabled:
            self.game_id = self.storage_service.start_game(
                initial_fen_for_storage,
                clock_enabled=self._clock.enabled,
                initial_seconds=self._clock.initial_seconds,
                increment_seconds=self._clock.increment_seconds,
                white_time_ms=self._clock.white_time_ms,
                black_time_ms=self._clock.black_time_ms,
            )
            return

        self.game_id = self.storage_service.start_game(initial_fen_for_storage)

    def _restore_position_history(self, position_fens):
        self.board.position_counts = {}
        for fen in position_fens:
            fen_state = parse_fen(fen, Board)
            board = fen_state["board"]
            side_to_move = fen_state["side_to_move"]
            key = board.repetition_key(side_to_move)
            self.board.position_counts[key] = self.board.position_counts.get(key, 0) + 1

    def make_move(self, start, end):
        """Attempt to make a move from start to end for the current player.

        Args:
            start (tuple[int, int]): (row, col) coordinates of the source square.
            end (tuple[int, int]): (row, col) coordinates of the destination square.

        Returns:
            bool: True if the move was executed (or a promotion was set), False
                if the move is illegal or the game is already finished or a
                promotion is pending.
        """
        if self.result is not None or self.board.pending_promotion is not None:
            return False
        if self.clock_state is not None and self.handle_clock_tick():
            return False
        if not self.is_move_legal(start, end, self.turn):
            return False
        piece = self.board.get_piece(start[0], start[1])
        target_piece = self.board.get_piece(end[0], end[1])
        is_capture = target_piece is not None
        if isinstance(piece, Pawn) and end == self.board.en_passant_target:
            is_capture = True
        self.last_move_context = {
            "start": start,
            "end": end,
            "piece": piece.symbol,
            "piece_color": piece.color,
            "promotion": None,
            "is_pawn_move": isinstance(piece, Pawn),
            "is_capture": is_capture,
            "is_castling": self._is_castling_move(piece, start, end),
            "board_before": self.board.clone(),
        }
        self.board.move_piece(start, end)
        if self.board.pending_promotion is not None:
            return True
        self.switch_turn()
        return True

    def complete_promotion(self, piece_type):
        """Complete a pending pawn promotion.

        Args:
            piece_type (str): One-letter code for the promotion piece (Q,R,B,N).

        Returns:
            bool: True if the promotion succeeded and the turn was switched,
                False if there was no pending promotion or the piece type was invalid.
        """
        if self.board.pending_promotion is None:
            return False
        success = self.board.promote(piece_type)
        if not success:
            return False
        if self.last_move_context is not None:
            self.last_move_context["promotion"] = piece_type.upper()
        self.switch_turn()
        return True

    def click_board(self, row, col):
        """Return the piece on a square and its legal moves for the current turn.

        Args:
            row (int): Row index of the square.
            col (int): Column index of the square.

        Returns:
            tuple: (piece, legal_moves) where piece is the piece instance or
                None and legal_moves is a list of (row, col) destinations that
                are legal for the current player.
        """
        piece = self.board.get_piece(row, col)
        if self.result is not None or self.board.pending_promotion is not None:
            return piece, []
        if piece is None:
            return piece, []
        moves = piece.get_moves((row, col), self.board)
        legal_moves = []
        for move in moves:
            if self.is_move_legal((row, col), move, self.turn):
                legal_moves.append(move)
        return piece, legal_moves

    def is_move_legal(self, start, end, color):
        """Return True if a particular move is legal for a given color.

        The legality checks include basic move generation for the piece,
        ensuring the destination is not occupied by a king, castling rules,
        and verifying the move does not leave the player's own king in 
        check by simulating the move on a cloned board.

        Args:
            start (tuple[int, int]): Source square coordinates.
            end (tuple[int, int]): Destination square coordinates.
            color (str): 'w' or 'b' for the side attempting the move.

        Returns:
            bool: True if the move is legal, False otherwise.
        """
        if self.result is not None or self.board.pending_promotion is not None:
            return False
        return self._is_move_legal_on_board(self.board, start, end, color)

    def _is_move_legal_on_board(self, board_state, start, end, color):
        piece = board_state.get_piece(start[0], start[1])
        if piece is None or piece.color != color:
            return False
        moves = piece.get_moves(start, board_state)
        if end not in moves:
            return False
        target_piece = board_state.get_piece(end[0], end[1])
        if isinstance(target_piece, King):
            return False
        if self._is_castling_move(piece, start, end):
            opponent_color = _opponent(color)
            col_between = start[1] + (1 if end[1] > start[1] else -1)
            if (
                board_state.is_square_attacked(start[0], start[1], opponent_color)
                or board_state.is_square_attacked(start[0], col_between, opponent_color)
                or board_state.is_square_attacked(start[0], end[1], opponent_color)
            ):
                return False
        board_after_move = board_state.clone()
        board_after_move.move_piece(start, end)
        return not board_after_move.is_king_in_check(color)

    @staticmethod
    def _is_castling_move(piece, start, end):
        return isinstance(piece, King) and start[0] == end[0] and abs(start[1] - end[1]) == 2

    def switch_turn(self):
        """Advance the game to the next player's turn.

        If there is a recorded last move context, this method updates the
        halfmove clock, fullmove number, persists the move via the storage
        service, and updates check/checkmate/stalemate state. When called with
        no context it simply flips the active player.
        """
        if self.last_move_context is None:
            self._switch_turn_without_move_context()
            return

        next_turn = _opponent(self._position.turn)
        self._advance_move_counters()
        elapsed_ms = self._apply_clock_after_move(next_turn)
        fen_after = self._position.board.to_fen(
            next_turn,
            self._position.halfmove_clock,
            self._position.fullmove_number,
        )
        self._position.turn = next_turn
        self._update_result_after_move()
        self._stop_clock_for_finished_game()
        san = self._build_san(self.last_move_context)
        self._persist_move(fen_after, san, elapsed_ms)
        self.last_move_context = None
        if self.result is not None and self.game_id is not None:
            self._finish_game_in_storage()

    def _build_san(self, context):
        start = context["start"]
        end = context["end"]
        if context.get("is_castling", False):
            notation = self._castling_san(start, end)
        else:
            notation = self._standard_san(context)
        return f"{notation}{self._san_suffix()}"

    @staticmethod
    def _castling_san(start, end):
        return "O-O" if end[1] > start[1] else "O-O-O"

    def _standard_san(self, context):
        start = context["start"]
        piece_symbol = context["piece"]
        destination = _coords_to_square(context["end"])
        capture_marker = "x" if context["is_capture"] else ""
        piece_part = self._san_piece_part(context, start, piece_symbol)
        promotion = context["promotion"]
        notation = f"{piece_part}{capture_marker}{destination}"
        if promotion is not None:
            notation += f"={promotion}"
        return notation

    def _san_piece_part(self, context, start, piece_symbol):
        if piece_symbol == "P":
            return _coords_to_square(start)[0] if context["is_capture"] else ""

        disambiguation = self._san_disambiguation_for_context(context)
        return f"{piece_symbol}{disambiguation}"

    def _san_disambiguation_for_context(self, context):
        board_before = context.get("board_before")
        color = context.get("piece_color")
        if board_before is None or color is None:
            return ""

        return self._san_disambiguation(
            board_before=board_before,
            color=color,
            piece_symbol=context["piece"],
            start=context["start"],
            end=context["end"],
        )

    def _san_suffix(self):
        if self.result is not None and self.result.get("type") == "checkmate":
            return "#"
        if self.board.is_king_in_check(self.turn):
            return "+"
        return ""

    def _record_current_position(self):
        key = self.board.repetition_key(self.turn)
        self.board.position_counts[key] = self.board.position_counts.get(key, 0) + 1

    def _san_disambiguation(self, *, board_before, color, piece_symbol, start, end):
        candidates = []
        for row in range(8):
            for col in range(8):
                if (row, col) == start:
                    continue
                piece = board_before.get_piece(row, col)
                if piece is None or piece.color != color or piece.symbol != piece_symbol:
                    continue
                if not self._is_move_legal_on_board(board_before, (row, col), end, color):
                    continue
                candidates.append((row, col))
        if not candidates:
            return ""
        same_file = any(candidate[1] == start[1] for candidate in candidates)
        same_rank = any(candidate[0] == start[0] for candidate in candidates)
        start_square = _coords_to_square(start)
        file_char = start_square[0]
        rank_char = start_square[1]
        if not same_file:
            return file_char
        if not same_rank:
            return rank_char
        return f"{file_char}{rank_char}"

    def _has_any_legal_move(self, color):
        for start, moves in self._iter_piece_moves(color):
            for move in moves:
                if self.is_move_legal(start, move, color):
                    return True
        return False

    def _iter_piece_moves(self, color):
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece is None or piece.color != color:
                    continue
                start = (row, col)
                yield start, piece.get_moves(start, self.board)

    def is_current_turn_in_check(self):
        """Return whether the side to move is currently in check."""
        return self.board.is_king_in_check(self.turn)

    def winner(self):
        """Return the winning side code, or ``None`` for draws and live games."""
        if self.result is None:
            return None
        return self.result.get("winner")

    def _update_turn_state(self):
        if self._has_insufficient_material():
            self.result = {"type": "insufficient_material"}
            return
        in_check = self.board.is_king_in_check(self.turn)
        if self._has_any_legal_move(self.turn):
            self.result = None
            return
        if in_check:
            self.result = {
                "type": "checkmate",
                "winner": _opponent(self.turn),
            }
            return
        self.result = {"type": "stalemate"}

    def _has_insufficient_material(self):
        non_king_pieces = []
        bishops = []
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece is None or isinstance(piece, King):
                    continue
                non_king_pieces.append(piece)
                if isinstance(piece, Bishop):
                    bishops.append((row, col))
        if not non_king_pieces:
            return True
        if len(non_king_pieces) == 1:
            return isinstance(non_king_pieces[0], (Bishop, Knight))
        if len(non_king_pieces) == 2 and all(
            isinstance(piece, Bishop) for piece in non_king_pieces
        ):
            return (bishops[0][0] + bishops[0][1]) % 2 == (bishops[1][0] + bishops[1][1]) % 2
        return False

    def pause_clock(self):
        """Pause the clock, persist time, and finish the game on timeout."""
        if self.clock_state is None:
            return
        pause_result = self.clock_state.pause()
        self._sync_clock_times()
        if self.game_id is not None:
            self.storage_service.update_game_clock(
                self.game_id,
                white_time_ms=self.white_time_ms,
                black_time_ms=self.black_time_ms,
            )
        if pause_result.get("timed_out"):
            loser = pause_result["loser"]
            self.result = {
                "type": "timeout",
                "winner": _opponent(loser),
            }
            if self.game_id is not None:
                self._finish_game_in_storage()

    def resume_clock(self):
        """Resume the current side's clock when the game is active."""
        if self.clock_state is None or self.result is not None:
            return
        self.clock_state.start(self.turn)

    def handle_clock_tick(self):
        """Process timeout detection for the running clock.

        Returns:
            bool: ``True`` if the tick ended the game on time, else ``False``.
        """
        if self.clock_state is None or self.result is not None:
            return False
        loser = self.clock_state.check_timeout()
        if loser is None:
            return False
        self._sync_clock_times()
        self.result = {
            "type": "timeout",
            "winner": _opponent(loser),
        }
        if self.game_id is not None:
            self.storage_service.update_game_clock(
                self.game_id,
                white_time_ms=self.white_time_ms,
                black_time_ms=self.black_time_ms,
            )
            self._finish_game_in_storage()
        return True

    def get_clock_display(self):
        """Return display-ready remaining times for both sides.

        Returns:
            dict[str, int] | None: Remaining milliseconds for white and black,
                or ``None`` for untimed games.
        """
        if self.clock_state is None:
            return None
        return {
            "w": self.clock_state.get_display_remaining_ms("w"),
            "b": self.clock_state.get_display_remaining_ms("b"),
        }

    def _finish_game_in_storage(self):
        final_fen = self.board.to_fen(self.turn, self.halfmove_clock, self.fullmove_number)
        self.storage_service.finish_game(
            self.game_id,
            result_type=self.result["type"],
            winner=self.result.get("winner"),
            final_fen=final_fen,
        )

    def _switch_turn_without_move_context(self):
        self._position.turn = _opponent(self._position.turn)
        self._update_turn_state()
        if self.clock_state is not None and self.result is None:
            self.clock_state.start(self._position.turn)

    def _advance_move_counters(self):
        if self.last_move_context["is_pawn_move"] or self.last_move_context["is_capture"]:
            self._position.halfmove_clock = 0
        else:
            self._position.halfmove_clock += 1
        if self._position.turn == "b":
            self._position.fullmove_number += 1

    def _apply_clock_after_move(self, next_turn):
        if self.clock_state is None:
            return None

        clock_result = self.clock_state.apply_move(next_turn)
        self._clock.white_time_ms = clock_result["white_time_ms"]
        self._clock.black_time_ms = clock_result["black_time_ms"]
        if clock_result["timed_out"]:
            loser = clock_result["loser"]
            self.result = {
                "type": "timeout",
                "winner": _opponent(loser),
            }
        return clock_result["elapsed_ms"]

    def _update_result_after_move(self):
        if self.result is not None:
            return

        self._record_current_position()
        self._update_turn_state()
        if self.result is not None:
            return

        repetition_key = self.board.repetition_key(self.turn)
        repetition_count = self.board.position_counts.get(repetition_key, 0)
        if self._position.halfmove_clock >= 100:
            self.result = {"type": "fifty_move_rule"}
        elif repetition_count >= 3:
            self.result = {"type": "threefold_repetition"}

    def _stop_clock_for_finished_game(self):
        if self.clock_state is None or self.result is None:
            return
        if self.result.get("type") == "timeout":
            return
        self.clock_state.running = False
        self.clock_state.last_started_at_ms = None
        self._sync_clock_times()

    def _persist_move(self, fen_after, san, elapsed_ms):
        if self.game_id is None:
            return

        move_data = {
            "start": self.last_move_context["start"],
            "end": self.last_move_context["end"],
            "piece": self.last_move_context["piece"],
            "fen_after": fen_after,
            "promotion": self.last_move_context["promotion"],
            "san": san,
            "white_time_ms": self.white_time_ms,
            "black_time_ms": self.black_time_ms,
            "elapsed_ms": elapsed_ms,
        }
        self.storage_service.save_move(self.game_id, **move_data)
        if self.clock_state is not None:
            self.storage_service.update_game_clock(
                self.game_id,
                white_time_ms=self.white_time_ms,
                black_time_ms=self.black_time_ms,
            )

    def _sync_clock_times(self):
        if self.clock_state is None:
            return
        self._clock.white_time_ms = self.clock_state.remaining_ms["w"]
        self._clock.black_time_ms = self.clock_state.remaining_ms["b"]
