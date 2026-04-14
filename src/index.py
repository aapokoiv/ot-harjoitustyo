from game import Game

def print_board(board):
    for row in board.grid:
        print(" ".join(str(piece) if piece else "--" for piece in row))

def main():
    game = Game()

    print("Commands:")
    print("  t row col             -> show piece and moves")
    print("  m row1 col1 row2 col2 -> move piece")
    print("  q                     -> quit\n")

    while True:
        print_board(game.board)
        print(f"Turn: {game.turn}")

        command = input("> ").strip().split()

        if not command:
            continue

        if command[0] == "q":
            break

        elif command[0] == "t":
            row, col = int(command[1]), int(command[2])
            piece, moves = game.click_board(row, col)

            print(f"{str(piece) if piece else 'None'},  Moves: {moves}")

        elif command[0] == "m":
            if not game.make_move((int(command[1]), int(command[2])), (int(command[3]), int(command[4]))):
                print("Invalid move")

if __name__ == "__main__":
    main()
