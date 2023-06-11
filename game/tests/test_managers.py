from typing import List, Tuple
from unittest.mock import patch

import pytest
from repos.managers import GridManager


def test_grid_manager_get_board_method() -> None:
    """Test if get_board method returns the game board."""
    new_board: List[List[None]] = [[None, None, None] for _ in range(3)]
    grid_manager: List[List[None]] = GridManager(new_board).get_board()

    assert grid_manager == new_board


def test_grid_manager_initialize_grid_method() -> None:
    """Test if initialize_grid method initializes the game board."""
    new_board: List[List[None]] = [[None, None, None] for _ in range(3)]
    grid_manager: List[List[None]] = GridManager.initialize_grid()

    assert grid_manager == new_board


def test_grid_manager_is_move_possible_method() -> None:
    """
    Test if is_move_possible method returns True if a move is possible.
    Check if board is full when calling the method 9 times.
    """
    new_board: List[List[None]] = [[None, None, None] for _ in range(3)]
    grid_manager: GridManager = GridManager(new_board)

    for num in range(3):
        for num2 in range(3):
            assert grid_manager.is_move_possible(num, num2) is True

    moves: int = 0

    grid_manager.set_field(0, 0, "X")
    assert grid_manager.is_move_possible(0, 0) is False
    moves += 1

    grid_manager.set_field(0, 1, "O")
    assert grid_manager.is_move_possible(0, 1) is False
    moves += 1

    grid_manager.set_field(0, 2, "X")
    assert grid_manager.is_move_possible(0, 2) is False
    moves += 1

    grid_manager.set_field(1, 0, "O")
    assert grid_manager.is_move_possible(1, 0) is False
    moves += 1

    grid_manager.set_field(1, 1, "X")
    assert grid_manager.is_move_possible(1, 1) is False
    moves += 1

    grid_manager.set_field(1, 2, "O")
    assert grid_manager.is_move_possible(1, 2) is False
    moves += 1

    grid_manager.set_field(2, 0, "X")
    assert grid_manager.is_move_possible(2, 0) is False
    moves += 1

    grid_manager.set_field(2, 1, "O")
    assert grid_manager.is_move_possible(2, 1) is False
    moves += 1

    grid_manager.set_field(2, 2, "X")
    assert grid_manager.is_move_possible(2, 2) is False
    moves += 1

    assert moves == 9

    for element in grid_manager.get_board():
        assert None not in element


def test_grid_manager_set_field_method() -> None:
    """
    Test if set_field method sets a field on the game board
    and get_field method returns it back
    """
    new_board: List[List[None]] = [[None, None, None] for _ in range(3)]
    grid_manager: GridManager = GridManager(new_board)

    grid_manager.set_field(0, 0, "X")
    assert grid_manager.get_field(0, 0) == "X"

    grid_manager.set_field(0, 1, "O")
    assert grid_manager.get_field(0, 1) == "O"

    grid_manager.set_field(0, 2, "X")
    assert grid_manager.get_field(0, 2) == "X"

    grid_manager.set_field(1, 0, "O")
    assert grid_manager.get_field(1, 0) == "O"

    grid_manager.set_field(1, 1, "X")
    assert grid_manager.get_field(1, 1) == "X"

    grid_manager.set_field(1, 2, "O")
    assert grid_manager.get_field(1, 2) == "O"

    grid_manager.set_field(2, 0, "X")
    assert grid_manager.get_field(2, 0) == "X"

    grid_manager.set_field(2, 1, "O")
    assert grid_manager.get_field(2, 1) == "O"

    grid_manager.set_field(2, 2, "X")
    assert grid_manager.get_field(2, 2) == "X"


def test_grid_set_field_method_wrong_index() -> None:
    """Test if set_field method raises IndexError."""
    new_board: List[List[None]] = [[None, None, None] for _ in range(3)]
    grid_manager: GridManager = GridManager(new_board)

    with pytest.raises(IndexError):
        grid_manager.set_field(3, 3, "X")


def test_grid_get_field_method_wrong_index() -> None:
    """Test if set_field method raises IndexError."""
    new_board: List[List[None]] = [[None, None, None] for _ in range(3)]
    grid_manager: GridManager = GridManager(new_board)

    with pytest.raises(IndexError):
        grid_manager.get_field(3, 3)


def test_grid_manager_make_move() -> None:
    """Test make_move method. Expected: call set_field method."""
    new_board: List[List[None]] = [[None, None, None] for _ in range(3)]
    grid_manager: GridManager = GridManager(new_board)
    with patch.object(GridManager, "set_field") as mocked_method:
        mocked_method.return_value = True
        grid_manager.make_move(0, 0, "X")
        assert mocked_method.called


def test_grid_manager_find_free_spots_method():
    """Test find_free_spots method. Expected: return free spots."""
    new_board: List[List[None]] = [[None, None, None] for _ in range(3)]
    grid_manager: GridManager = GridManager(new_board)
    expected_spots: List[tuple] = [
        (0, 0),
        (0, 1),
        (0, 2),
        (1, 0),
        (1, 1),
        (1, 2),
        (2, 0),
        (2, 1),
        (2, 2),
    ]

    assert grid_manager.find_free_spots() == expected_spots


def test_grid_manager_find_free_spots_method_one_spot_taken():
    """Test find_free_spots method with one field taken. Expected: return free spots."""
    new_board: List[List[None]] = [[None, None, None] for _ in range(3)]
    grid_manager: GridManager = GridManager(new_board)
    grid_manager.set_field(0, 0, "X")
    expected_spots: List[tuple] = [
        (0, 1),
        (0, 2),
        (1, 0),
        (1, 1),
        (1, 2),
        (2, 0),
        (2, 1),
        (2, 2),
    ]

    assert grid_manager.find_free_spots() == expected_spots


def test_grid_manager_find_free_spots_method_more_spots_taken():
    """
    Test find_free_spots method with some fields taken. Expected: return free spots.
    """
    new_board: List[List[None]] = [[None, None, None] for _ in range(3)]
    grid_manager: GridManager = GridManager(new_board)
    grid_manager.set_field(0, 0, "X")
    grid_manager.set_field(0, 1, "O")
    grid_manager.set_field(0, 2, "X")
    grid_manager.set_field(1, 0, "O")
    grid_manager.set_field(2, 2, "X")

    expected_spots: List[tuple] = [(1, 1), (1, 2), (2, 0), (2, 1)]

    assert grid_manager.find_free_spots() == expected_spots


def test_grid_manager_check_game_state_X_winner_diagonal1() -> None:
    """
    Test check_game_state method. Expected: return game state with X as winner.
    Diagonal winner.
    """
    game_board: List[List[None | str]] = [
        [None, None, "X"],
        [None, "X", None],
        ["X", None, None],
    ]
    grid_manager: GridManager = GridManager(game_board).check_game_state()
    assert grid_manager == (True, "X")


def test_grid_manager_check_game_state_X_winner_diagonal2() -> None:
    """
    Test check_game_state method. Expected: return game state with X as winner.
    Diagonal winner.
    """
    game_board: List[List[None | str]] = [
        ["X", None, None],
        [None, "X", None],
        [None, None, "X"],
    ]
    grid_manager: GridManager = GridManager(game_board).check_game_state()
    assert grid_manager == (True, "X")


def test_grid_manager_check_game_state_X_winner_col1() -> None:
    """
    Test check_game_state method. Expected: return game state with X as winner.
    First column winner.
    """
    game_board: List[List[None | str]] = [
        ["X", None, None],
        ["X", None, None],
        ["X", None, None],
    ]
    grid_manager: GridManager = GridManager(game_board).check_game_state()
    assert grid_manager == (True, "X")


def test_grid_manager_check_game_state_O_winner_col2() -> None:
    """
    Test check_game_state method. Expected: return game state with X as winner.
    Second column winner.
    """
    game_board: List[List[None | str]] = [
        [None, "O", None],
        [None, "O", None],
        [None, "O", None],
    ]
    grid_manager: GridManager = GridManager(game_board)
    state: Tuple[bool, str] = grid_manager.check_game_state()
    assert state == (True, "O")


def test_grid_manager_check_game_state_O_winner_col3() -> None:
    """
    Test check_game_state method. Expected: return game state with X as winner.
    Third column winner.
    """
    game_board: List[List[None | str]] = [
        [None, None, "O"],
        [None, None, "O"],
        [None, None, "O"],
    ]
    grid_manager: GridManager = GridManager(game_board)
    state: Tuple[bool, str] = grid_manager.check_game_state()
    assert state == (True, "O")


def test_grid_manager_check_game_state_O_winner_row1() -> None:
    """
    Test check_game_state method. Expected: return game state with X as winner.
    first row winner.
    """
    game_board: List[List[None | str]] = [
        ["O", "O", "O"],
        [None, None, None],
        [None, None, None],
    ]
    grid_manager: GridManager = GridManager(game_board)
    state: Tuple[bool, str] = grid_manager.check_game_state()
    assert state == (True, "O")


def test_grid_manager_check_game_state_X_winner_row2() -> None:
    """
    Test check_game_state method. Expected: return game state with X as winner.
    Second row winner.
    """
    game_board: List[List[None | str]] = [
        [None, None, None],
        ["X", "X", "X"],
        [None, None, None],
    ]
    grid_manager: GridManager = GridManager(game_board)
    state: Tuple[bool, str] = grid_manager.check_game_state()
    assert state == (True, "X")


def test_grid_manager_check_game_state_X_winner_row3() -> None:
    """
    Test check_game_state method. Expected: return game state with X as winner.
    Third row winner.
    """
    game_board: List[List[None | str]] = [
        [None, None, None],
        [None, None, None],
        ["X", "X", "X"],
    ]
    grid_manager: GridManager = GridManager(game_board)
    state: Tuple[bool, str] = grid_manager.check_game_state()
    assert state == (True, "X")


def test_grid_manager_check_game_state_no_winner() -> None:
    """Test check_game_state method. Expected: return game state with no winner."""
    game_board: List[List[None | str]] = [
        [None, None, None],
        [None, "X", None],
        ["X", None, "X"],
    ]
    grid_manager: GridManager = GridManager(game_board)
    state: Tuple[bool, str] = grid_manager.check_game_state()
    assert state == (False, None)
