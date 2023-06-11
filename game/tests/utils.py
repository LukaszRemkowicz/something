from entities.entites import (
    GameListPydantic,
    GamePydantic,
    UserListPydantic,
    UserPydantic,
    UserSessionListPydantic,
    UserSessionPydantic,
)
from entities.models import Game, User, UserSession
from tests.factories import GameFactory, UserFactory, UserSessionFactory


def user2pydantic(user: User | UserFactory) -> UserPydantic:
    """Convert User model instance to UserPydantic instance"""
    return UserPydantic(**user.__dict__)


def user2pydantic_list(user: User | UserFactory) -> UserListPydantic:
    """Convert User model instance to UserPydantic instance"""
    return UserListPydantic(__root__=[user.__dict__])


def user_session2pydantic(
    user_session: UserSession | UserSessionFactory,
) -> UserSessionPydantic:
    """Convert User model instance to UserPydantic instance"""
    return UserSessionPydantic(**user_session.__dict__)


def user_session2pydantic_list(
    user_session: UserSession | UserSessionFactory,
) -> UserSessionListPydantic:
    """Convert User model instance to UserPydantic instance"""
    return UserSessionListPydantic(__root__=[user_session.__dict__])


def game2pydantic(game: Game | GameFactory) -> GamePydantic:
    """Convert Game model instance to GamePydantic instance"""
    return GamePydantic(**game.__dict__)


def game2pydantic_list(game: Game | GameFactory) -> GameListPydantic:
    """Convert Game model instance to GamePydantic instance"""
    return GameListPydantic(__root__=[game.__dict__])
