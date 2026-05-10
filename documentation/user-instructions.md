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

The app starts in a menu from which you can create a new game, review or continue previous games, view the full previously played history.

### Starting a new Game

On the left in the main menu you can create a new game. You can select if you want to have a chess clock with whatever time amount and possible time increment.
The game works like normal chess, the game clocks pause if you exit the game.

### Game history

On the main menu you can see the last previous games. You can continue playing non-finished games and review all games.
You can also move to the history page from which you can see all games.

### Moving Pieces

1. Click one of your own pieces.
2. Legal destination squares are highlighted.
3. Click a highlighted square to make the move.

If you click the selected piece again or click a non-highlighted square, the selection is cancelled.

### Game End and Controls

- On checkmate, the app shows the winner.
- On stalemate, the app shows a draw result.
- Press `Quit` in any place to close the application.
