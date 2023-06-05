from typing import Optional, List

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
    score: Optional[str]
    user_id: str
    is_finished: bool = False


class UserSessionListPydantic(BaseModel):
    __root__: list[UserSessionPydantic]


class GamePydantic(BaseModel):
    id: int
    board: List
    user_id: int
    current_player: str
    winner: Optional[int]


class GameListPydantic(BaseModel):
    __root__: list[GamePydantic]

