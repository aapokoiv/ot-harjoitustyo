# Architecture

## Structure

The project uses a package structure under `src/`, where responsibilities are
split into three main areas:

- `src/ui/`
  - graphical user interface
  - view management in `ui/app.py`
  - views in `ui/views/`
  - reusable widgets and dialogs in `ui/widgets/` and `ui/dialogs/`
- `src/logic/`
  - chess rules and application logic
  - board representation, pieces, FEN handling, clocks, and game state
- `src/persistence/`
  - SQLite storage, schema creation, and persistence service used by the game
  - Stockfish engine loading, worker process execution, and analysis saving

Other relevant files are:

- `src/ui.py`, which acts as the application entry point
- `src/init_db.py`, which initializes the database manually when needed
- `src/tests/`, which contains the automated tests
- `assets/`, which contains the chess piece images used by the UI and docs images

## User interface

The graphical interface contains four main views:

- `MenuView`
- `GameView`
- `HistoryView`
- `ReviewView`

Only one view is active at a time. View creation, navigation, geometry changes,
and returning to previous views are handled by `ChessApp` in `src/ui/app.py`.

The UI is separated from the chess rules themselves. `GameView` communicates with
the `Game` object for board interaction, move validation, promotion, and clock
handling. History and review related views fetch stored game data through
`MoveStorageService`. `ReviewView` also uses `StockfishAnalysisService` to run
and cache engine analysis for finished games.

## Application logic

The main logic is centered around the `Game` class. `Game` owns the current
position, handles move validation and rule enforcement, tracks clock state,
updates game-end conditions, generates SAN notation, and persists moves through
the storage service.

The main classes and their relationships are described below.

```mermaid
classDiagram
  ChessApp --> MoveStorageService
  ChessApp --> StockfishAnalysisService
  ChessApp --> GameView
  ChessApp --> HistoryView
  ChessApp --> ReviewView
  GameView --> Game
  HistoryView --> MoveStorageService
  ReviewView --> MoveStorageService
  ReviewView --> StockfishAnalysisService
  ReviewView ..> FenModule : parse_fen

  Game --> Board
  Game --> ClockState
  Game --> MoveStorageService
  StockfishAnalysisService --> MoveStorageService
  StockfishAnalysisService --> EngineWorker
  Board --> Piece
  Board ..> FenModule : to_fen/from_fen
  MoveStorageService --> SQLiteStorage

  class Game {
    +board: Board
    +turn: str
    +result: dict|None
    +halfmove_clock: int
    +fullmove_number: int
    +game_id: int|None
    +make_move(start, end)
    +complete_promotion(piece_type)
    +click_board(row, col)
    +is_move_legal(start, end, color)
    +switch_turn()
    +pause_clock()
    +resume_clock()
    +handle_clock_tick()
  }

  class Board {
    +grid
    +en_passant_target
    +pending_promotion
    +position_counts
    +get_piece(row, col)
    +set_piece(row, col, piece)
    +move_piece(start, end)
    +promote(piece_type)
    +clone()
    +to_fen(side, halfmove, fullmove)
    +from_fen(fen)
    +repetition_key(side_to_move)
    +is_square_attacked(row, col, by_color)
    +is_king_in_check(color)
  }

  class ClockState {
    +remaining_ms
    +active_side
    +start(side)
    +pause()
    +apply_move(next_side)
    +check_timeout()
  }

  class MoveStorageService {
    +start_game(initial_fen)
    +save_move(game_id, move_data)
    +finish_game(game_id, result_type, winner, final_fen)
    +update_game_clock(game_id, white_time_ms, black_time_ms)
    +list_games(limit, include_ongoing, sort_desc)
    +get_game(game_id)
    +get_moves(game_id)
    +get_latest_snapshot(game_id)
    +game_needs_analysis(game_id)
    +save_move_analysis(move_id, eval_cp, eval_mate, eval_delta_cp)
  }

  class StockfishAnalysisService {
    +analyze_game(game_id)
  }

  class EngineWorker {
    +analyze_positions(payload)
  }

  class SQLiteStorage {
    +create_game(initial_fen)
    +store_move(game_id, move_data)
    +finish_game(game_id, result_type, winner, final_fen)
    +list_games(limit, include_ongoing, sort_desc)
    +get_game(game_id)
    +get_moves(game_id)
    +get_latest_snapshot(game_id)
  }

  class Piece {
    +color
    +symbol
    +get_moves(pos, board)
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

`Board`, `Piece`, and the FEN helpers form the lower-level chess model.
`Game` builds on top of them and represents a complete playable game.

## Persistence

Persistence is handled through `MoveStorageService` in `src/persistence/service.py`,
which wraps `SQLiteStorage` in `src/persistence/storage.py`. Finished games can
also be analyzed through `StockfishAnalysisService` in
`src/persistence/analysis_service.py`, which runs a separate worker process from
`src/persistence/engine_worker.py` and saves per-move evaluations back to the
database.

The default database path is `data/chess.db`, unless another path is given
through the `CHESS_DB_PATH` environment variable or through the `--db-path`
argument of `src/init_db.py`.

The schema is defined in `src/persistence/schema.sql`. 

The database contains two main tables:

- `games`
  - stores the initial and final FEN of a game
  - stores game result metadata
  - stores whether the game is ongoing or finished
  - stores time control and remaining clock information
- `moves`
  - stores one row per ply
  - stores move coordinates, moved piece, optional promotion, SAN notation,
    elapsed move time, the FEN snapshot after the move, and optional stored
    engine evaluation fields

This stored move history is used both for continuing unfinished games and for
reviewing finished ones.

## Main functionality

The following sequence diagrams describe the most important user-visible flows.

### Piece selection and move highlighting

When the user clicks a square in the game view, the UI asks `Game` for the piece
on that square and for its legal moves. `Game` first asks the selected piece for
candidate moves and then filters them with full legality checks.

```mermaid
sequenceDiagram
  actor User
  participant View as GameView
  participant Game
  participant Board
  participant Piece
  User->>View: click square (row, col)
  View->>Game: click_board(row, col)
  Game->>Board: get_piece(row, col)
  Board-->>Game: piece or None
  Game->>Piece: get_moves((row, col), board)
  Piece-->>Game: candidate moves
  Game->>Game: filter with is_move_legal(...)
  Game-->>View: piece, legal_moves
  View->>View: highlight legal targets or clear selection
```

### Making a move and handling promotion

When the user clicks a highlighted destination square, `GameView` asks `Game` to
make the move. The board state is updated, special move rules are handled, and
the move is persisted after it is fully finalized. If promotion is needed, the
UI asks the user for the promotion piece and completes the move only after that.

```mermaid
sequenceDiagram
  actor User
  participant View as GameView
  participant Game
  participant Board
  participant Dialog as PromotionDialog
  participant Storage as MoveStorageService
  User->>View: click highlighted target
  View->>Game: make_move(start, end)
  Game->>Game: validate move
  Game->>Board: move_piece(start, end)
  Board-->>Game: board updated, pending_promotion?
  alt Promotion pending
    Game-->>View: move accepted, promotion pending
    View->>Dialog: show()
    Dialog-->>View: chosen piece
    View->>Game: complete_promotion(choice)
    Game->>Board: promote(choice)
  end
  Game->>Game: switch_turn()
  Game->>Game: update counters, repetition state and result
  Game->>Storage: save_move(..., fen_after, san, clock data)
  Storage-->>Game: saved
  View->>Storage: get_moves(game_id)
  View->>View: refresh board, status, clocks and move list
```

### Creating a new game

When the user creates a new game from the main menu, the application creates a
new `Game` object and stores the initial game row immediately.

```mermaid
sequenceDiagram
  actor User
  participant Menu as MenuView
  participant App as ChessApp
  participant Game
  participant Storage as MoveStorageService
  User->>Menu: click "Create Game"
  Menu->>App: create_game(clock settings)
  App->>Game: Game(storage_service, clock_config)
  Game->>Storage: start_game(initial_fen, clock settings)
  Storage-->>Game: game_id
  App->>App: show_game(game)
```

### Reviewing a finished game

Finished games can be opened in review mode. The review view loads the initial
FEN and all stored move snapshots, and then reconstructs any position by parsing
the stored FEN string of the selected snapshot.

```mermaid
sequenceDiagram
  actor User
  participant History as HistoryView
  participant App as ChessApp
  participant Review as ReviewView
  participant Storage as MoveStorageService
  participant Fen as FenModule
  User->>History: click "Review"
  History->>App: open_review(game_id)
  App->>Review: create ReviewView(game_id)
  Review->>Storage: get_game(game_id)
  Review->>Storage: get_moves(game_id)
  Storage-->>Review: game row and moves
  Review->>Fen: parse_fen(snapshot_fen)
  Fen-->>Review: board state
  Review->>Review: render selected position and move list
```

## Problems / things left to improve
- The `Game` class has grown quite large and it should be refactored
  - SAN notation and turn switching and move validation could be separated
