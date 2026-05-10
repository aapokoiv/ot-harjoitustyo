PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS games (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  initial_fen TEXT NOT NULL,
  clock_enabled INTEGER NOT NULL DEFAULT 0,
  initial_seconds INTEGER,
  increment_seconds INTEGER NOT NULL DEFAULT 0,
  white_time_ms INTEGER,
  black_time_ms INTEGER,
  status TEXT NOT NULL DEFAULT 'ongoing',
  result_type TEXT,
  winner CHAR(1),
  final_fen TEXT,
  ended_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS moves (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  ply INTEGER NOT NULL,
  from_row INTEGER NOT NULL,
  from_col INTEGER NOT NULL,
  to_row INTEGER NOT NULL,
  to_col INTEGER NOT NULL,
  piece CHAR(1) NOT NULL,
  promotion CHAR(1),
  san TEXT,
  white_time_ms INTEGER,
  black_time_ms INTEGER,
  elapsed_ms INTEGER,
  fen_after TEXT NOT NULL,
  eval_cp INTEGER,
  eval_mate INTEGER,
  eval_delta_cp INTEGER,
  analyzed_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(game_id, ply)
);

CREATE INDEX IF NOT EXISTS idx_moves_game_ply ON moves(game_id, ply);
CREATE INDEX IF NOT EXISTS idx_moves_game ON moves(game_id);
