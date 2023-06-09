from typing import Dict, List

import factory
from pytest_factoryboy import register

from entities.models import Game, User, UserSession
from entities.types import SessionStatusStates


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

    class Meta:
        model = UserSession


@register
class GameFactory(factory.Factory):
    id: int = 1
    user_id: int = 1
    symbol: str = "X"
    status: str = "not_started"
    board: Dict[str, List[List[str | None]]] = {
        "board": [[None, None, None] for _ in range(3)]
    }

    class Meta:
        model = Game
