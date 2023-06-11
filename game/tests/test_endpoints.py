from copy import deepcopy
from unittest.mock import patch

from entities.entites import GameListPydantic, GamePydantic, UserSessionPydantic
from entities.types import GameStatus, SessionStatus, SessionStatusStates
from flask import Response
from flask.testing import FlaskClient
from pytest_mock import MockFixture
from settings import PlayCredits
from tests.factories import GameFactory, UserFactory, UserSessionFactory
from tests.utils import user2pydantic
from use_cases.use_case import UserUseCase


def test_register_endpoint_not_allowed_methods(
    client: FlaskClient, jwt_token_headers: dict
) -> None:
    """
    Test session endpoint for not allowed methods.
    Expected: 405 status code
    """

    for method in ["GET", "PUT", "DELETE", "PATCH"]:
        client_method = getattr(client, method.lower())
        res: Response = client_method("/register", headers=jwt_token_headers)
        assert res.status_code == 405


def test_register(client: FlaskClient) -> None:
    """
    Test register endpoint. Expected: 200 status code
    and call to UserUseCase.create_or_400 method
    """

    with patch.object(UserUseCase, "create_or_400") as mock_create:
        mock_create.return_value = (None, 200)
        response: Response = client.post("/register", json={})  # noqa
        assert response.status_code == 200
        assert mock_create.called


def test_login_endpoint_not_allowed_methods(
    client: FlaskClient, jwt_token_headers: dict
) -> None:
    """
    Test session endpoint for not allowed methods.
    Expected: 405 status code
    """

    for method in ["GET", "PUT", "DELETE", "PATCH"]:
        client_method = getattr(client, method.lower())
        res: Response = client_method("/login", headers=jwt_token_headers)
        assert res.status_code == 405


def test_login_success(client: FlaskClient, mocker: "MockFixture") -> None:
    """
    Integration login endpoint test.
    Expected: 200 status code and access_token in response
    """

    user: UserFactory = UserFactory.create()
    mocker.patch("entities.models.User.filter_by", return_value=[user])
    data: dict = {"email": user.email, "password": user.password}
    response: Response = client.post("/login", json=data)  # noqa

    assert response.status_code == 200
    assert "access_token" in response.json


def test_login_failure(client: FlaskClient, mocker: "MockFixture") -> None:
    """
    Integration login endpoint test.
    Expected: 401 status code and error message in response
    """

    mocker.patch("entities.models.User.filter_by", return_value=[None])
    data: dict = {"email": "invalid", "password": "invalid"}
    response: Response = client.post("/login", json=data)  # noqa

    assert response.status_code == 401
    assert response.json == {"error": "User doesn't exists or password do not match"}


def test_account_detail_endpoint_not_allowed_methods(
    client: FlaskClient, jwt_token_headers: dict
) -> None:
    """
    Test session endpoint for not allowed methods.
    Expected: 405 status code
    """

    for method in ["POST", "PUT", "DELETE", "PATCH"]:
        client_method = getattr(client, method.lower())
        res: Response = client_method("/account", headers=jwt_token_headers)
        assert res.status_code == 405


def test_account_detail_endpoint(client: FlaskClient, jwt_token_headers: dict) -> None:
    """
    Test account detail endpoint.
    Expected: 200 status code and user data in response
    """

    user: UserFactory = UserFactory.create()
    response: Response = client.get("/account", headers=jwt_token_headers)  # noqa

    assert response.status_code == 200
    assert response.json == user2pydantic(user).dict(exclude={"password"})


def test_account_detail_endpoint_user_not_found(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """Test account detail endpoint. Expected: 404 status code"""

    mocker.patch("use_cases.use_case.UserUseCase.get_user", return_value=None)
    response: Response = client.get("/account", headers=jwt_token_headers)  # noqa

    assert response.status_code == 404


def test_account_update_endpoint_not_allowed_methods(
    client: FlaskClient, jwt_token_headers: dict
) -> None:
    """
    Test session endpoint for not allowed methods.
    Expected: 405 status code
    """

    for method in ["POST", "PUT", "DELETE", "GET"]:
        client_method = getattr(client, method.lower())
        res: Response = client_method("/account/update", headers=jwt_token_headers)
        assert res.status_code == 405


def test_account_update(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """Integration test for account update endpoint. Expected: 200 status code"""
    user: UserFactory = UserFactory.create(credits=0)
    mocker.patch("entities.models.User.filter_by", return_value=[user])
    user_updated: UserFactory = deepcopy(user)
    user_updated.credits = 10
    mocker.patch(
        "repos.db_repo.UserDBRepo.update_fields",
        return_value=user2pydantic(user_updated),
    )

    response: Response = client.patch(  # noqa
        "/account/update", json={"credits": 10}, headers=jwt_token_headers
    )
    data_response: dict = response.json

    assert response.status_code == 200
    assert data_response.pop("message") == "Account updated"
    assert data_response.get("credits") == 10
    assert data_response == user2pydantic(user_updated).dict(exclude={"password"})


def test_account_update_credits_count_invalid(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """
    Integration test for account update endpoint.
    Expected: 400 status code because of invalid credits count
    """
    user: UserFactory = UserFactory.create()
    mocker.patch("entities.models.User.filter_by", return_value=[user])
    mocker.patch(
        "repos.db_repo.UserDBRepo.update_fields", return_value=user2pydantic(user)
    )

    response: Response = client.patch(  # noqa
        "/account/update", json={"credits": 10}, headers=jwt_token_headers
    )
    data_response: dict = response.json

    assert response.status_code == 403
    assert (
        data_response.pop("error")
        == "Invalid credits count. Should be 0 before updating"
    )


def test_account_update_user_not_found(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """Integration test for account update endpoint. Expected: 404 status code"""
    mocker.patch("entities.models.User.filter_by", return_value=[None])
    response: Response = client.patch(  # noqa
        "/account/update", json={"credits": 10}, headers=jwt_token_headers
    )
    data_response: dict = response.json

    assert response.status_code == 404
    assert data_response.pop("error") == "User not found"


def test_session_endpoint_not_allowed_methods(
    client: FlaskClient, jwt_token_headers: dict
) -> None:
    """
    Test session endpoint for not allowed methods.
    Expected: 405 status code
    """

    for method in ["POST", "PUT", "DELETE", "PATCH"]:
        client_method = getattr(client, method.lower())
        res: Response = client_method("/session", headers=jwt_token_headers)
        assert res.status_code == 405


def test_session_create_session_active(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """
    Integration test for session create endpoint. Due to the fact
    that session is in active state, endpoint shouldn't create new one.
    Expected: 400 status code
    """
    user: UserFactory = UserFactory.create()
    user_session: UserSessionFactory = UserSessionFactory.create(
        status=SessionStatusStates.ACTIVE.value, user_id=user.id
    )
    game: GameFactory = GameFactory.create(session_id=user_session.id, user_id=user.id)
    game_pydantic: GameListPydantic = GameListPydantic(__root__=[game.__dict__])

    mocker.patch("entities.models.UserSession.filter_by", return_value=[user_session])
    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic)
    response: Response = client.get("/session", headers=jwt_token_headers)  # noqa

    data_response: dict = response.json
    games_response: list = data_response.get("session_detail").get("games")

    assert response.status_code == 400
    assert (
        data_response.get("error")
        == f"Session already started with id {user_session.id}"
    )
    assert games_response == [game_pydantic.__root__[0].dict(exclude={"board"})]
    assert data_response.get("session_detail").get("id") == user_session.id
    assert data_response.get("session_detail").get("status") == user_session.status


def test_session_create(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """
    Integration test for session create endpoint. Expected: 200 status code,
    new session created
    """
    user: UserFactory = UserFactory.create()
    user_session: UserSessionFactory = UserSessionFactory.create(
        status=SessionStatusStates.FINISHED.value, user_id=user.id
    )

    new_session: UserSessionFactory = UserSessionFactory.create()
    session_pydantic: UserSessionPydantic = UserSessionPydantic(**new_session.__dict__)

    game: GameFactory = GameFactory.create(session_id=user_session.id, user_id=user.id)
    game_pydantic: GamePydantic = GamePydantic(**game.__dict__)

    mocker.patch("entities.models.User.filter_by", return_value=[user])
    mocker.patch("entities.models.UserSession.filter_by", return_value=None)
    mocker.patch(
        "repos.db_repo.UserSessionDBRepo.create", return_value=session_pydantic
    )
    mocker.patch("repos.db_repo.GameDBRepo.create", return_value=game_pydantic)

    user_updated: UserFactory = deepcopy(user)
    user_updated.credits -= PlayCredits.PLAY.value

    mocker.patch(
        "repos.db_repo.UserDBRepo.update_fields", return_value=user2pydantic(user)
    )

    response: Response = client.get("/session", headers=jwt_token_headers)  # noqa
    data_response: dict = response.json

    assert response.status_code == 200
    assert data_response.get("message") == "Game session started"
    assert data_response.get("game_id") == game.id
    assert data_response.get("score") == session_pydantic.score
    assert data_response.get("status") == session_pydantic.status
    assert data_response.get("user_id") == user.id


def test_new_game_endpoint_not_allowed_methods(
    client: FlaskClient, jwt_token_headers: dict
) -> None:
    """
    Test new game endpoint for not allowed methods.
    Expected: 405 status code
    """

    for method in ["POST", "PUT", "DELETE", "PATCH"]:
        client_method = getattr(client, method.lower())
        res: Response = client_method("/session/1/game", headers=jwt_token_headers)
        assert res.status_code == 405


def test_new_game_endpoint_no_active_session(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """
    Integration test for new game endpoint. Case: active session not found on DB.
    Expected: 400 status code
    """
    user: UserFactory = UserFactory.create()
    mocker.patch("entities.models.User.filter_by", return_value=[user])
    mocker.patch("entities.models.UserSession.filter_by", return_value=None)

    response: Response = client.get(  # noqa
        "/session/1/game", headers=jwt_token_headers
    )
    data_response: dict = response.json

    assert response.status_code == 400
    assert data_response.get("error") == "No active session found"


def test_new_game_endpoint_game_already_started(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """
    Integration test for new game endpoint. Case: there is active game in DB,
    so we can't start new one. Expected: 400 status code
    """
    user: UserFactory = UserFactory.create()
    user_session: UserSessionFactory = UserSessionFactory.create(
        status=SessionStatusStates.ACTIVE.value, user_id=user.id
    )
    game: GameFactory = GameFactory.create(
        session_id=user_session.id, user_id=user.id, status=GameStatus.IN_PROGRESS.value
    )
    game_pydantic: GameListPydantic = GameListPydantic(__root__=[game.__dict__])

    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic)
    mocker.patch("entities.models.UserSession.filter_by", return_value=[user_session])
    mocker.patch("entities.models.User.filter_by", return_value=[user])

    response: Response = client.get(  # noqa
        "/session/1/game", headers=jwt_token_headers
    )
    data_response: dict = response.json

    assert response.status_code == 400
    assert data_response.get("error") == "Game already started"
    assert data_response.get("game_id") == game.id
    assert data_response.get("session_id") == user_session.id


def test_new_game_endpoint_session_finished(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """
    Integration test for new game endpoint. Case: session is not active,
    so we can't start new game. Expected: 400 status code
    """
    user: UserFactory = UserFactory.create()
    user_session: UserSessionFactory = UserSessionFactory.create(
        status=SessionStatusStates.FINISHED.value, user_id=user.id
    )

    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=None)
    mocker.patch("entities.models.UserSession.filter_by", return_value=[user_session])
    mocker.patch("entities.models.User.filter_by", return_value=[user])

    response: Response = client.get(  # noqa
        "/session/1/game", headers=jwt_token_headers
    )
    data_response: dict = response.json

    assert response.status_code == 400
    assert data_response.get("error") == "Session already finished"


def test_new_game_endpoint_no_credits(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """
    Integration test for new game endpoint. Case: user has no credits,
    so we can't start new game. Expected: 400 status code
    """
    user: UserFactory = UserFactory.create(credits=0)
    user_session: UserSessionFactory = UserSessionFactory.create(
        status=SessionStatusStates.ACTIVE.value, user_id=user.id
    )

    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=None)
    mocker.patch("entities.models.UserSession.filter_by", return_value=[user_session])
    mocker.patch("entities.models.User.filter_by", return_value=[user])
    mocker.patch(
        "use_cases.use_case.UserUseCase.update_session_status", return_value=[user]
    )

    response: Response = client.get(  # noqa
        "/session/1/game", headers=jwt_token_headers
    )
    data_response: dict = response.json

    assert response.status_code == 400
    assert data_response.get("error") == "Not enough credits. Game cannot start"


def test_new_game_endpoint_valid_game(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """
    Integration test for new game endpoint. Expected: 200 status code,
    new game started
    """
    user: UserFactory = UserFactory.create()
    user_session: UserSessionFactory = UserSessionFactory.create(
        status=SessionStatusStates.ACTIVE.value, user_id=user.id
    )

    game: GameFactory = GameFactory.create(
        session_id=user_session.id, user_id=user.id, status=GameStatus.IN_PROGRESS.value
    )
    game_pydantic: GamePydantic = GamePydantic(**game.__dict__)

    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=None)
    mocker.patch("entities.models.UserSession.filter_by", return_value=[user_session])
    mocker.patch("entities.models.User.filter_by", return_value=[user])
    mocker.patch(
        "repos.db_repo.UserDBRepo.update_fields", return_value=user2pydantic(user)
    )
    mocker.patch("repos.db_repo.GameDBRepo.create", return_value=game_pydantic)

    response: Response = client.get(  # noqa
        "/session/1/game", headers=jwt_token_headers
    )
    data_response: dict = response.json

    assert response.status_code == 200
    assert isinstance(data_response.get("game_details"), dict)
    assert data_response.get("game_details").get("id") == game.id
    assert data_response.get("game_details").get("user_id") == game.user_id
    assert data_response.get("game_details").get("session_id") == game.session_id
    assert data_response.get("game_details").get("status") == game.status


def test_play_start_endpoint_method_not_allowed(
    client: FlaskClient, jwt_token_headers: dict
) -> None:
    """
    Test play start endpoint for not allowed methods.
    Expected: 405 status code
    """

    for method in ["PUT", "DELETE", "PATCH"]:
        client_method = getattr(client, method.lower())
        res: Response = client_method("/session/1/game/1", headers=jwt_token_headers)
        assert res.status_code == 405


def test_play_start_endpoint_game_not_found2(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """Test for play start endpoint. with session status not active"""
    session_status: SessionStatus = SessionStatus(False, {"test": "test"}, 200)
    mocker.patch(
        "use_cases.use_case.UserUseCase.check_session_status",
        return_value=session_status,
    )
    response: Response = client.get(  # noqa
        "/session/1/game/1", json={}, headers=jwt_token_headers
    )

    assert response.status_code == session_status.status_code
    assert response.json == session_status.session_data


def test_play_start_endpoint_GET(
    client: FlaskClient, jwt_token_headers: dict, mocker: "MockFixture"
) -> None:
    """Test for play start endpoint. GET method should return board details"""
    user: UserFactory = UserFactory.create()
    user_session: UserSessionFactory = UserSessionFactory.create(
        status=SessionStatusStates.ACTIVE.value, user_id=user.id
    )
    game: GameFactory = GameFactory.create(
        session_id=user_session.id, user_id=user.id, status=GameStatus.IN_PROGRESS.value
    )
    session_status: SessionStatus = SessionStatus(True, {"test": "test"}, 200)
    mocker.patch(
        "use_cases.use_case.UserUseCase.check_session_status",
        return_value=session_status,
    )
    mocker.patch(
        "use_cases.use_case.UserUseCase.check_game_status", return_value=(False, "test")
    )

    expected_response: dict = {
        "actual_board": game.board,
        "player_sign": game.symbol,
    }

    mocker.patch(
        "use_cases.use_case.UserUseCase.lets_play_GET",
        return_value=(expected_response, 200),
    )
    response: Response = client.get(  # noqa
        "/session/1/game/1", json={}, headers=jwt_token_headers
    )

    assert response.status_code == 200
    assert response.json == expected_response


# def test_play_start_endpoint_POST(
#         client: FlaskClient,
#         jwt_token_headers: dict,
#         mocker: "MockFixture",
#         mock_session_status_response
# ) -> None:
#     """Test for play start endpoint. GET method should return board details"""
#     user: UserFactory = UserFactory.create()
#     user_session: UserSessionFactory = UserSessionFactory.create(
#         status=SessionStatusStates.ACTIVE.value, user_id=user.id
#     )
#     game: GameFactory = GameFactory.create(
#         session_id=user_session.id,
#         user_id=user.id,
#         status=GameStatus.IN_PROGRESS.value
#     )
#     session_status: SessionStatus = SessionStatus(True, {"test": "test"}, 200)
#     mocker.patch(
#     "use_cases.use_case.UserUseCase.check_session_status",
#     return_value=session_status
#     )
#
#     expected_response: dict = {
#         "actual board": game.board,
#         "player sign": game.symbol,
#     }
#
#     mocker.patch(
#     "use_cases.use_case.UserUseCase.lets_play_GET",
#     return_value=(expected_response, 200)
#     )
#     response: Response = client.get(  # noqa
#     f"/session/1/game/1", json={}, headers=jwt_token_headers
#     )
#
#     assert response.status_code == 200
#     assert response.json == expected_response
