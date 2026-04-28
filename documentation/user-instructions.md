# User Instructions

Download the latest source code of the project from the repository and open it in your terminal.

## Installation and Setup

Before starting the application, install dependencies in the project root:

```bash
poetry install
```

The application uses an SQLite database at `data/chess.db` for storing game and move history. The database schema is created automatically when the app starts.

If you want to initialize the database manually, run:

```bash
poetry run python3 src/init_db.py
```

Now start the application:

```bash
poetry run invoke start
```

## How the App Works

The app is a local two-player chess game played on the same computer.

### Starting a Game

When the app opens, a new chess game starts with the standard initial position. White moves first.

### Moving Pieces

1. Click one of your own pieces.
2. Legal destination squares are highlighted.
3. Click a highlighted square to make the move.

If you click the selected piece again, the selection is cancelled.

### Game End and Controls

- On checkmate, the app shows the winner.
- On stalemate, the app shows a draw result.
- Press `Restart` to begin a new game.
- Press `Quit` to close the application.
