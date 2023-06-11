from copy import deepcopy
from typing import Iterable, Optional
from unittest.mock import patch

from entities.entites import (
    GameListPydantic,
    GamePydantic,
    UserListPydantic,
    UserPydantic,
    UserSessionListPydantic,
    UserSessionPydantic,
)
from entities.models import Game, User, UserSession
from entities.types import SessionStatusStates
from pytest_mock import MockerFixture
from repos.db_repo import GameDBRepo, UserDBRepo, UserSessionDBRepo
from tests.factories import GameFactory, UserFactory, UserSessionFactory
from tests.utils import game2pydantic_list, user2pydantic, user_session2pydantic_list


def test_user_db_repo_filter(mocker: "MockerFixture"):
    """Test UserDBRepo.filter method. Expect to return UserListPydantic instance"""

    user: UserFactory = UserFactory.create()
    repo: UserDBRepo = UserDBRepo()
    mocker.patch("entities.models.User.filter_by", return_value=[user])
    res: Optional[UserListPydantic] = repo.filter(
        email=user.email, password=user.password
    )

    assert isinstance(res, UserListPydantic)
    assert res.__root__[0].email == user.email


def test_user_db_repo_filter_no_return(mocker: "MockerFixture"):
    """Test UserDBRepo.filter method. Expect to return None"""

    user: UserFactory = UserFactory.create()
    repo: UserDBRepo = UserDBRepo()
    mocker.patch("entities.models.User.filter_by", return_value=None)
    res: Optional[UserListPydantic] = repo.filter(
        email=user.email, password=user.password
    )

    assert not res


def test_user_db_repo_create(mocker: "MockerFixture"):
    """Test UserDBRepo.create method. Expect to return UserPydantic instance"""

    user: UserFactory = UserFactory.create()
    repo: UserDBRepo = UserDBRepo()
    mocker.patch("entities.models.User.create", return_value=user)
    mocker.patch("entities.models.User.filter_by", return_value=[user])

    res: UserPydantic = repo.create(**user.__dict__)
    assert isinstance(res, UserPydantic)
    assert res.email == user.email
    assert res.password == user.password


def test_user_db_repo_save() -> None:
    """Test UserDBRepo.create method. Expect to call User.save method"""

    user: UserFactory = UserFactory.create()
    repo: UserDBRepo = UserDBRepo()

    with patch.object(User, "save", return_value=user) as mock_method:
        repo.save(user)
        mock_method.assert_called_once()


@patch("flask_sqlalchemy.model._QueryProperty.__get__")
def test_user_db_repo_update_fields(mocked_method):
    """Test UserDBRepo.update_fields method. Expect to change instance attributes"""

    user: UserFactory = UserFactory.create()
    deep_copy_user = deepcopy(user)
    params_to_update = {
        "password": "new_password",
        "email": "new_email",
    }

    class MockRefresh:
        def __call__(self, instance):
            """Update instance attributes"""
            instance.password = params_to_update["password"]
            instance.email = params_to_update["email"]

    with patch("repos.db_repo.db.session.refresh", side_effect=MockRefresh()), patch(
        "repos.db_repo.db.session.commit"
    ):
        repo: UserDBRepo = UserDBRepo()
        filter_by_mock = mocked_method.return_value.filter_by
        filter_by_mock.return_value.first.return_value = user
        user_pydantic: UserPydantic = user2pydantic(user)
        res = repo.update_fields(
            user_pydantic,
            password=params_to_update["password"],
            email=params_to_update["email"],
        )

        assert isinstance(res, UserPydantic)
        assert res.password == params_to_update["password"]
        assert res.email == params_to_update["email"]
        assert res.email != deep_copy_user.email
        assert res.password != deep_copy_user.password


@patch("flask_sqlalchemy.model._QueryProperty.__get__")
def test_user_db_repo_update_fields_no_return(mocked_method):
    """Test UserDBRepo.update_fields method. Expect to return None"""

    user: UserFactory = UserFactory.create()
    params_to_update = {
        "password": "new_password",
        "email": "new_email",
    }

    class MockRefresh:
        def __call__(self, instance):
            """Update instance attributes"""
            instance.password = params_to_update["password"]
            instance.email = params_to_update["email"]

    with patch("repos.db_repo.db.session.refresh", side_effect=MockRefresh()), patch(
        "repos.db_repo.db.session.commit"
    ):
        repo: UserDBRepo = UserDBRepo()
        filter_by_mock = mocked_method.return_value.filter_by
        filter_by_mock.return_value.first.return_value = None
        user_pydantic: UserPydantic = user2pydantic(user)
        res = repo.update_fields(user_pydantic, password=params_to_update["password"])

        assert not res


def test_user_session_db_repo_filter(mocker: "MockerFixture"):
    """
    Test UserSessionDBRepo.filter method.
    Expect to return UserSessionListPydantic instance
    """

    user_session: UserSessionFactory = UserSessionFactory.create()
    repo: UserSessionDBRepo = UserSessionDBRepo()
    mocker.patch("entities.models.UserSession.filter_by", return_value=[user_session])
    res: Optional[UserSessionListPydantic] = repo.filter(
        user_id=user_session.id, status=SessionStatusStates.ACTIVE.value
    )

    assert isinstance(res, UserSessionListPydantic)
    assert res.__root__[0].user_id == user_session.id


def test_user_session_db_repo_filter_no_instance(mocker: "MockerFixture"):
    """Test UserSessionDBRepo.filter method. Expect to return None"""

    user_session: UserSessionFactory = UserSessionFactory.create()
    repo: UserSessionDBRepo = UserSessionDBRepo()
    mocker.patch("entities.models.UserSession.filter_by", return_value=None)
    res: Optional[UserSessionListPydantic] = repo.filter(
        user_id=user_session.id, status=SessionStatusStates.ACTIVE.value
    )

    assert not res


def test_user_session_db_repo_create(mocker: "MockerFixture"):
    """
    Test UserSessionDBRepo.create method.
    Expect to return UserSessionPydantic instance
    """

    user_session: UserSessionFactory = UserSessionFactory.create()
    repo: UserSessionDBRepo = UserSessionDBRepo()

    user_session_pydantic: UserSessionListPydantic = user_session2pydantic_list(
        user_session
    )

    mocker.patch("entities.models.UserSession.create", return_value=None)
    mocker.patch(
        "repos.db_repo.UserSessionDBRepo.filter", return_value=user_session_pydantic
    )

    res: UserSessionPydantic = repo.create(**user_session.__dict__)
    assert isinstance(res, UserSessionPydantic)
    assert res.user_id == user_session.id


def test_user_session_db_repo_save() -> None:
    """Test UserSessionDBRepo.create method. Expect to call UserSession.save method"""

    user_session: UserSessionFactory = UserSessionFactory.create()
    repo: UserSessionDBRepo = UserSessionDBRepo()

    with patch.object(UserSession, "save", return_value=user_session) as mock_method:
        repo.save(user_session)
        mock_method.assert_called_once()


@patch("flask_sqlalchemy.model._QueryProperty.__get__")
def test_user_session_db_repo_update_fields(mocked_method):
    """
    Test UserSessionDBRepo.update_fields method.
    Expect to return UserSessionPydantic
    """
    user: UserFactory = UserFactory.create()
    user_session: UserSessionFactory = UserSessionFactory.create(user=user)

    new_user_dict: dict = {
        key: val
        for key, val in user_session.__dict__.items()
        if not key.startswith("_")
    }
    new_user_dict.pop("user")
    deep_copy_user = UserSessionFactory.create(**new_user_dict, user=user)

    params_to_update = {
        "status": SessionStatusStates.FINISHED.value,
        "score": 100,
    }

    class MockRefresh:
        def __call__(self, instance):
            """Update instance attributes"""
            instance.score = params_to_update["score"]
            instance.status = params_to_update["status"]

    with patch("repos.db_repo.db.session.refresh", side_effect=MockRefresh()), patch(
        "repos.db_repo.db.session.commit"
    ):
        repo: UserSessionDBRepo = UserSessionDBRepo()
        filter_by_mock = mocked_method.return_value.filter_by
        filter_by_mock.return_value.first.return_value = user_session
        user_session_pydantic: UserSessionPydantic = user_session2pydantic_list(
            user_session
        ).__root__[0]
        res = repo.update_fields(
            user_session_pydantic,
            score=params_to_update["score"],
            status=params_to_update["status"],
        )

        assert isinstance(res, UserSessionPydantic)
        assert res.score == params_to_update["score"]
        assert res.status == params_to_update["status"]
        assert res.score != deep_copy_user.score
        assert res.status != deep_copy_user.status


@patch("flask_sqlalchemy.model._QueryProperty.__get__")
def test_user_session_db_repo_update_fields_no_return(mocked_method):
    """Test UserSessionDBRepo.update_fields method. Expect to return None"""

    user_session: UserSessionFactory = UserSessionFactory.create()
    params_to_update = {
        "status": SessionStatusStates.FINISHED.value,
        "score": 100,
    }

    class MockRefresh:
        def __call__(self, instance):
            """Update instance attributes"""
            instance.score = params_to_update["score"]
            instance.status = params_to_update["status"]

    with patch("repos.db_repo.db.session.refresh", side_effect=MockRefresh()), patch(
        "repos.db_repo.db.session.commit"
    ):
        repo: UserSessionDBRepo = UserSessionDBRepo()
        filter_by_mock = mocked_method.return_value.filter_by
        filter_by_mock.return_value.first.return_value = None
        user_session_pydantic: UserSessionPydantic = user_session2pydantic_list(
            user_session
        ).__root__[0]
        res = repo.update_fields(
            user_session_pydantic,
            score=params_to_update["score"],
            status=params_to_update["status"],
        )

        assert not res


@patch("flask_sqlalchemy.model._QueryProperty.__get__")
def test_user_session_db_repo_all(mocked_method):
    """Test UserSessionDBRepo.all method. Expect to return list of UserSession objects"""

    user_session: UserSessionFactory = UserSessionFactory.create()
    repo: UserSessionDBRepo = UserSessionDBRepo()

    filter_by_mock = mocked_method.return_value.order_by
    filter_by_mock.return_value.all.return_value = [user_session]

    res: Iterable = repo.all(desc=True)

    assert res
    assert isinstance(res, list)
    assert isinstance(res[0], UserSession)


@patch("flask_sqlalchemy.model._QueryProperty.__get__")
def test_user_session_db_repo_all_no_desc(mocked_method):
    """
    Test UserSessionDBRepo.all method.
    Expect to return UserSessionListPydantic instance
    """

    user_session: UserSessionFactory = UserSessionFactory.create()
    repo: UserSessionDBRepo = UserSessionDBRepo()

    filter_by_mock = mocked_method.return_value.all
    filter_by_mock.return_value = [user_session]

    res: Iterable = repo.all()

    assert res
    assert isinstance(res, list)
    assert isinstance(res[0], UserSession)


@patch("flask_sqlalchemy.model._QueryProperty.__get__")
def test_game_db_repo_filter(mocked_method) -> None:
    """
    Test UserSessionDBRepo.get_score method.
    Expect to return GameListPydantic instance
    """
    repo: GameDBRepo = GameDBRepo()
    game: GameFactory = GameFactory.create()

    filter_by_mock = mocked_method.return_value.filter
    filter_by_mock.return_value.all.return_value = [game]

    res: GameListPydantic = repo.filter(user_id=1)

    assert isinstance(res, GameListPydantic)
    assert res.__root__[0].board == game.board


@patch("flask_sqlalchemy.model._QueryProperty.__get__")
def test_game_db_repo_filter_no_return(mocked_method) -> None:
    """Test UserSessionDBRepo.get_score method. Expect no return"""
    repo: GameDBRepo = GameDBRepo()

    filter_by_mock = mocked_method.return_value.filter
    filter_by_mock.return_value.all.return_value = None

    res: GameListPydantic = repo.filter(user_id=1)

    assert not res


def test_game_db_repo_create(mocker: "MockerFixture") -> None:
    """Test GameDBRepo.create method. Expect to return Game object"""
    repo: GameDBRepo = GameDBRepo()
    game: GameFactory = GameFactory.create()

    game_pydantic: GameListPydantic = game2pydantic_list(game)

    mocker.patch("entities.models.Game.create", return_value=None)
    mocker.patch("repos.db_repo.GameDBRepo.filter", return_value=game_pydantic)

    res: GamePydantic = repo.create(**game.__dict__)

    assert isinstance(res, GamePydantic)
    assert res.board == game.board
    assert res.user_id == game.user_id


def test_game_db_repo_save() -> None:
    """Test GameDBRepo.create method. Expect to call Game.save method"""

    repo: GameDBRepo = GameDBRepo()
    game: GameFactory = GameFactory.create()

    with patch.object(Game, "save", return_value=game) as mock_method:
        repo.save(game)
        mock_method.assert_called_once()


@patch("flask_sqlalchemy.model._QueryProperty.__get__")
def test_game_db_repo_update_fields(mocked_method):
    """
    Test GameDBRepo.update_fields method.
    Expect to return UserSessionPydantic
    """

    user: UserFactory = UserFactory.create()
    user_session: UserSessionFactory = UserSessionFactory.create(user=user)
    game: GameFactory = GameFactory.create(user=user, session=user_session)

    game_deep_copy_dict: dict = {
        key: val for key, val in game.__dict__.items() if not key.startswith("_")
    }
    game_deep_copy_dict.pop("user")
    game_deep_copy_dict.pop("session")

    deep_copy_user = GameFactory.create(
        **game_deep_copy_dict, user=user, session=user_session
    )

    params_to_update = {"winner": True, "symbol": "X" if game.symbol == "O" else "O"}

    class MockRefresh:
        def __call__(self, instance):
            """Update instance attributes"""
            instance.winner = params_to_update["winner"]
            instance.symbol = params_to_update["symbol"]

    with patch("repos.db_repo.db.session.refresh", side_effect=MockRefresh()), patch(
        "repos.db_repo.db.session.commit"
    ):
        repo: GameDBRepo = GameDBRepo()
        filter_by_mock = mocked_method.return_value.filter_by
        filter_by_mock.return_value.first.return_value = game
        game_pydantic: GamePydantic = game2pydantic_list(game).__root__[0]
        res = repo.update_fields(
            game_pydantic,
            winner=params_to_update["winner"],
            symbol=params_to_update["symbol"],
        )
        assert isinstance(res, GamePydantic)
        assert res.winner == params_to_update["winner"]
        assert res.symbol == params_to_update["symbol"]
        assert res.symbol != deep_copy_user.symbol
        assert res.winner != deep_copy_user.winner


@patch("flask_sqlalchemy.model._QueryProperty.__get__")
def test_game_db_repo_update_fields_no_return(mocked_method):
    """Test GameDBRepo.update_fields method. Expect return None"""

    user: UserFactory = UserFactory.create()
    user_session: UserSessionFactory = UserSessionFactory.create(user=user)
    game: GameFactory = GameFactory.create(user=user, session=user_session)

    params_to_update = {"winner": True, "symbol": "X" if game.symbol == "O" else "O"}

    class MockRefresh:
        def __call__(self, instance):
            """Update instance attributes"""
            instance.winner = params_to_update["winner"]
            instance.symbol = params_to_update["symbol"]

    with patch("repos.db_repo.db.session.refresh", side_effect=MockRefresh()), patch(
        "repos.db_repo.db.session.commit"
    ):
        repo: GameDBRepo = GameDBRepo()
        filter_by_mock = mocked_method.return_value.filter_by
        filter_by_mock.return_value.first.return_value = None
        game_pydantic: GamePydantic = game2pydantic_list(game).__root__[0]
        res = repo.update_fields(
            game_pydantic,
            winner=params_to_update["winner"],
            symbol=params_to_update["symbol"],
        )
        assert not res
