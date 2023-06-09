import random
from datetime import datetime
from typing import List, Optional, Tuple, Type

from entities.entites import (
    GameListPydantic,
    GamePydantic,
    UserListPydantic,
    UserPydantic,
    UserSessionListPydantic,
    UserSessionPydantic,
)
from entities.types import GameStatus, SessionStatus, SessionStatusStates
from repos.db_repo import GameDBRepo, UserDBRepo, UserSessionDBRepo
from repos.managers import GridManager
from settings import PlayCredits
from utils.exceptions import NoGameFoundException


class UserUseCase:
    def __init__(
        self,
        db_repo: Type[UserDBRepo],
        user_session_repo: Type[UserSessionDBRepo],
        game_db_repo: Type[GameDBRepo],
    ):
        self.db_repo: UserDBRepo = db_repo()
        self.user_session_repo: UserSessionDBRepo = user_session_repo()
        self.grid_manager: Type[GridManager] = GridManager
        self.game_db_repo: GameDBRepo = game_db_repo()

    def create_or_400(self, player_data: dict) -> Tuple[dict, int]:
        """Create new user or return 400 if user already exists."""
        user_obj: UserPydantic | None = self.get_user(email=player_data.get("email"))
        if user_obj:
            return {"error": "User already exists"}, 400

        result: UserPydantic = self.db_repo.create(**player_data)
        return result.dict(), 201

    def get_user(self, **kwargs) -> UserPydantic | None:
        """Get user from DB."""
        user_obj: UserListPydantic | None = self.db_repo.filter(**kwargs)
        if user_obj and user_obj.__root__:
            return user_obj.__root__[0]
        return None

    def update_user_account(self, user_id: int, **kwargs) -> Tuple[dict, int]:
        """Update user account."""
        user: UserPydantic | None = self.get_user(id=user_id)
        message: str

        if user:
            if kwargs.get("credits") and user.credits != 0:
                message = "Invalid credits count. Should be 0 before updating"
                return {"message": message}, 400
            result: UserPydantic | None = self.db_repo.update_fields(obj=user, **kwargs)
            if result:
                result_dict: dict = result.dict(exclude={"password"})
                result_dict.update({"message": "Account updated"})
                return result_dict, 200

        return {"message": "User not found"}, 404

    def start_session(self, user_id: int) -> Tuple[dict, int]:
        """
        Start new game session. User shouldn't have more than one active session,
        that's why we check if there is an active one. Expected is return of
        active session or create new one. With session, we create new game.
        """
        user: UserPydantic | None = self.get_user(id=user_id)

        if not user:
            return {"error": "User not found"}, 404

        session: UserSessionListPydantic | None = self.user_session_repo.filter(
            user_id=user_id, status=SessionStatusStates.ACTIVE.value
        )
        if session and session.__root__:
            message: str = f"Session already started with id {session.__root__[0].id}"
            session_detail: dict = session.__root__[0].dict()
            games: GameListPydantic | None = self.game_db_repo.filter(
                session_id=session_detail.get("id"), user_id=user_id
            )
            session_detail.update(
                {
                    "games": [
                        game.dict(
                            exclude={
                                "board",
                            }
                        )
                        for game in games.__root__
                    ]
                }
            )
            return {"error": message, "session_detail": session_detail}, 400

        new_session: UserSessionPydantic = self.user_session_repo.create(
            user_id=user.id
        )
        new_board: list = self.grid_manager.initialize_grid()
        game: GamePydantic = self.game_db_repo.create(
            user_id=user.id,
            session_id=new_session.id,
            board={"new_board": new_board},
            status=GameStatus.IN_PROGRESS.value,
        )

        user.credits -= PlayCredits.PLAY.value
        self.db_repo.update_fields(obj=user, credits=user.credits)

        result: dict = new_session.dict()
        result.update({"game_id": game.id})
        result.update({"message": "Game session started"})
        return result, 200

    def create_new_game(self, user_id: int, session_id: int) -> Tuple[dict, int]:
        """
        Create new game object with empty board, or return existing one.
        Link game to session.
        """
        user: UserPydantic | None = self.get_user(id=user_id)

        # Check if there is active session with given id
        user_session: UserSessionListPydantic = self.user_session_repo.filter(
            user_id=user.id, status=SessionStatusStates.ACTIVE.value
        )
        if not user_session or not user_session.__root__:
            return {"message": "No active session found"}, 400

        session_obj: UserSessionPydantic = user_session.__root__[0]

        # Check if there is already game in progress with given session id
        user_game: GameListPydantic | None = self.game_db_repo.filter(
            user_id=user_id,
            session_id=session_id,
            status__in=[GameStatus.IN_PROGRESS.value, GameStatus.NOT_STARTED.value],
        )
        if user_game and user_game.__root__:
            return {
                "error": "Game already started",
                "game_id": user_game.__root__[0].id,
                "session_id": session_id,
            }, 400
        if session_obj.status == SessionStatusStates.FINISHED.value:
            return {"error": "Session already finished"}, 400

        # Check if user has enough credits to start new game
        if user.credits < PlayCredits.PLAY.value:
            self.update_session_status(session_id=session_obj.id, user_id=user.id)
            return {"error": "Not enough credits. Game cannot start"}, 400

        user.credits -= PlayCredits.PLAY.value
        self.db_repo.update_fields(obj=user, credits=user.credits)

        new_board: list = self.grid_manager.initialize_grid()
        game: GamePydantic = self.game_db_repo.create(
            user_id=user.id,
            session_id=session_obj.id,
            board={"new_board": new_board},
            status=GameStatus.IN_PROGRESS.value,
        )
        return {
            "game_details": game.dict(
                exclude={
                    "board",
                }
            )
        }, 200

    def get_session_object(
        self, session_id: int, user_id: int
    ) -> UserSessionListPydantic | None:
        session: UserSessionListPydantic | None = self.user_session_repo.filter(
            id=session_id, user_id=user_id
        )
        return session

    @staticmethod
    def validate_field_indexes(fields: dict) -> Tuple[list, dict]:
        """Validate field indexes. Check if they are in range 1-3."""
        errors: dict = {}

        row = fields.get("row")
        col = fields.get("col")

        if row > 3 or row < 0:
            errors.update({"row": "The number is wrong. Should be between 1 and 3"})
        if col > 3 or col < 0:
            errors.update({"col": "The number is wrong. Should be between 1 and 3"})

        return [row, col], errors

    def _player_play(
        self, data: dict, user_game: GamePydantic
    ) -> Tuple[List[List[str | None]], int] | Tuple[dict, int]:
        row = data.get("row")
        col = data.get("col")
        if not row or not col:
            return {"message": "Invalid request. You didnt sent row and col"}, 400
        _, errors = self.validate_field_indexes(data)
        if errors:
            return {"status": "error", "error list": errors}, 400

        key: str = list(user_game.board.keys())[0]
        board_list: list = list(user_game.board.values())[0]

        user_board: GridManager = self.grid_manager(board_list)
        if not user_board.is_move_possible(row - 1, col - 1):
            return {
                "error": "Invalid move. Field is taken",
                "actual_board": user_board.get_board(),
                "player_sign": user_game.symbol,
            }, 400

        user_board.make_move(row - 1, col - 1, user_game.symbol)
        self.game_db_repo.update_fields(
            obj=user_game, board={key: user_board.get_board()}
        )
        return user_board.get_board(), 200

    def random_play(
        self, user_game: GamePydantic, session_id: int, user_id: int
    ) -> Tuple[List[List[str | None]], int] | Tuple[dict, int]:
        """Make random play."""
        user: UserPydantic | None = self.get_user(id=user_id)

        row, col = self.get_random_field_indexes()

        key: str = list(user_game.board.keys())[0]
        board_list: list = list(user_game.board.values())[0]

        user_board: GridManager = self.grid_manager(board_list)

        while not user_board.is_move_possible(row - 1, col - 1):
            row, col = self.get_random_field_indexes()

        if user_game.symbol == "X":
            user_board.make_move(row - 1, col - 1, "O")
        else:
            user_board.make_move(row - 1, col - 1, "X")

        self.game_db_repo.update_fields(
            obj=user_game, board={key: user_board.get_board()}
        )

        return {
            "actual_board": user_board.get_board(),
            "player_sign": user_game.symbol,
            "credits": user.credits,
        }, 200

    def lets_play_POST(self, session_id: int, user_id: int, game_id: int, data: dict):
        user_game: GameListPydantic | None = self.game_db_repo.filter(
            user_id=user_id, session_id=session_id, id=game_id
        )
        if not user_game or not user_game.__root__:
            return {"message": "Game not found"}, 404

        user_game_obj: GamePydantic = user_game.__root__[0]

        response: Tuple[List[List[str | None]], int] | Tuple[dict, int]
        status_code: int

        # player play
        response, status_code = self._player_play(data, user_game_obj)
        if status_code != 200:
            return response, status_code

        is_finished, winner = self.check_game_status(
            session_id, user_id, game_id=game_id
        )
        if is_finished:
            return winner, 200

        # random play
        response, status_code = self.random_play(user_game_obj, session_id, user_id)

        is_finished, winner = self.check_game_status(
            session_id, user_id, game_id=game_id
        )
        if is_finished:
            return winner, 200

        return response, status_code

    @staticmethod
    def get_random_field_indexes() -> Tuple[int, int]:
        """Get random field indexes. Method used for computer move."""
        row: int = random.randint(1, 3)
        col: int = random.randint(1, 3)
        return row, col

    def check_game_status(self, session_id: int, user_id: int, game_id: int):
        user_game: GameListPydantic | None = self.game_db_repo.filter(
            user_id=user_id, session_id=session_id, id=game_id
        )
        if not user_game:
            raise NoGameFoundException

        user_game_obj: GamePydantic = user_game.__root__[0]

        board_list: list = list(user_game_obj.board.values())[0]

        user_board: GridManager = self.grid_manager(board_list)
        is_finished, winner = user_board.check_game_state()
        user: UserPydantic | None = self.get_user(id=user_id)

        message: dict = {
            "status": "game is in progress",
            "actual_board": user_board.get_board(),
            "credits": user.credits,
            "user_sign": user_game_obj.symbol,
        }
        winner_res: Optional[bool]

        if is_finished:
            if winner == user_game_obj.symbol:
                user_game_obj.winner = user_game_obj.user_id
                if (
                    user
                    and user_game.__root__[0]
                    and user_game_obj.status != GameStatus.FINISHED.value
                ):
                    user.credits += PlayCredits.WIN.value
                    self.db_repo.update_fields(obj=user, credits=user.credits)
                    session: UserSessionListPydantic = self.get_session_obj(
                        user_id=user_id, session_id=session_id
                    )
                    if session_obj := session.__root__[0]:
                        self.user_session_repo.update_fields(
                            session_obj, score=session_obj.score + 1
                        )

                message = {
                    "status": "You won",
                    "actual_board": user_board.get_board(),
                    "credits": user.credits,
                    "user_sign": user_game_obj.symbol,
                }
                winner_res = True

            elif winner is None:
                message = {
                    "status": "There is no winner",
                    "actual_board": user_board.get_board(),
                    "credits": user.credits,
                    "user_sign": user_game_obj.symbol,
                }
                winner_res = False

            else:
                if user.credits < PlayCredits.PLAY.value:
                    self.update_session_status(session_id=session_id, user_id=user_id)
                message = {
                    "status": "You lost",
                    "actual_board": user_board.get_board(),
                    "credits": user.credits,
                    "user_sign": user_game_obj.symbol,
                }
                winner_res = None
            if user_game_obj.status != GameStatus.FINISHED.value:
                self.game_db_repo.update_fields(
                    obj=user_game_obj,
                    winner=winner_res,
                    status=GameStatus.FINISHED.value,
                    ended_at=datetime.now(),
                )

        return is_finished, message

    def get_session_obj(self, user_id: int, session_id: int) -> UserSessionListPydantic:
        return self.get_session_object(user_id=user_id, session_id=session_id)

    def update_session_status(self, session_id: int, user_id: int):
        """
        Update session status to finished if user lost
        and there is not enough credits in account. Due to fact,
        that play game cost 3 credits, if user lost, he will not be able to play again
        (he won't earn additional credits).
        """
        user: UserPydantic | None = self.get_user(id=user_id)
        session: UserSessionListPydantic = self.get_session_obj(
            user_id=user_id, session_id=session_id
        )

        self.user_session_repo.update_fields(
            obj=session.__root__[0], status=SessionStatusStates.FINISHED.value
        )
        if user.credits < PlayCredits.PLAY.value:
            session.__root__[0].status = SessionStatusStates.FINISHED.value
            self.user_session_repo.update_fields(
                obj=session.__root__[0],
                status=SessionStatusStates.FINISHED.value,
                ended_at=datetime.now(),
            )

    def lets_play_GET(self, user_id: int, session_id: int, game_id: int):
        user: UserPydantic | None = self.get_user(id=user_id)
        game_instance: GameListPydantic | None = self.game_db_repo.filter(
            user_id=user_id, session_id=session_id, id=game_id
        )
        if not game_instance or not game_instance.__root__:
            return {"message": "Game not found"}, 404

        board_list: list = list(game_instance.__root__[0].board.values())[0]
        result: dict = {
            "actual_board": self.grid_manager(board_list).get_board(),
            "player_sign": game_instance.__root__[0].symbol,
            "game": game_instance.__root__[0].id,
            "session": game_instance.__root__[0].session_id,
            "credits": user.credits,
        }
        return result, 200

    def check_session_status(self, session_id: int, user_id: int):
        session: UserSessionListPydantic | None = self.get_session_object(
            session_id, user_id
        )
        if not session:
            return SessionStatus(
                False, {"message": "Game session not found for requested user"}, 404
            )
        if (
            session
            and session.__root__
            and session.__root__[0].status == SessionStatusStates.FINISHED.value
        ):
            return SessionStatus(False, {"message": "Game session is finished"}, 400)

        return SessionStatus(True, session.dict(), 200)

    def get_high_scores(self):
        games = self.user_session_repo.get_score_data()
        return games, 200
