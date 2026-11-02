from board import Board
from rules import valid_move, completed_boxes


class DotsAndBoxes:
    def __init__(self, rows=2, cols=2):
        self.board = Board(rows, cols)
        self.current = 0
        self.scores = [0, 0]

    def play_move(self, orientation, row, col):
        """
        Apply a move safely.

        Return True if the move was accepted, otherwise False.
        Invalid moves never change scores or the current player.
        """
        if self.board.is_complete():
            return False

        if not valid_move(self.board, orientation, row, col):
            return False

        before = set(self.board.completed)

        if not self.board.add_line(orientation, row, col):
            return False

        newly_completed = completed_boxes(self.board, before)

        if newly_completed:
            new_boxes = self.board.completed - before
            self.board.claim_boxes(new_boxes, self.current)
            self.scores[self.current] += newly_completed
        else:
            self.current = 1 - self.current

        return True

    def run(self):
        print("Dots and Boxes")
        print(
            f"Board size: {self.board.rows} rows x "
            f"{self.board.cols} columns"
        )
        print("Enter moves as H row col or V row col.")
        print("Rows and columns start at 0.")
        print("Example: H 0 1")
        print("Press Ctrl-D (Unix/macOS) or Ctrl-Z then Enter (Windows) to quit.")

        while not self.board.is_complete():
            self.board.display(self.scores, self.current)

            try:
                raw = input(
                    f"Player {self.current + 1}, move: "
                ).strip().upper()
            except EOFError:
                print("\nInput closed. Exiting game.")
                return

            parts = raw.split()

            if len(parts) != 3:
                print("Invalid format. Use H row col or V row col.")
                continue

            orientation, row_text, col_text = parts

            # Accept only non-negative decimal integers.
            if not row_text.isdecimal() or not col_text.isdecimal():
                print("Invalid coordinates. Row and column must be non-negative integers.")
                continue

            row, col = int(row_text), int(col_text)

            if not valid_move(self.board, orientation, row, col):
                if self.board.is_complete():
                    print("The game is already complete.")
                else:
                    print("Invalid or already-used move.")
                continue

            self.play_move(orientation, row, col)

        self.board.display(self.scores, self.current)
        print("Game over!")

        if self.scores[0] == self.scores[1]:
            print("The game is a draw.")
        else:
            winner = 1 if self.scores[0] > self.scores[1] else 2
            print(f"Player {winner} wins!")

        print(f"Player 1 claimed {self.scores[0]} box(es).")
        print(f"Player 2 claimed {self.scores[1]} box(es).")
