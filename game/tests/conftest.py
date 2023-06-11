import pytest
from app import app as flask_app
from entities.entites import GameListPydantic, UserPydantic, UserSessionListPydantic
from entities.types import SessionStatus
from flask import Response
from flask.testing import FlaskClient
from pytest_mock import MockFixture
from repos.db_repo import GameDBRepo, UserDBRepo, UserSessionDBRepo
from tests.factories import GameFactory, UserFactory, UserSessionFactory
from tests.utils import game2pydantic_list, user2pydantic, user_session2pydantic_list
from use_cases.use_case import UserUseCase


@pytest.fixture
def client():
    with flask_app.test_client() as client:
        with flask_app.app_context():
            flask_app.config["DEBUG"] = True
            yield client


@pytest.fixture
def jwt_token_headers(client: FlaskClient, mocker: "MockFixture"):
    user: UserFactory = UserFactory.create()
    mocker.patch("entities.models.User.filter_by", return_value=[user])
    data: dict = {"email": user.email, "password": user.password}
    response: Response = client.post("/login", json=data)  # noqa
    return {
        "Authorization": f"Bearer {response.json['access_token']}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def mock_session_status_response(mocker: "MockFixture"):
    session_status: SessionStatus = SessionStatus(True, {"test": "test"}, 200)
    mocker.patch(
        "use_cases.use_case.UserUseCase.check_session_status",
        return_value=session_status,
    )


@pytest.fixture
def use_case():
    """Return UserUseCase instance"""

    return UserUseCase(
        db_repo=UserDBRepo, user_session_repo=UserSessionDBRepo, game_db_repo=GameDBRepo
    )


@pytest.fixture
def trio_objects_package():
    """Return trio objects"""
    user: UserFactory = UserFactory.create(credits=0)
    user_pydantic: UserPydantic = user2pydantic(user)

    user_session: UserSessionFactory = UserSessionFactory.create(user_id=user.id)
    user_session_pydantic: UserSessionListPydantic = user_session2pydantic_list(
        user_session
    )

    game: GameFactory = GameFactory.create(session_id=user_session.id)
    game_pydantic_list: GameListPydantic = game2pydantic_list(game)

    return user_pydantic, user_session_pydantic, game_pydantic_list
