# Requirements specification

## Application description
With this application you can play 2-player chess locally on the same computer. 
The application includes a graphical chess board and the ability to review games.

## Users
There is currently only one type of user.

## Core features
### The player can
- Start a new game :white_check_mark:
  - Select whether to have a chess clock and customize its time settings :white_check_mark:
- See a visual chess board :white_check_mark:
  - The state of the game is updated visually every move :white_check_mark:
  - Player can move a piece by clicking it and a square the piece can move to :white_check_mark:
  - GUI shows legal moves when clicking a piece :white_check_mark:
  - GUI shows list of played moves :white_check_mark:
- See full game history and review all games :white_check_mark:

### The application will
- Validate played moves :white_check_mark:
  - The app will block illegal moves :white_check_mark:
- Recognize when the game ends either in checkmate or stalemate :white_check_mark:
- Manage turns between white and black :white_check_mark:
- Save games and moves to the database

## Future feature ideas
- Player can review on-going games previous positions through the list
- Players can configure custom chess position and play from there 
- Sound effects
  - Check 
  - Moving a piece
- Stockfish
  - Game evaluation
  - Playing against a local bot

