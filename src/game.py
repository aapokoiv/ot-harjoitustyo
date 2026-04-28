from board import Board
from piece import Pawn, King
from service import MoveStorageService

class Game:
    """Manages the game coordinating board state and move persistence.

    The Game class owns a :class:`Board` and enforces move legality, turn
    progression, and persistence of moves via a MoveStorageService.
    """

    def __init__(self, storage_service=MoveStorageService()):
        """Create a new game instance.

        Args:
            storage_service (MoveStorageService): Service used to persist game
                start, moves and final result. A default instance is created
                when omitted.
        """
        self.board = Board()
        self.turn = "w"
        self.result = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.last_move_context = None
        self.board.set_starting_position()
        self.storage_service = storage_service

        initial_fen = self.board.to_fen(self.turn, self.halfmove_clock, self.fullmove_number)
        self.game_id = self.storage_service.start_game(initial_fen)
        self._update_turn_state()

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

        if not self.is_move_legal(start, end, self.turn):
            return False

        piece = self.board.get_piece(start[0], start[1])

        target_piece = self.board.get_piece(end[0], end[1])
        is_capture = target_piece is not None
        if isinstance(piece, Pawn) and end == self.board.en_passant_target:
            is_capture = True

        self.board.move_piece(start, end)

        self.last_move_context = {
            "start": start,
            "end": end,
            "piece": piece.symbol,
            "promotion": None,
            "is_pawn_move": isinstance(piece, Pawn),
            "is_capture": is_capture,
        }

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

        piece = self.board.get_piece(start[0], start[1])
        if piece is None or piece.color != color:
            return False

        moves = piece.get_moves(start, self.board)
        if end not in moves:
            return False

        target_piece = self.board.get_piece(end[0], end[1])
        if isinstance(target_piece, King):
            return False

        if self._is_castling_move(piece, start, end):
            opponent_color = "b" if color == "w" else "w"
            col_between = start[1] + (1 if end[1] > start[1] else -1)

            if (self.board.is_square_attacked(start[0], start[1], opponent_color)
                or self.board.is_square_attacked(start[0], col_between, opponent_color)
                or self.board.is_square_attacked(start[0], end[1], opponent_color)):
                return False

        board = self.board.clone()
        board.move_piece(start, end)
        return not board.is_king_in_check(color)

    def _is_castling_move(self, piece, start, end):
        return isinstance(piece, King) and start[0] == end[0] and abs(start[1] - end[1]) == 2

    def switch_turn(self):
        """Advance the game to the next player's turn.

        If there is a recorded last move context, this method updates the
        halfmove clock, fullmove number, persists the move via the storage
        service, and updates check/checkmate/stalemate state. When called with
        no context it simply flips the active player.
        """

        if self.last_move_context is None:
            self.turn = "b" if self.turn == "w" else "w"
            self._update_turn_state()
            return

        next_turn = "b" if self.turn == "w" else "w"

        if self.last_move_context["is_pawn_move"] or self.last_move_context["is_capture"]:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if self.turn == "b":
            self.fullmove_number += 1

        fen_after = self.board.to_fen(next_turn, self.halfmove_clock, self.fullmove_number)

        self.storage_service.save_move(
            self.game_id,
            start=self.last_move_context["start"],
            end=self.last_move_context["end"],
            piece=self.last_move_context["piece"],
            fen_after=fen_after,
            promotion=self.last_move_context["promotion"],
        )

        self.turn = next_turn
        self.last_move_context = None
        self._update_turn_state()

        if self.result is not None:
            final_fen = self.board.to_fen(self.turn, self.halfmove_clock, self.fullmove_number)
            self.storage_service.finish_game(
                self.game_id,
                result_type=self.result["type"],
                winner=self.result.get("winner"),
                final_fen=final_fen,
            )

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
        """Return the winner of the game if the game is finished.

        Returns:
            str | None: 'w' or 'b' if there is a winner, otherwise None.
        """
        if self.result is None:
            return None
        return self.result.get("winner")

    def _update_turn_state(self):
        in_check = self.board.is_king_in_check(self.turn)

        if self._has_any_legal_move(self.turn):
            self.result = None
            return

        if in_check:
            self.result = {
                "type": "checkmate",
                "winner": "b" if self.turn == "w" else "w",
            }
            return

        self.result = {"type": "stalemate"}
