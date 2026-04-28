PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS games (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  initial_fen TEXT NOT NULL,
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
  fen_after TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(game_id, ply)
);

CREATE INDEX IF NOT EXISTS idx_moves_game_ply ON moves(game_id, ply);
CREATE INDEX IF NOT EXISTS idx_moves_game ON moves(game_id);
