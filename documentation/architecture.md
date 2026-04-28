# Architecture

## Structure

The project currently has source files under
`src/` and responsibilities are grouped as follows:

- Presentation: `src/ui.py` (Tkinter UI, board rendering and dialogs)
- Application core: `src/game.py`, `src/board.py`, `src/piece.py`
- Persistence / services: `src/service.py`, `src/storage.py`, `src/schema.sql`
- Utilities: `src/fen.py` (FEN conversion)
- Assets: `assets/` (piece images used by the UI)

## App logic

```mermaid
classDiagram
  %% Core relationships
  Game "1" --> "1" Board
  Game "1" --> "1" MoveStorageService
  ChessUI "1" --> "1" Game
  Board "1" --> "0..32" Piece
  Board ..> FenModule : to_fen/from_fen
  MoveStorageService ..> SQLiteStorage : persists

  class Game {
    +board: Board
    +turn: str
    +result: dict|None
    +halfmove_clock: int
    +fullmove_number: int
    +last_move_context: dict|None
    +game_id: int
    +storage_service: MoveStorageService
    +make_move(start, end)
    +complete_promotion(piece_type)
    +click_board(row, col)
    +is_move_legal(start, end, color)
    +switch_turn()
    +_update_turn_state()
  }

  class Board {
    +grid
    +en_passant_target
    +pending_promotion
    +get_piece(row, col)
    +set_piece(row, col, piece)
    +move_piece(start, end)
    +handle_promotion(row, col, piece)
    +promote(piece_type)
    +clone()
    +to_fen(side, halfmove, fullmove)
    +from_fen(fen)
    +is_king_in_check(color)
  }

  class Piece {
    -color
    -symbol
    +get_moves(pos, board)
    +__str__()
  }

  class Pawn
  class Knight
  class Bishop
  class Rook {
    +has_moved: bool
  }
  class Queen
  class King {
    +has_moved: bool
  }

  Piece <|-- Pawn
  Piece <|-- Knight
  Piece <|-- Bishop
  Piece <|-- Rook
  Piece <|-- Queen
  Piece <|-- King
```

## Main Functionality ##

The following sequence diagrams describe the primary user-visible flows.

### Piece Selection and Move Highlighting

When a user clicks a square the UI asks the Game for the piece and the
legal destinations. The Game asks the piece for generated moves and then
filters them using `is_move_legal`.

```mermaid
sequenceDiagram
  actor User
  participant UI as ChessUI
  participant Game
  participant Board
  participant Piece
  User->>UI: click square (row, col)
  UI->>Game: click_board(row, col)
  Game->>Board: get_piece(row, col)
  Board-->>Game: piece or None
  Game->>Piece: if piece: piece.get_moves((row,col), board)
  Piece-->>Game: moves
  Game->>Game: filter legal moves (is_move_legal)
  Game-->>UI: (piece, legal_moves)
  UI->>UI: highlight legal targets / clear highlights
```

### Make Move and Promotion Handling

When the user clicks a highlighted destination the UI calls `make_move`.
`Board.move_piece` applies mutations and sets `pending_promotion` if a
pawn reached the last rank. If a promotion is pending the UI shows the
modal and calls `complete_promotion`. After the move is finalised the
Game asks the storage service to save the ply together with the FEN
after the move.

```mermaid
sequenceDiagram
  actor User
  participant UI as ChessUI
  participant Game
  participant Board
  participant Piece
  participant Dialog
  participant Storage as MoveStorageService
  User->>UI: click highlighted target (end)
  UI->>Game: make_move(start, end)
  Game->>Game: is_move_legal(start, end, turn)
  Game->>Board: get_piece(start)
  Board-->>Game: piece or None
  Game->>Piece: piece.get_moves(start, board)
  Piece-->>Game: moves
  Game->>Board: move_piece(start, end)
  Board-->>Game: moved - castling and enpassant handled, pending_promotion set
  Game-->>UI: move succeeded (pending_promotion?)
  Game->>Game: switch_turn() (if not pending_promotion)
  UI->>Dialog: show_promotion_dialog() (if pending_promotion)
  Dialog-->>UI: choice (e.g., "Q")
  UI->>Game: complete_promotion(choice)
  Game->>Board: promote(choice)
  Board-->>Game: promotion success
  Game->>Game: switch_turn()
  Game->>Board: to_fen(next_turn, halfmove_clock, fullmove_number)
  Board-->>Game: fen_after
  Game->>Storage: After either switch_turn: save_move(game_id, start, end, piece, fen_after, promotion)
  Storage-->>Game: saved
  Game-->>UI: promotion completed / move finalized
UI->>UI: refresh board / update turn label
```

## Persistence

Persistence is handled by `MoveStorageService` (`src/service.py`) which
wraps `SQLiteStorage` (`src/storage.py`). The default database path is
`data/chess.db` and the schema is in `src/schema.sql`. The storage model
contains two tables:

- `games` — stores initial and final FEN and result metadata,
- `moves` — stores one row per ply with move coordinates, piece,
  optional promotion and the FEN after the move.

