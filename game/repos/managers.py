from typing import Optional

from entities.models import User, db, UserSession

from entities.types import Managers


class GridManager:

    @staticmethod
    def get_grid():
        return [[" ", " ", " "], [" ", " ", " "], [" ", " ", " "]]


class UserManager:
    def __init__(self, user: User | None = None):
        self.users = user

    @staticmethod
    def update_fields(instance: User, **kwargs) -> None:
        breakpoint()
        if kwargs:
            for key, val in kwargs.items():
                try:
                    setattr(instance, key, val)
                except AttributeError as error:
                    raise error
            db.session.commit()

    @staticmethod
    def filter(**kwargs) -> User | None:
        """Filter users by given kwargs"""
        return User.query.filter_by(**kwargs).first()

    @staticmethod
    def refresh_from_db(instance: User) -> User:
        db.session.refresh(instance)


class UserSessionManager:
    def __init__(self, user_session: UserSession | None = None):
        self.user_session = user_session

    @staticmethod
    def update():
        db.session.commit()

    @staticmethod
    def filter(**kwargs) -> User | None:
        """Filter user sessions by given kwargs"""
        return UserSession.query.filter_by(**kwargs).first()

    def create(self, **kwargs) -> Optional[UserSession]:
        """Save object to database"""
        if kwargs:
            UserSession.create(**kwargs)
            instance: UserSession = self.filter(**kwargs)
            return instance
        return None


managers = Managers(UserManager, UserSessionManager, GridManager)
