from typing import Type, Tuple

from entities.entites import UserListPydantic, UserPydantic, UserSessionPydantic, GamePydantic
from entities.types import SessionStatus
from repos.db_repo import UserDBRepo, UserSessionDBRepo, GameDBRepo
from repos.managers import GridManager


class UserUseCase:
    def __init__(
            self,
            db_repo: Type[UserDBRepo],
            user_session_repo: Type[UserSessionDBRepo],
            game_db_repo: Type[GameDBRepo]
    ):
        self.db_repo: UserDBRepo = db_repo()
        self.user_session_repo: UserSessionDBRepo = user_session_repo()
        self.grid_manager: GridManager = GridManager()
        self.game_db_repo: GameDBRepo = game_db_repo()

    def create_or_400(self, player_data: dict) -> Tuple[dict, int]:
        """Create new user or return 400 if user already exists."""
        user_obj: UserPydantic | None = self.get_user(email=player_data.get('email'))
        if user_obj:
            return {"error": "User already exists"}, 400

        result: UserPydantic = self.db_repo.create(**player_data)
        return result.dict(), 201

    def get_user(self, **kwargs) -> UserPydantic | None:
        user_obj: UserListPydantic | None = self.db_repo.filter(**kwargs)
        if user_obj and user_obj.__root__:
            return user_obj.__root__[0]
        return None

    def update_user_account(self, user_id: int, **kwargs):
        """Update user account."""
        user: UserPydantic | None = self.get_user(id=user_id)
        message: str

        if user:
            if kwargs.get('credits') and user.credits != 0:
                message = 'Invalid credits count. Should be 0 before updating'
                return {"message": message}, 400
            result: UserPydantic | None = self.db_repo.update_fields(obj=user, **kwargs)
            if result:
                result_dict: dict = result.dict()
                result_dict.pop('password')
                result_dict.update({"message": "Account updated"})
                return result_dict, 200

        message = "User not found"
        return {"message": message}, 404

    def start_session(self, user_id: int):
        """Start new game session."""
        user: UserPydantic | None = self.get_user(id=user_id)

        if user.credits < 3:
            return {'message': 'Not enough credits'}, 400

        user.credits -= 3
        self.db_repo.update_fields(obj=user, credits=user.credits)
        user_session: UserSessionPydantic = self.user_session_repo.create(user_id=user.id)

        result: dict = user_session.dict()
        result.update({'message': 'Game session started'})
        return result, 200

    def get_session_object(self, session_id: int, user_id: int):
        session: UserSessionPydantic | None = self.user_session_repo.filter(
            id=session_id, user_id=user_id
        )
        if session:
            return session
        return None

    def lets_play_POST(self, session_id: int, user_id: int, **kwargs):
        session: UserSessionPydantic | None = self.get_session_object(session_id, user_id)
        user: UserPydantic | None = self.get_user(id=user_id)

        if 0 < user.credits < 3:
            session.is_finished = True
            self.user_session_repo.update_fields(obj=session, is_finished=True)
            return {'message': 'Not enough credits'}, 400

        game_board = self.grid_manager.get_grid()


    def lets_play_GET(self):
        ...

    def check_session_status(self, session_id: int, user_id: int):
        session: UserSessionPydantic | None = self.get_session_object(session_id, user_id)
        if not session:
            return SessionStatus(False, {'message': 'Game session not found for requested user'}, 404)

        if session.is_finished:
            return SessionStatus(False, {'message': 'Game session is finished'}, 400)

        return SessionStatus(True, session.dict(), 200)
