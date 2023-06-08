import pytest
from flask import Response
from flask.testing import FlaskClient
from pytest_mock import MockFixture

from app import app as flask_app
from entities.types import SessionStatus
from tests.factories import UserFactory


@pytest.fixture
def client():
    with flask_app.test_client() as client:
        with flask_app.app_context():
            flask_app.config['DEBUG'] = True
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
    mocker.patch("use_cases.use_case.UserUseCase.check_session_status", return_value=session_status)
