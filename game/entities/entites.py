from datetime import date
from typing import Optional

from pydantic import BaseModel


class UserPydantic(BaseModel):
    id: int
    password: str
    email: str
    credits: int


class UserListPydantic(BaseModel):
    __root__: list[UserPydantic]


class UserSessionPydantic(BaseModel):
    id: int
    score: Optional[int]
    user_id: int
    status: str
    ended_at: Optional[date] = None


class UserSessionListPydantic(BaseModel):
    __root__: list[UserSessionPydantic]


class GamePydantic(BaseModel):
    id: int
    board: dict
    user_id: int
    symbol: str
    winner: Optional[int]
    session_id: int
    status: str


class GameListPydantic(BaseModel):
    __root__: list[GamePydantic]


class ScorePydantic(BaseModel):
    score: str
    user_name: str
    time_played: int | str


class ScoreListPydantic(BaseModel):
    __root__: list[ScorePydantic]
