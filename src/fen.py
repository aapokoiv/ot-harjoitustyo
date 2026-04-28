"""FEN to board state and back conversion

This module converts between the internal board representation and
Forsyth-Edwards Notation (FEN)
"""

from piece import Pawn, Knight, Bishop, Rook, Queen, King

### The code in this file is mostly done with ai
### AI code starting
PIECE_TO_FEN = {
    Pawn: "p",
    Knight: "n",
    Bishop: "b",
    Rook: "r",
    Queen: "q",
    King: "k",
}

FEN_TO_PIECE = {
    "p": Pawn,
    "n": Knight,
    "b": Bishop,
    "r": Rook,
    "q": Queen,
    "k": King,
}


def board_to_fen(board, side_to_move, halfmove_clock=0, fullmove_number=1):
    """Convert a Board instance into a FEN string.

    Args:
        board: Board-like object with a grid, en_passant_target and piece
        instances compatible with the PIECE_TO_FEN mapping.
        side_to_move (str): 'w' or 'b' indicating which side is to move.
        halfmove_clock (int): Fifty-move rule counter.
        fullmove_number (int): Full move counter.

    Returns:
        str: FEN formatted string representing the board state.

    Raises:
        ValueError: If side_to_move is not 'w' or 'b'.
    """
    ranks = []
    for row in board.grid:
        empty_count = 0
        rank_parts = []
        for piece in row:
            if piece is None:
                empty_count += 1
                continue

            if empty_count:
                rank_parts.append(str(empty_count))
                empty_count = 0

            fen_symbol = PIECE_TO_FEN[type(piece)]
            rank_parts.append(fen_symbol.upper() if piece.color == "w" else fen_symbol)

        if empty_count:
            rank_parts.append(str(empty_count))

        ranks.append("".join(rank_parts))

    if side_to_move not in {"w", "b"}:
        raise ValueError("side_to_move must be 'w' or 'b'")

    castling = _get_castling_rights(board)
    en_passant = _coords_to_algebraic(board.en_passant_target)

    return (
        f"{'/'.join(ranks)} {side_to_move} {castling} "
        f"{en_passant} {halfmove_clock} {fullmove_number}"
    )


def board_from_fen(
    fen,
    board_cls,
    board_rows=8,
    board_cols=8,
):
    """Create a Board instance from a FEN string.

    Args:
        fen (str): FEN string with six fields (piece placement, active color,
        castling availability, en-passant square, halfmove clock, fullmove number).
        board_cls: Board class to instantiate for the parsed board.
        board_rows (int): Number of rows expected (default 8).
        board_cols (int): Number of columns expected (default 8).

    Returns:
        board_cls: An instance of board_cls representing the FEN state.

    Raises:
        ValueError: If the FEN string is malformed.
    """
    parts = fen.strip().split()
    if len(parts) != 6:
        raise ValueError("Invalid FEN: expected 6 fields")

    placement = parts[0]
    castling = parts[2]
    en_passant = parts[3]

    ranks = placement.split("/")
    if len(ranks) != 8:
        raise ValueError("Invalid FEN: expected 8 ranks")

    board = board_cls()
    board.grid = [[None for _ in range(board_cols)] for _ in range(board_rows)]

    for row_idx, rank in enumerate(ranks):
        _populate_board_row(board.grid[row_idx], rank)

    board.en_passant_target = None if en_passant == "-" else _algebraic_to_coords(en_passant)
    board.pending_promotion = None
    _apply_castling_rights(board, castling)
    return board


def _populate_board_row(board_row, rank):
    col_idx = 0

    for char in rank:
        if char.isdigit():
            col_idx += int(char)
            continue

        board_row[col_idx] = _piece_from_fen_symbol(char)
        col_idx += 1

    if col_idx != 8:
        raise ValueError("Invalid FEN: rank does not contain 8 files")


def _piece_from_fen_symbol(char):
    piece_class = FEN_TO_PIECE.get(char.lower())
    if piece_class is None:
        raise ValueError("Invalid FEN: unknown piece symbol")

    piece_color = "w" if char.isupper() else "b"
    piece = piece_class(piece_color)

    if isinstance(piece, (King, Rook)):
        piece.has_moved = True

    return piece


def _get_castling_rights(board):
    rights = []

    white_king = board.get_piece(7, 4)
    if isinstance(white_king, King) and white_king.color == "w" and not white_king.has_moved:
        white_kingside_rook = board.get_piece(7, 7)
        white_queenside_rook = board.get_piece(7, 0)

        if (
            isinstance(white_kingside_rook, Rook)
            and white_kingside_rook.color == "w"
            and not white_kingside_rook.has_moved
        ):
            rights.append("K")
        if (
            isinstance(white_queenside_rook, Rook)
            and white_queenside_rook.color == "w"
            and not white_queenside_rook.has_moved
        ):
            rights.append("Q")

    black_king = board.get_piece(0, 4)
    if isinstance(black_king, King) and black_king.color == "b" and not black_king.has_moved:
        black_kingside_rook = board.get_piece(0, 7)
        black_queenside_rook = board.get_piece(0, 0)

        if (
            isinstance(black_kingside_rook, Rook)
            and black_kingside_rook.color == "b"
            and not black_kingside_rook.has_moved
        ):
            rights.append("k")
        if (
            isinstance(black_queenside_rook, Rook)
            and black_queenside_rook.color == "b"
            and not black_queenside_rook.has_moved
        ):
            rights.append("q")

    return "".join(rights) if rights else "-"


def _apply_castling_rights(board, castling_rights):
    white_king = board.get_piece(7, 4)
    if isinstance(white_king, King) and white_king.color == "w":
        white_king.has_moved = not ("K" in castling_rights or "Q" in castling_rights)

    black_king = board.get_piece(0, 4)
    if isinstance(black_king, King) and black_king.color == "b":
        black_king.has_moved = not ("k" in castling_rights or "q" in castling_rights)

    white_rook_k = board.get_piece(7, 7)
    if isinstance(white_rook_k, Rook) and white_rook_k.color == "w":
        white_rook_k.has_moved = "K" not in castling_rights

    white_rook_q = board.get_piece(7, 0)
    if isinstance(white_rook_q, Rook) and white_rook_q.color == "w":
        white_rook_q.has_moved = "Q" not in castling_rights

    black_rook_k = board.get_piece(0, 7)
    if isinstance(black_rook_k, Rook) and black_rook_k.color == "b":
        black_rook_k.has_moved = "k" not in castling_rights

    black_rook_q = board.get_piece(0, 0)
    if isinstance(black_rook_q, Rook) and black_rook_q.color == "b":
        black_rook_q.has_moved = "q" not in castling_rights


def _coords_to_algebraic(coords):
    if coords is None:
        return "-"
    row, col = coords
    file_char = chr(ord("a") + col)
    rank_char = str(8 - row)
    return f"{file_char}{rank_char}"


def _algebraic_to_coords(square):
    if len(square) != 2:
        raise ValueError("Invalid en-passant target in FEN")

    file_char, rank_char = square[0], square[1]
    if file_char < "a" or file_char > "h" or rank_char < "1" or rank_char > "8":
        raise ValueError("Invalid en-passant target in FEN")

    col = ord(file_char) - ord("a")
    row = 8 - int(rank_char)
    return row, col
### AI code ending
