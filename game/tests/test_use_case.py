from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from unittest.mock import patch

import pytest
from entities.entites import (
    GameListPydantic,
    GamePydantic,
    UserListPydantic,
    UserPydantic,
    UserSessionListPydantic,
    UserSessionPydantic,
)
from entities.types import GameStatus, SessionStatus, SessionStatusStates
from pytest_mock import MockerFixture
from settings import PlayCredits
from tests.factories import GameFactory, UserFactory, UserSessionFactory
from tests.utils import (
    game2pydantic,
    game2pydantic_list,
    user2pydantic,
    user2pydantic_list,
    user_session2pydantic,
    user_session2pydantic_list,
)
from use_cases.use_case import UserUseCase
from utils.exceptions import NoGameFoundException


def test_create_or_400_method_exists(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """Test use_case.get_or_404 method. Expect to return error"""

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=True)
    res: Tuple[dict, int] = use_case.create_or_400({"email": "test_email"})
    assert isinstance(res, tuple)
    assert res[1] == 400
    assert res[0] == {"error": "User already exists"}


def test_create_or_400_method(use_case: UserUseCase, mocker: "MockerFixture") -> None:
    """Test use_case.get_or_404 method. Expect to return user as pydantic"""

    user: UserFactory = UserFactory.create()
    user_pydantic: UserPydantic = user2pydantic(user)

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=False)
    mocker.patch("repos.db_repo.UserDBRepo.create", return_value=user_pydantic)
    res: Tuple[dict, int] = use_case.create_or_400({"email": user.email})
    assert isinstance(res, tuple)
    assert res[1] == 201
    assert res[0] == user_pydantic.dict()


def test_get_user_method(use_case: UserUseCase, mocker: "MockerFixture") -> None:
    """Test use_case.get_user method. Expect to return user as pydantic"""

    user: UserFactory = UserFactory.create()
    user_pydantic: UserListPydantic = user2pydantic_list(user)

    mocker.patch("repos.db_repo.UserDBRepo.filter", return_value=user_pydantic)
    res: UserPydantic = use_case.get_user(email=user.email)
    assert isinstance(res, UserPydantic)
    assert res == user_pydantic.__root__[0]


def test_get_user_method_no_user(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """Test use_case.get_user method. Expect to return None"""

    mocker.patch("repos.db_repo.UserDBRepo.filter", return_value=False)
    res: UserPydantic = use_case.get_user(email="test_email")
    assert not res


def test_update_account_method_to_high_num_credits_sent(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.update_account method. Case when user has 0 credits, and want to
    update account with 100 credits. Expect to return error
    """

    kwargs: Dict[str, int] = {"credits": 100}
    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=True)
    res: Tuple[dict, int] = use_case.update_user_account(user_id=1, **kwargs)

    assert res[1] == 403
    assert res[0] == {"error": "Invalid credits count. Should be less than 10"}


@pytest.mark.parametrize("credit_count", range(1, 11))
def test_update_account_method_user_credits_too_high(
    use_case: UserUseCase, mocker: "MockerFixture", credit_count: int
) -> None:
    """
    Test use_case.update_account method. Case when user has 0 credits, and want to
    update account with 100 credits. Expect to return error
    """

    user: UserFactory = UserFactory.create(credits=credit_count)
    kwargs: Dict[str, int] = {"credits": 10}
    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user)
    res: Tuple[dict, int] = use_case.update_user_account(user_id=1, **kwargs)
    assert res[1] == 403
    assert res[0] == {"error": "Invalid credits count. Should be 0 before updating"}


def test_update_account_method(use_case: UserUseCase, mocker: "MockerFixture") -> None:
    """Test use_case.update_account. Expect to update user account"""

    kwargs_: Dict[str, int] = {"credits": 10, "email": "new_email"}

    class MockRefresh:
        def __call__(self, obj, **kwargs):
            """Update obj attributes"""
            for key, val in kwargs.items():
                setattr(obj, key, kwargs_[key])

            return obj

    with patch("repos.db_repo.UserDBRepo.update_fields", side_effect=MockRefresh()):
        user: UserFactory = UserFactory.create(credits=0)
        user_pydantic: UserPydantic = user2pydantic(user)
        mocker.patch(
            "use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic
        )
        res: Tuple[dict, int] = use_case.update_user_account(user_id=user.id, **kwargs_)

        expected_res: dict = user_pydantic.dict(exclude={"password"})
        expected_res.update({"message": "Account updated"})

        assert res[1] == 200
        assert res[0] == expected_res
        assert res[0]["credits"] == 10
        assert res[0]["email"] == "new_email"


def test_update_account_method_no_user(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """Test use_case.update_account. Expected error because of no user found"""

    kwargs_: Dict[str, int] = {"credits": 10, "email": "new_email"}
    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=None)
    res: Tuple[dict, int] = use_case.update_user_account(user_id=1, **kwargs_)

    assert res[1] == 404
    assert res[0]["error"] == "User not found"


def test_start_session_method_no_user(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.start_session method.
    Expect to return error because of no user found
    """

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=None)
    res: Tuple[Dict[str, str], int] = use_case.start_session(user_id=1)

    assert res[1] == 404
    assert res[0]["error"] == "User not found"


def test_start_session_method_session_found(
    use_case: UserUseCase,
    mocker: "MockerFixture",
    trio_objects_package: Tuple[
        UserPydantic, UserSessionListPydantic, GameListPydantic
    ],
) -> None:
    """
    Test use_case.start_session method. Expect to return error because of session found.
    Response should include session details with game details
    """

    user_pydantic: UserPydantic
    user_session_pydantic: UserSessionListPydantic
    game_pydantic: GameListPydantic
    user_pydantic, user_session_pydantic, game_pydantic = trio_objects_package

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic)
    mocker.patch(
        "repos.db_repo.UserSessionDBRepo.filter", return_value=user_session_pydantic
    )
    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic)

    user_session_instance: UserSessionPydantic = user_session_pydantic.__root__[0]

    expected_res: Dict[str, str] = {
        "error": f"Session already started with id {user_session_instance.id}",
        "session_detail": {
            **user_session_instance.dict(),
            "games": [game_pydantic.__root__[0].dict(exclude={"board"})],
        },
    }
    res: Tuple[Dict[str, str], int] = use_case.start_session(user_id=1)

    assert res[1] == 400
    assert res[0] == expected_res


def test_start_session_method(use_case: UserUseCase, mocker: "MockerFixture") -> None:
    """
    Test use_case.start_session method.
    Expect to return response 200 with session details.
    Because of no session found, new session should be created
    """

    user: UserFactory = UserFactory.create(credits=0)
    user_pydantic: UserPydantic = user2pydantic(user)

    user_session: UserSessionFactory = UserSessionFactory.create(user_id=user.id)
    user_session_pydantic: UserSessionPydantic = user_session2pydantic(user_session)
    game: GameFactory = GameFactory.create(
        session_id=user_session.id, user_id=user.id, status=GameStatus.IN_PROGRESS.value
    )
    game_pydantic: GamePydantic = game2pydantic(game)

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic)
    mocker.patch("repos.db_repo.UserSessionDBRepo.filter", return_value=None)
    mocker.patch("repos.db_repo.GameDBRepo.create", return_value=game_pydantic)

    mocker.patch(
        "repos.db_repo.UserSessionDBRepo.create", return_value=user_session_pydantic
    )
    mocker.patch("repos.db_repo.UserDBRepo.update_fields", return_value=None)

    expected_res: Dict[str, Any] = {
        **user_session_pydantic.dict(),
        "game_id": game_pydantic.id,
        "message": "Game session started",
    }
    res: Tuple[Dict[str, str], int] = use_case.start_session(user_id=1)

    assert res[1] == 200
    assert res[0] == expected_res


def test_create_new_game_method_no_user(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.create_new_game method.
    Expect to return error because of no user found
    """

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=None)
    res: Tuple[Dict[str, str], int] = use_case.create_new_game(user_id=1, session_id=1)

    assert res[1] == 404
    assert res[0]["error"] == "User not found"


def test_create_new_game_method_no_session(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.create_new_game method.
    Expect to return error because of no session found
    """

    user: UserFactory = UserFactory.create(credits=0)
    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user)
    mocker.patch("repos.db_repo.UserSessionDBRepo.filter", return_value=None)
    res: Tuple[Dict[str, str], int] = use_case.create_new_game(user_id=1, session_id=1)

    assert res[1] == 400
    assert res[0]["error"] == "No active session found"


def test_create_new_game_method_game_exists(
    use_case: UserUseCase,
    mocker: "MockerFixture",
    trio_objects_package: Tuple[
        UserPydantic, UserSessionListPydantic, GameListPydantic
    ],
) -> None:
    """
    Test use_case.create_new_game method. Expected to return error
    because of game already exists
    """

    user_pydantic: UserPydantic
    user_session_pydantic: UserSessionListPydantic
    game_pydantic_list: GameListPydantic
    user_pydantic, user_session_pydantic, game_pydantic_list = trio_objects_package

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic)
    mocker.patch(
        "repos.db_repo.UserSessionDBRepo.filter", return_value=user_session_pydantic
    )
    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic_list)

    expected: Dict[str, Any] = {
        "error": "Game already started",
        "game_id": game_pydantic_list.__root__[0].id,
        "session_id": user_session_pydantic.__root__[0].id,
    }

    res: Tuple[Dict[str, str], int] = use_case.create_new_game(user_id=1, session_id=1)

    assert res[1] == 400
    assert res[0]["error"] == expected["error"]
    assert res[0] == expected


def test_create_new_game_method_session_finished(
    use_case: UserUseCase,
    mocker: "MockerFixture",
    trio_objects_package: Tuple[
        UserPydantic, UserSessionListPydantic, GameListPydantic
    ],
) -> None:
    """
    Test use_case.create_new_game method. Expected return error
    because of session already finished
    """

    user_pydantic: UserPydantic
    user_session_pydantic: UserSessionListPydantic
    game_pydantic_list: GameListPydantic
    user_pydantic, user_session_pydantic, game_pydantic_list = trio_objects_package

    user_session_pydantic.__root__[0].status = SessionStatusStates.FINISHED.value

    game_pydantic_list.__root__[0].status = GameStatus.FINISHED.value
    game_pydantic_list.__root__[0].user_id = user_pydantic.id

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic)
    mocker.patch(
        "repos.db_repo.UserSessionDBRepo.filter", return_value=user_session_pydantic
    )
    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=None)
    mocker.patch(
        "repos.db_repo.GameDBRepo.create", return_value=game_pydantic_list.__root__[0]
    )
    mocker.patch(
        "use_cases.use_case.UserUseCase.update_session_status", return_value=None
    )

    res: Tuple[Dict[str, str], int] = use_case.create_new_game(user_id=1, session_id=1)

    assert res[1] == 400
    assert res[0]["error"] == "Session already finished"


@pytest.mark.parametrize("credit_count", range(1, 3))
def test_create_new_game_method_no_credits(
    credit_count: int,
    use_case: UserUseCase,
    mocker: "MockerFixture",
    trio_objects_package: Tuple[
        UserPydantic, UserSessionListPydantic, GameListPydantic
    ],
) -> None:
    """Test use_case.create_new_game method. Expected to return success"""

    user_pydantic: UserPydantic
    user_session_pydantic: UserSessionListPydantic
    game_pydantic_list: GameListPydantic
    user_pydantic, user_session_pydantic, game_pydantic_list = trio_objects_package

    user_pydantic.credits = credit_count

    user_session_pydantic.__root__[0].status = SessionStatusStates.ACTIVE.value
    user_session_pydantic.__root__[0].user_id = user_pydantic.id

    game_pydantic_list.__root__[0].status = GameStatus.FINISHED.value
    game_pydantic_list.__root__[0].user_id = user_pydantic.id
    game_pydantic_list.__root__[0].session_id = user_session_pydantic.__root__[0].id

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic)
    mocker.patch(
        "repos.db_repo.UserSessionDBRepo.filter", return_value=user_session_pydantic
    )
    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=None)
    mocker.patch(
        "repos.db_repo.GameDBRepo.create", return_value=game_pydantic_list.__root__[0]
    )
    mocker.patch(
        "use_cases.use_case.UserUseCase.update_session_status", return_value=None
    )

    res: Tuple[Dict[str, str], int] = use_case.create_new_game(user_id=1, session_id=1)

    assert res[1] == 400
    assert res[0]["error"] == "Not enough credits. Game cannot start"


def test_create_new_game_method_success(
    use_case: UserUseCase,
    mocker: "MockerFixture",
    trio_objects_package: Tuple[
        UserPydantic, UserSessionListPydantic, GameListPydantic
    ],
) -> None:
    """Test use_case.create_new_game method. Expected to return success"""

    user_pydantic: UserPydantic
    user_session_pydantic: UserSessionListPydantic
    game_pydantic_list: GameListPydantic
    user_pydantic, user_session_pydantic, game_pydantic_list = trio_objects_package

    user_pydantic.credits = 10

    user_session_pydantic.__root__[0].status = SessionStatusStates.ACTIVE.value
    user_session_pydantic.__root__[0].user_id = user_pydantic.id

    game_pydantic_list.__root__[0].status = GameStatus.FINISHED.value
    game_pydantic_list.__root__[0].user_id = user_pydantic.id
    game_pydantic_list.__root__[0].session_id = user_session_pydantic.__root__[0].id

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic)
    mocker.patch(
        "repos.db_repo.UserSessionDBRepo.filter", return_value=user_session_pydantic
    )
    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=None)
    mocker.patch(
        "repos.db_repo.GameDBRepo.create", return_value=game_pydantic_list.__root__[0]
    )
    mocker.patch(
        "use_cases.use_case.UserUseCase.update_session_status", return_value=None
    )
    mocker.patch("repos.db_repo.UserDBRepo.update_fields", return_value=None)

    expected_result: Dict[str, Any] = {
        "game_details": game_pydantic_list.__root__[0].dict(exclude={"board"})
    }

    res: Tuple[Dict[str, str], int] = use_case.create_new_game(user_id=1, session_id=1)

    assert res[1] == 200
    assert res[0] == expected_result


def test_get_session_obj(use_case: UserUseCase, mocker: "MockerFixture") -> None:
    """
    Test use_case.get_session_obj method.
    Expected to return UserSessionListPydantic object
    """
    user_session: UserSessionFactory = UserSessionFactory()
    user_session_pydantic: UserSessionPydantic = user_session2pydantic(user_session)

    mocker.patch(
        "repos.db_repo.UserSessionDBRepo.filter", return_value=user_session_pydantic
    )

    res: UserSessionPydantic | None = use_case.get_session_object(
        session_id=1, user_id=1
    )

    assert res == user_session_pydantic


def test_get_session_obj_no_session(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """Test use_case.get_session_obj method. Expect to return be None"""
    mocker.patch("repos.db_repo.UserSessionDBRepo.filter", return_value=None)

    res: UserSessionPydantic | None = use_case.get_session_object(
        session_id=1, user_id=1
    )

    assert not res


def test_validate_field_indexes_method_success(use_case: UserUseCase) -> None:
    """
    Test use_case.validate_field_indexes method.
    Expected to return success because fields are valid
    """

    expected: Tuple[List[int, int], Dict[str, str]] = ([1, 2], {})
    res: Tuple[List[int, int], Dict[str, str]] = use_case.validate_field_indexes(
        fields={"row": 1, "col": 2}
    )

    assert res == expected


def test_validate_field_indexes_method_fail(use_case: UserUseCase) -> None:
    """
    Test use_case.validate_field_indexes method.
    Expected to return errors because row and col are not valid (too high)
    """

    expected: Tuple[List[int, int], Dict[str, str]] = (
        [10, 2],
        {"row": "The number is wrong. Should be between 1 and 3"},
    )
    res: Tuple[List[int, int], Dict[str, str]] = use_case.validate_field_indexes(
        fields={"row": 10, "col": 2}
    )

    assert res == expected

    expected = ([2, 10], {"col": "The number is wrong. Should be between 1 and 3"})
    res: Tuple[List[int, int], Dict[str, str]] = use_case.validate_field_indexes(
        fields={"row": 2, "col": 10}
    )

    assert res == expected

    expected = (
        [10, 10],
        {
            "col": "The number is wrong. Should be between 1 and 3",
            "row": "The number is wrong. Should be between 1 and 3",
        },
    )
    res: Tuple[List[int, int], Dict[str, str]] = use_case.validate_field_indexes(
        fields={"row": 10, "col": 10}
    )

    assert res == expected


def test_validate_field_indexes_method_not_an_int(use_case: UserUseCase) -> None:
    """
    Test use_case.validate_field_indexes method.
    Expected to return errors because row and col are not integers
    """

    expected: Tuple[List[Any, Any], Dict[str, str]] = (
        ["a", 2],
        {"row": "Should be integer, not object or string"},
    )

    res: Tuple[List[Any, Any], Dict[str, str]] = use_case.validate_field_indexes(
        fields={"row": "a", "col": 2}
    )

    assert res == expected

    expected = ([1, "a"], {"col": "Should be integer, not object or string"})

    res: Tuple[List[Any, Any], Dict[str, str]] = use_case.validate_field_indexes(
        fields={"row": 1, "col": "a"}
    )

    assert res == expected

    expected = (
        ["a", "a"],
        {
            "row": "Should be integer, not object or string",
            "col": "Should be integer, not object or string",
        },
    )

    res: Tuple[List[Any, Any], Dict[str, str]] = use_case.validate_field_indexes(
        fields={"row": "a", "col": "a"}
    )

    assert res == expected


def test_player_play_method_fields_not_valid(
    use_case: UserUseCase,
) -> None:
    """
    Test use_case.player_play method.
    Expected to return error because fields are not valid (col too high)
    """

    expected = {
        "status": "error",
        "error list": {
            "col": "The number is wrong. Should be between 1 and 3",
        },
    }

    game: GameFactory = GameFactory()
    game_pydantic: GamePydantic = game2pydantic(game)

    res: Tuple[Dict[str, str], int] = use_case._player_play(
        data={"row": 1, "col": 10}, user_game=game_pydantic
    )

    assert res[0] == expected
    assert res[1] == 400


def test_player_play_method_fields_none(use_case) -> None:
    """
    Test use_case.player_play method.
    Expected to return error because fields are not sent
    """
    game: GameFactory = GameFactory()
    game_pydantic: GamePydantic = game2pydantic(game)

    expected = {"error": "Invalid request. You didnt sent row and col"}

    res: Tuple[Dict[str, str], int] = use_case._player_play(
        data={}, user_game=game_pydantic
    )

    assert res[0] == expected
    assert res[1] == 400


def test_player_play_method_fields_invalid_move(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.player_play method.
    Expected to return error because move is not possible
    """
    game: GameFactory = GameFactory()
    game_pydantic: GamePydantic = game2pydantic(game)

    mocker.patch("repos.managers.GridManager.is_move_possible", return_value=False)

    expected = {
        "error": "Invalid move. Field is taken",
        "actual_board": game.board["board"],
        "player_sign": game.symbol,
    }

    res: Tuple[Dict[str, str], int] = use_case._player_play(
        data={"row": 1, "col": 1}, user_game=game_pydantic
    )

    assert res[0] == expected
    assert res[1] == 400


def test_player_play_method_fields_valid_move(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.player_play method.
    Expected to return status code 200 with updated game board
    """
    game: GameFactory = GameFactory()
    game_pydantic: GamePydantic = game2pydantic(game)

    mocker.patch("repos.managers.GridManager.is_move_possible", return_value=True)
    mocker.patch("repos.db_repo.GameDBRepo.update_fields", return_value=False)

    res: Tuple[Dict[str, str], int] = use_case._player_play(
        data={"row": 1, "col": 1}, user_game=game_pydantic
    )

    game_pydantic.board["board"][0][0] = game.symbol

    assert res[0] == game_pydantic.board["board"]
    assert res[1] == 200


def test_random_play_method(use_case: UserUseCase, mocker: "MockerFixture") -> None:
    """
    Test use_case.random_play method.
    Expected to make a move and return updated game board
    """

    class MockRefresh:
        def __call__(self, obj, **kwargs):
            """Update obj attributes"""
            for key, val in kwargs.items():
                setattr(obj, key, val)

            return obj

    with patch("repos.db_repo.GameDBRepo.update_fields", side_effect=MockRefresh()):
        user: UserFactory = UserFactory()
        user_pydantic: UserPydantic = user2pydantic(user)
        game: GameFactory = GameFactory()
        game_pydantic: GamePydantic = game2pydantic(game)

        mocker.patch(
            "use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic
        )

        mocker.patch(
            "use_cases.use_case.UserUseCase.get_random_field_indexes",
            return_value=(1, 1),
        )

        res: Tuple[Dict[str, Any], int] = use_case.random_play(
            game_pydantic, 1, user_id=user.id
        )
        expected_board = game_pydantic.board["board"]
        expected_board[0][0] = "X" if game_pydantic.symbol != "X" else "O"
        expected_response: Dict[str, Any] = {
            "actual_board": expected_board,
            "player_sign": game_pydantic.symbol,
            "credits": user.credits,
        }

        assert res[0] == expected_response
        assert res[1] == 200


def test_random_play_method_not_possible_move(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.random_play method.
    Expected to return error, because there is no possible move - board is full
    """

    user: UserFactory = UserFactory()
    user_pydantic: UserPydantic = user2pydantic(user)
    game: GameFactory = GameFactory(
        board={"board": [["X", "O", "X"], ["O", "X", "O"], ["X", "O", "X"]]}
    )

    game_pydantic: GamePydantic = game2pydantic(game)

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic)

    mocker.patch(
        "use_cases.use_case.UserUseCase.get_random_field_indexes", return_value=(1, 1)
    )

    res: Tuple[Dict[str, str], int] = use_case.random_play(
        game_pydantic, 1, user_id=user.id
    )

    assert res[0] == {"error": "Board is full. Game over"}
    assert res[1] == 400


def test_lets_play_method_no_game(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.lets_play method. Expected to return error, because there is no game
    """
    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=None)
    res: Tuple[Dict[str, str], int] = use_case.lets_play_POST(
        user_id=1, game_id=1, session_id=1, data={}
    )
    assert res[0] == {"error": "Game not found"}
    assert res[1] == 404


def test_lets_play_method_game_not_started(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.lets_play method.
    Expected to return error, because game is not started
    """

    game: GameFactory = GameFactory(status="not_started")
    game_pydantic_list: GameListPydantic = game2pydantic_list(game)

    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic_list)
    mocker.patch(
        "use_cases.use_case.UserUseCase._player_play",
        return_value=({"error": "Game is not started"}, 400),
    )

    res: Tuple[Dict[str, str], int] = use_case.lets_play_POST(
        user_id=1, game_id=1, session_id=1, data={}
    )

    assert res[0] == {"error": "Game is not started"}
    assert res[1] == 400


def test_lets_play_method_game_finished(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.lets_play method.
    Expected to return error, because game is finished
    """

    game: GameFactory = GameFactory(status="finished")
    game_pydantic_list: GameListPydantic = game2pydantic_list(game)

    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic_list)
    mocker.patch("use_cases.use_case.UserUseCase._player_play", return_value=({}, 200))
    mocker.patch(
        "use_cases.use_case.UserUseCase.check_game_status", return_value=(True, "X")
    )

    res: Tuple[Dict[str, str], int] = use_case.lets_play_POST(
        user_id=1, game_id=1, session_id=1, data={}
    )

    assert res[0] == "X"
    assert res[1] == 200


def test_lets_play_method_game_in_progress(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.lets_play method.
    Expected to return game board - status code is 200
    """

    user: UserFactory = UserFactory()
    game: GameFactory = GameFactory()
    game_pydantic_list: GameListPydantic = game2pydantic_list(game)
    game.board = {"board": [["X", None, "X"], ["O", "X", None], [None, "O", "X"]]}

    random_play_response: Dict[str, Any] = {
        "actual_board": game.board["board"],
        "player_sign": game.symbol,
        "credits": user.credits,
    }

    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic_list)
    mocker.patch("use_cases.use_case.UserUseCase._player_play", return_value=({}, 200))
    mocker.patch(
        "use_cases.use_case.UserUseCase.check_game_status", return_value=(False, None)
    )
    mocker.patch(
        "use_cases.use_case.UserUseCase.random_play",
        return_value=(random_play_response, 200),
    )

    res: Tuple[Dict[str, str], int] = use_case.lets_play_POST(
        user_id=1, game_id=1, session_id=1, data={}
    )

    assert res[0] == random_play_response
    assert res[1] == 200


def test_check_game_status_method_raise_exception(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.check_game_status method.
    Expected to raise exception because there is no game
    """

    with pytest.raises(NoGameFoundException):
        mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=None)

        use_case.check_game_status(session_id=1, game_id=1, user_id=1)


def test_check_game_status_method_game_in_progress(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.check_game_status method.
    Expected to return information, that game is in progress
    """

    user: UserFactory = UserFactory()
    user_pydantic: UserPydantic = user2pydantic(user)
    game: GameFactory = GameFactory()
    game_pydantic_list: GameListPydantic = game2pydantic_list(game)

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic)
    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic_list)
    mocker.patch(
        "repos.managers.GridManager.check_game_state", return_value=(False, None)
    )
    expected_res: dict = {
        "status": "game is in progress",
        "actual_board": game.board["board"],
        "credits": user.credits,
        "user_sign": game.symbol,
    }

    res: Tuple[bool, str] = use_case.check_game_status(
        session_id=1, game_id=1, user_id=1
    )

    assert res[1] == expected_res
    assert res[0] is False


def test_check_game_status_method_game_finished_player_win(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.check_game_status method.
    Expected to update objects and user win
    """

    class MockRefresh:
        def __call__(self, obj, **kwargs):
            """Update obj attributes"""
            for key, val in kwargs.items():
                setattr(obj, key, val)

            return obj

    with patch("repos.db_repo.UserDBRepo.update_fields", side_effect=MockRefresh()):
        with patch(
            "repos.db_repo.UserSessionDBRepo.update_fields", side_effect=MockRefresh()
        ):
            with patch(
                "repos.db_repo.GameDBRepo.update_fields", side_effect=MockRefresh()
            ):
                user: UserFactory = UserFactory()
                user_pydantic: UserPydantic = user2pydantic(user)
                game: GameFactory = GameFactory()
                game_pydantic_list: GameListPydantic = game2pydantic_list(game)

                user_credits: int = user.credits

                session: UserSessionFactory = UserSessionFactory()
                session_pydantic: UserSessionListPydantic = user_session2pydantic_list(
                    session
                )

                mocker.patch(
                    "use_cases.use_case.UserUseCase.get_session_object",
                    return_value=session_pydantic,
                )
                mocker.patch(
                    "use_cases.use_case.UserUseCase.get_user",
                    return_value=user_pydantic,
                )
                mocker.patch(
                    "repos.db_repo.GameDBRepo.filter", return_value=game_pydantic_list
                )
                mocker.patch(
                    "repos.managers.GridManager.check_game_state",
                    return_value=(True, game.symbol),
                )

                res: Tuple[bool, str] = use_case.check_game_status(
                    session_id=1, game_id=1, user_id=1
                )

                expected_res = {
                    "status": "You won",
                    "actual_board": game.board["board"],
                    "credits": user_pydantic.credits,
                    "user_sign": game.symbol,
                }

                assert res[1] == expected_res
                assert res[0] is True
                assert session_pydantic.__root__[0].score == 1
                assert user_pydantic.credits == user_credits + PlayCredits.WIN.value
                assert (game_res := game_pydantic_list.__root__[0]).status == "finished"
                assert game_res.winner is True


def test_check_game_status_method_game_finished_no_winner(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.check_game_status method.
    Expected to return information about no winner
    """

    class MockRefresh:
        def __call__(self, obj, **kwargs):
            """Update obj attributes"""
            for key, val in kwargs.items():
                setattr(obj, key, val)

            return obj

    with patch("repos.db_repo.GameDBRepo.update_fields", side_effect=MockRefresh()):
        user: UserFactory = UserFactory()
        user_pydantic: UserPydantic = user2pydantic(user)
        game: GameFactory = GameFactory()
        game_pydantic_list: GameListPydantic = game2pydantic_list(game)

        session: UserSessionFactory = UserSessionFactory()
        session_pydantic: UserSessionListPydantic = user_session2pydantic_list(session)

        mocker.patch(
            "use_cases.use_case.UserUseCase.get_session_object",
            return_value=session_pydantic,
        )
        mocker.patch(
            "use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic
        )
        mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic_list)
        mocker.patch(
            "repos.managers.GridManager.check_game_state", return_value=(True, None)
        )

        res: Tuple[bool, str] = use_case.check_game_status(
            session_id=1, game_id=1, user_id=1
        )

        expected_res = {
            "status": "There is no winner",
            "actual_board": game.board["board"],
            "credits": user_pydantic.credits,
            "user_sign": game.symbol,
        }

        assert res[1] == expected_res
        assert res[0] is True
        assert (game_res := game_pydantic_list.__root__[0]).status == "finished"
        assert game_res.winner is False


def test_check_game_status_method_game_finished_player_lost(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.check_game_status method.
    Expected to update objects and information about user lost
    """

    class MockRefresh:
        def __call__(self, obj, **kwargs):
            """Update obj attributes"""
            for key, val in kwargs.items():
                setattr(obj, key, val)

            return obj

    with patch("repos.db_repo.GameDBRepo.update_fields", side_effect=MockRefresh()):
        user: UserFactory = UserFactory()
        user_pydantic: UserPydantic = user2pydantic(user)
        game: GameFactory = GameFactory()
        game_pydantic_list: GameListPydantic = game2pydantic_list(game)

        session: UserSessionFactory = UserSessionFactory()
        session_pydantic: UserSessionListPydantic = user_session2pydantic_list(session)

        mocker.patch(
            "use_cases.use_case.UserUseCase.get_session_object",
            return_value=session_pydantic,
        )
        mocker.patch(
            "use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic
        )
        mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic_list)
        mocker.patch(
            "repos.managers.GridManager.check_game_state",
            return_value=(True, "X" if game.symbol == "O" else "O"),
        )

        res: Tuple[bool, str] = use_case.check_game_status(
            session_id=1, game_id=1, user_id=1
        )

        expected_res = {
            "status": "You lost",
            "actual_board": game.board["board"],
            "credits": user_pydantic.credits,
            "user_sign": game.symbol,
        }

        assert res[1] == expected_res
        assert res[0] is True
        assert (game_res := game_pydantic_list.__root__[0]).status == "finished"
        assert game_res.winner is None


def test_update_session_status_method(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.update_session_status method.
    Expected to update session status because user is out of the credits
    """

    class MockRefresh:
        def __call__(self, obj, **kwargs):
            """Update obj attributes"""
            for key, val in kwargs.items():
                setattr(obj, key, val)

            return obj

    with patch(
        "repos.db_repo.UserSessionDBRepo.update_fields", side_effect=MockRefresh()
    ):
        user: UserFactory = UserFactory(credits=2)
        user_pydantic: UserPydantic = user2pydantic(user)
        session: UserSessionFactory = UserSessionFactory(ended_at=None)
        session_pydantic: UserSessionListPydantic = user_session2pydantic_list(session)

        mocker.patch(
            "use_cases.use_case.UserUseCase.get_session_object",
            return_value=session_pydantic,
        )
        mocker.patch(
            "use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic
        )

        res: bool = use_case.update_session_status(session_id=1, user_id=user.id)

        assert res is None
        assert (session_obj := session_pydantic.__root__[0]).status == "finished"
        assert session_obj.ended_at is not None


def test_update_session_status_method_no_update(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.update_session_status method.
    Expected to not update session status because user has credits
    """

    class MockRefresh:
        def __call__(self, obj, **kwargs):
            """Update obj attributes"""
            for key, val in kwargs.items():
                setattr(obj, key, val)

            return obj

    with patch(
        "repos.db_repo.UserSessionDBRepo.update_fields", side_effect=MockRefresh()
    ):
        user: UserFactory = UserFactory(credits=4)
        user_pydantic: UserPydantic = user2pydantic(user)
        session: UserSessionFactory = UserSessionFactory(ended_at=None)
        session_pydantic: UserSessionListPydantic = user_session2pydantic_list(session)

        mocker.patch(
            "use_cases.use_case.UserUseCase.get_session_object",
            return_value=session_pydantic,
        )
        mocker.patch(
            "use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic
        )

        res: None = use_case.update_session_status(session_id=1, user_id=user.id)

        assert res is None
        assert (session_obj := session_pydantic.__root__[0]).status == "finished"
        assert session_obj.ended_at is None


def test_lets_play_get_method_no_game(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.lets_play get method. Expect to return game not found error
    """

    user: UserFactory = UserFactory()
    user_pydantic: UserPydantic = user2pydantic(user)

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic)
    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=None)

    res: Tuple[GameListPydantic, UserSessionListPydantic] = use_case.lets_play_GET(
        session_id=1, game_id=1, user_id=1
    )

    assert res[0] == {"error": "Game not found"}
    assert res[1] == 404


def test_lets_play_get_method_ok(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.lets_play get method. Expect to return game information
    """

    user: UserFactory = UserFactory()
    user_pydantic: UserPydantic = user2pydantic(user)
    game: GameFactory = GameFactory()
    game.board = {"board": ["X", "O", "X", "O", "X", "O", "X", "O", "X"]}
    game_pydantic: GameListPydantic = game2pydantic_list(game)

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=user_pydantic)
    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic)

    res: Tuple[GameListPydantic, UserSessionListPydantic] = use_case.lets_play_GET(
        session_id=1, game_id=1, user_id=1
    )

    expected: dict = {
        "actual_board": game.board["board"],
        "player_sign": game.symbol,
        "game": game.id,
        "session": game.session_id,
        "credits": user.credits,
    }

    assert res[0] == expected
    assert res[1] == 200


def test_check_session_status_method_error(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.check_session_status method. Expect to return session status
    """

    mocker.patch("use_cases.use_case.UserUseCase.get_session_object", return_value=None)

    res: SessionStatus = use_case.check_session_status(session_id=1, user_id=1)

    assert isinstance(res, SessionStatus)
    assert res.active is False
    assert res.session_data == {"error": "Game session not found for requested user"}
    assert res.status_code == 404


def test_check_session_status_session_finished(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.check_session_status method. Expect to return session status
    """

    session: UserSessionFactory = UserSessionFactory(
        status=SessionStatusStates.FINISHED.value
    )
    session_pydantic: UserSessionListPydantic = user_session2pydantic_list(session)

    mocker.patch(
        "use_cases.use_case.UserUseCase.get_session_object",
        return_value=session_pydantic,
    )

    res: SessionStatus = use_case.check_session_status(session_id=1, user_id=1)

    assert isinstance(res, SessionStatus)
    assert res.active is False
    assert res.session_data == {"message": "Game session is finished"}
    assert res.status_code == 400


def test_check_session_status_session_active(
    use_case: UserUseCase, mocker: "MockerFixture"
) -> None:
    """
    Test use_case.check_session_status method. Expect to return session status
    """

    session: UserSessionFactory = UserSessionFactory(
        status=SessionStatusStates.ACTIVE.value
    )
    session_pydantic: UserSessionListPydantic = user_session2pydantic_list(session)

    mocker.patch(
        "use_cases.use_case.UserUseCase.get_session_object",
        return_value=session_pydantic,
    )

    res: SessionStatus = use_case.check_session_status(session_id=1, user_id=1)

    assert isinstance(res, SessionStatus)
    assert res.active is True
    assert res.session_data == session_pydantic.dict()
    assert res.status_code == 200


def test_time_spent_method_minutes(use_case: UserUseCase) -> None:
    """Test use_case.time_spent method. Expect to return minutes"""

    start_time: datetime = datetime.now()
    end_time: datetime = start_time + timedelta(minutes=10)

    res: str = use_case.time_played(start_time, end_time)
    expected_result: str = "10 minutes"
    assert res == expected_result


def test_time_spent_method_minutes_seconds(use_case: UserUseCase) -> None:
    """Test use_case.time_spent method. Expect to return minutes and seconds"""

    start_time: datetime = datetime.now()
    end_time: datetime = start_time + timedelta(seconds=10)

    res: str = use_case.time_played(start_time, end_time)
    expected_result: str = "10 seconds"
    assert res == expected_result


def test_time_spent_method_minutes_in_progress(use_case: UserUseCase) -> None:
    """Test use_case.time_spent method. Expect to return in progress"""

    start_time: datetime = datetime.now()
    end_time = None

    res: str = use_case.time_played(start_time, end_time)
    expected_result: str = "In progress"
    assert res == expected_result


def test_anonymize_email_method(use_case: UserUseCase) -> None:
    """Test use_case.anonymize_email method. Expect to return anonymized email"""

    email: str = "test_email@gmail.com"
    expected_result: str = "tes****com"

    res: str = use_case.anonymize_email(email)
    assert res == expected_result


def test_get_high_scores_method(use_case: UserUseCase, mocker: "MockerFixture") -> None:
    """Test use_case.get_high_scores method. Expect to return high scores"""

    user_session: UserSessionFactory = UserSessionFactory.create(score=10)
    user_session.created_at = datetime.now()
    user_session.ended_at = datetime.now() + timedelta(minutes=10)

    mocker.patch("repos.db_repo.UserSessionDBRepo.all", return_value=[user_session])
    time_diff: timedelta = user_session.ended_at - user_session.created_at

    result: str
    minutes: float = int(time_diff.total_seconds() / 60)
    result = f"{minutes} minutes"
    if not minutes:
        result = f"{int(time_diff.total_seconds())} seconds"

    response: int
    status_code: int

    response, status_code = use_case.get_high_scores()
    expected_result: List[Dict[str, str]] = [
        {
            "date": user_session.ended_at.strftime("%d-%m-%Y"),
            "score": user_session.score,
            "user": user_session.user.email[:3] + "****" + user_session.user.email[-3:],
            "time_played": result,
        }
    ]

    assert response == expected_result
    assert status_code == 200
