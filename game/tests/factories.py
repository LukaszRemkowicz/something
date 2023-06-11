import datetime
from typing import Dict, List

import factory
from entities.models import Game, User, UserSession
from entities.types import SessionStatusStates
from pytest_factoryboy import register


@register
class UserFactory(factory.Factory):
    id: int = 1
    password: str = "123"
    email: str = "test_email@test_email"
    credits: int = 10

    class Meta:
        model = User


@register
class UserSessionFactory(factory.Factory):
    id: int = 1
    score: int = 0
    user_id: int = 1
    status: str = SessionStatusStates.NEW.value
    created_at: datetime = datetime.datetime.strptime(
        "2021-09-01 00:00:00", "%Y-%m-%d %H:%M:%S"
    ).date()
    ended_at: datetime = datetime.datetime.strptime(
        "2021-09-01 00:00:10", "%Y-%m-%d %H:%M:%S"
    ).date()
    user: User = factory.SubFactory(UserFactory)

    class Meta:
        model = UserSession


@register
class GameFactory(factory.Factory):
    id: int = 1
    user_id: int = 1
    symbol: str = "X"
    status: str = "not_started"
    session_id: int = 1
    board: Dict[str, List[List[str | None]]] = {
        "board": [[None, None, None] for _ in range(3)]
    }
    user: User = factory.SubFactory(UserFactory)
    session: UserSession = factory.SubFactory(UserSessionFactory)

    class Meta:
        model = Game
