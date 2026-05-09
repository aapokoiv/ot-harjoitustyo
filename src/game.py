from board import Board
from clock import ClockState
from fen import parse_fen
from piece import Bishop, King, Knight, Pawn
from service import MoveStorageService

def _opponent(color: str):
    return "b" if color == "w" else "w"

def _coords_to_square(coords: tuple[int, int]):
    row, col = coords
    file_char = chr(ord("a") + col)
    rank_char = str(8 - row)
    return f"{file_char}{rank_char}"

class Game:
    def __init__(
        self,
        storage_service=None,
        *,
        game_id: int | None = None,
        initial_fen: str | None = None,
        clock_enabled: bool = False,
        initial_seconds: int | None = None,
        increment_seconds: int = 0,
        white_time_ms: int | None = None,
        black_time_ms: int | None = None,
        create_storage_row: bool = True,
    ):
        self.storage_service = storage_service or MoveStorageService()
        self.result = None
        self.last_move_context = None
        if initial_fen is None:
            self.board = Board()
            self.turn = "w"
            self.halfmove_clock = 0
            self.fullmove_number = 1
            self.board.set_starting_position()
        else:
            fen_state = parse_fen(initial_fen, Board)
            self.board = fen_state["board"]
            self.turn = fen_state["side_to_move"]
            self.halfmove_clock = fen_state["halfmove_clock"]
            self.fullmove_number = fen_state["fullmove_number"]
        self.clock_enabled = bool(clock_enabled)
        self.initial_seconds = initial_seconds
        self.increment_seconds = increment_seconds
        self.clock_state = None
        self.white_time_ms = white_time_ms
        self.black_time_ms = black_time_ms
        if self.clock_enabled:
            clock_base_seconds = int(initial_seconds or 0)
            self.clock_state = ClockState(
                initial_seconds=clock_base_seconds,
                increment_seconds=increment_seconds,
            )
            if white_time_ms is not None and black_time_ms is not None:
                self.clock_state.set_remaining(
                    white_time_ms=white_time_ms,
                    black_time_ms=black_time_ms,
                )
            self.white_time_ms = self.clock_state.remaining_ms["w"]
            self.black_time_ms = self.clock_state.remaining_ms["b"]
        self.game_id = game_id
        if self.game_id is None and create_storage_row:
            initial_fen_for_storage = self.board.to_fen(
                self.turn,
                self.halfmove_clock,
                self.fullmove_number,
            )
            if self.clock_enabled:
                self.game_id = self.storage_service.start_game(
                    initial_fen_for_storage,
                    clock_enabled=self.clock_enabled,
                    initial_seconds=self.initial_seconds,
                    increment_seconds=self.increment_seconds,
                    white_time_ms=self.white_time_ms,
                    black_time_ms=self.black_time_ms,
                )
            else:
                self.game_id = self.storage_service.start_game(initial_fen_for_storage)
        self._record_current_position()
        self._update_turn_state()
        if self.clock_state is not None and self.result is None:
            self.clock_state.start(self.turn)

    @classmethod
    def load_existing(cls, game_id: int, storage_service=None):
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
            clock_enabled=bool(game_row.get("clock_enabled", 0)),
            initial_seconds=game_row.get("initial_seconds"),
            increment_seconds=int(game_row.get("increment_seconds") or 0),
            white_time_ms=game_row.get("white_time_ms"),
            black_time_ms=game_row.get("black_time_ms"),
            create_storage_row=False,
        )
        position_fens = [game_row["initial_fen"]]
        position_fens.extend(move["fen_after"] for move in moves)
        game._restore_position_history(position_fens)
        return game

    def _restore_position_history(self, position_fens):
        self.board.position_counts = {}
        for fen in position_fens:
            fen_state = parse_fen(fen, Board)
            board = fen_state["board"]
            side_to_move = fen_state["side_to_move"]
            key = board.repetition_key(side_to_move)
            self.board.position_counts[key] = self.board.position_counts.get(key, 0) + 1

    def make_move(self, start, end):
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
        if self.last_move_context is None:
            self.turn = _opponent(self.turn)
            self._update_turn_state()
            if self.clock_state is not None and self.result is None:
                self.clock_state.start(self.turn)
            return
        next_turn = _opponent(self.turn)
        if self.last_move_context["is_pawn_move"] or self.last_move_context["is_capture"]:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        if self.turn == "b":
            self.fullmove_number += 1
        elapsed_ms = None
        if self.clock_state is not None:
            clock_result = self.clock_state.apply_move(next_turn)
            elapsed_ms = clock_result["elapsed_ms"]
            self.white_time_ms = clock_result["white_time_ms"]
            self.black_time_ms = clock_result["black_time_ms"]
            if clock_result["timed_out"]:
                loser = clock_result["loser"]
                self.result = {
                    "type": "timeout",
                    "winner": _opponent(loser),
                }
        fen_after = self.board.to_fen(next_turn, self.halfmove_clock, self.fullmove_number)
        self.turn = next_turn
        if self.result is None:
            self._record_current_position()
            self._update_turn_state()
        if self.result is None:
            repetition_key = self.board.repetition_key(self.turn)
            repetition_count = self.board.position_counts.get(repetition_key, 0)
            if self.halfmove_clock >= 100:
                self.result = {"type": "fifty_move_rule"}
            elif repetition_count >= 3:
                self.result = {"type": "threefold_repetition"}
        san = self._build_san(self.last_move_context)
        if self.game_id is not None:
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
        self.last_move_context = None
        if self.result is not None and self.game_id is not None:
            self._finish_game_in_storage()

    def _build_san(self, context):
        start = context["start"]
        end = context["end"]
        piece_symbol = context["piece"]
        is_capture = context["is_capture"]
        promotion = context["promotion"]
        board_before = context.get("board_before")
        color = context.get("piece_color")
        if context.get("is_castling", False):
            notation = "O-O" if end[1] > start[1] else "O-O-O"
        else:
            destination = _coords_to_square(end)
            piece_part = ""
            capture_marker = "x" if is_capture else ""
            if piece_symbol == "P":
                if is_capture:
                    piece_part = _coords_to_square(start)[0]
            else:
                piece_part = piece_symbol
                disambiguation = ""
                if board_before is not None and color is not None:
                    disambiguation = self._san_disambiguation(
                        board_before=board_before,
                        color=color,
                        piece_symbol=piece_symbol,
                        start=start,
                        end=end,
                    )
                piece_part += disambiguation
            notation = f"{piece_part}{capture_marker}{destination}"
            if promotion is not None:
                notation += f"={promotion}"
        is_checkmate = self.result is not None and self.result.get("type") == "checkmate"
        if is_checkmate:
            notation += "#"
        elif self.board.is_king_in_check(self.turn):
            notation += "+"
        return notation

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
        return self.board.is_king_in_check(self.turn)

    def winner(self):
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
        if self.clock_state is None:
            return
        pause_result = self.clock_state.pause()
        self.white_time_ms = self.clock_state.remaining_ms["w"]
        self.black_time_ms = self.clock_state.remaining_ms["b"]
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
        if self.clock_state is None or self.result is not None:
            return
        self.clock_state.start(self.turn)

    def handle_clock_tick(self):
        if self.clock_state is None or self.result is not None:
            return False
        loser = self.clock_state.check_timeout()
        if loser is None:
            return False
        self.white_time_ms = self.clock_state.remaining_ms["w"]
        self.black_time_ms = self.clock_state.remaining_ms["b"]
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


class GameReview:
    def __init__(self, *, game_row, snapshots):
        if game_row.get("status") != "finished":
            raise ValueError(f"Game {game_row['id']} is not finished and cannot be reviewed")
        if not snapshots:
            raise ValueError(f"No snapshots found for game {game_row['id']}")
        self.game_id = game_row["id"]
        self.clock_enabled = False
        self.clock_state = None
        self.initial_seconds = None
        self.increment_seconds = 0
        self.white_time_ms = None
        self.black_time_ms = None
        self.last_move_context = None
        self.snapshots = snapshots
        self.current_index = len(snapshots) - 1
        self.result = None
        self._load_snapshot(self.current_index)
        result_type = game_row.get("result_type")
        if result_type:
            self.result = {"type": result_type}
            winner = game_row.get("winner")
            if winner is not None:
                self.result["winner"] = winner

    @classmethod
    def load_finished(cls, game_id: int, storage_service=None):
        service = storage_service or MoveStorageService()
        game_row = service.get_game(game_id)
        if game_row is None:
            raise ValueError(f"Game with id {game_id} not found")
        if game_row.get("status") != "finished":
            raise ValueError(f"Game {game_id} is ongoing and must be resumed in play mode")
        snapshots = [game_row["initial_fen"]]
        snapshots.extend(move["fen_after"] for move in service.get_moves(game_id))
        return cls(game_row=game_row, snapshots=snapshots)

    def _load_snapshot(self, index: int):
        fen_state = parse_fen(self.snapshots[index], Board)
        self.board = fen_state["board"]
        self.turn = fen_state["side_to_move"]
        self.halfmove_clock = fen_state["halfmove_clock"]
        self.fullmove_number = fen_state["fullmove_number"]

    def go_to_start(self):
        self.current_index = 0
        self._load_snapshot(self.current_index)

    def go_to_end(self):
        self.current_index = len(self.snapshots) - 1
        self._load_snapshot(self.current_index)

    def can_go_backward(self):
        return self.current_index > 0

    def can_go_forward(self):
        return self.current_index < len(self.snapshots) - 1

    def previous_position(self):
        if not self.can_go_backward():
            return False
        self.current_index -= 1
        self._load_snapshot(self.current_index)
        return True

    def next_position(self):
        if not self.can_go_forward():
            return False
        self.current_index += 1
        self._load_snapshot(self.current_index)
        return True

    def click_board(self, row, col):
        return self.board.get_piece(row, col), []

    def make_move(self, _start, _end):
        return False

    def complete_promotion(self, _piece_type):
        return False

    def is_move_legal(self, _start, _end, _color):
        return False

    def is_current_turn_in_check(self):
        return self.board.is_king_in_check(self.turn)

    def winner(self):
        if self.result is None:
            return None
        return self.result.get("winner")

    def pause_clock(self):
        return

    def resume_clock(self):
        return

    def handle_clock_tick(self):
        return False

    def get_clock_display(self):
        return None
