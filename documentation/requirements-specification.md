# Requirements specification

## Application description
With this application you can play 2-player chess locally on the same computer. 
The application will include a graphical chess board.

## Users
For the start there is a plan to have only one type of user. Might consider adding
an option for signing in at some point.

## Core features
### The player can
- Start a new game
- See a visual chess board 
  - The state of the game is updated visually every move
  - Player can move a piece by clicking it and a square the piece can move to

### The application will
- Validate played moves
  - The app will block illegal moves 
  - Illegal move will result in a notification and the game continuing
- Recognize when the game ends either in checkmate or stalemate
- Manage turns between white and black


## Future feature ideas
- Chess clocks for both sides
  - Players can choose different time constraints for a game
- GUI shows legal moves when clicking a piece
- GUI shows list of played moves
  - Player can review previous positions through the list
- Players can configure custom chess position and play from there 
- Sound effects
  - Check 
  - Illegal move
  - Moving a piece
- Game history
  - Full move history
  - Ability to review played games
- Stockfish
  - Game evaluation
  - Playing against a local bot

