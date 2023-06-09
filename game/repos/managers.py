from typing import List, Optional


class PlayMixin:
    """Mixin for playing the game."""

    def set_field(self, row: int, col: int, symbol: str) -> None:
        raise NotImplementedError

    def get_field(self, row: int, col: int) -> Optional[str]:
        raise NotImplementedError

    def make_move(self, col: int, row: int, symbol: str) -> None:
        """Make a move on the game board."""
        self.set_field(row, col, symbol)

    def find_free_spots(self) -> List[tuple[int, int]]:
        """Find all free spots on the board."""
        free_spots: List = []
        for row in range(3):
            for col in range(3):
                if not self.get_field(row, col):
                    free_spots.append((row, col))
        return free_spots

    def check_game_state(self):
        """
        Check if the game has ended in a draw. Returns True if the game has ended, and
        the winner if there is one.
        """
        for element in range(3):
            # Checking rows
            actual_row: List[str | None] = [
                self.get_field(element, x_row) for x_row in range(3)
            ]

            if len(set(actual_row)) == 1 and actual_row[0]:
                return True, actual_row[0]

            # checking columns
            actual_column: List[str | None] = [
                self.get_field(x_col, element) for x_col in range(3)
            ]

            if len(set(actual_column)) == 1 and actual_column[0]:
                return True, actual_column[0]
        # checking diagonals
        diagonal_1: List[str | None] = [self.get_field(num, num) for num in range(3)]
        diagonal_2: List[str | None] = [
            self.get_field(num, 2 - num) for num in range(3)
        ]

        if len(set(diagonal_1)) == 1 and diagonal_1[0]:
            return True, diagonal_1[0]
        if len(set(diagonal_2)) == 1 and diagonal_2[0]:
            return True, diagonal_2[0]

        # checking if there is a free spot
        if not self.find_free_spots():
            return True, None

        return False, None


class GridManager(PlayMixin):
    """Class for managing the game board."""

    def __init__(self, fields: List[List[None]]):
        self._fields: List[List[None]] = fields

    def get_board(self) -> List[List[Optional[str]]]:
        """Return the game board."""
        return self._fields

    @staticmethod
    def initialize_grid() -> List[List[None]]:
        """Initialize the game board."""
        return [[None, None, None] for _ in range(3)]

    def is_move_possible(self, row: int, col: int) -> bool:
        """Check if a move is possible on the game board."""
        field: str | None = self.get_field(row, col)
        if field:
            return False
        return True

    def set_field(self, row, col, value):
        """Set a field on the game board."""
        self._fields[col][row] = value

    def get_field(self, row, col) -> str | None:
        """Get a field from the game board."""
        return self._fields[row][col]
