import abc
from typing import Union, Type, Optional, Iterable

from entities.entites import UserListPydantic, UserPydantic, UserSessionPydantic, UserSessionListPydantic, GamePydantic, \
    GameListPydantic
from entities.models import Game, UserSession, User, db
from entities.types import SessionStatusStates

ModelType = Union[User, UserSession, Game]


class BaseRepo(abc.ABC):
    model: Type[ModelType]

    @abc.abstractmethod
    def filter(self, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, obj):
        """Save LinkModelPydantic instance to database"""
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, obj):
        raise NotImplementedError

    @abc.abstractmethod
    def update_fields(self, obj, **kwargs) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def all(self):
        """Get all model instances from DB"""
        raise NotImplementedError


class UserDBRepo(BaseRepo):
    model = User

    def filter(self, **kwargs) -> Optional[UserListPydantic]:
        filter_res: Iterable | None = self.model.filter_by(**kwargs)
        if filter_res:
            new_res: UserListPydantic = UserListPydantic(__root__=[
                obj.__dict__ for obj in filter_res if obj]
            )
            return new_res
        return None

    def create(self, **kwargs) -> UserPydantic:
        """Create new user in DB"""
        self.model.create(**kwargs)
        user: Optional[UserListPydantic] = self.filter(**kwargs)
        return UserPydantic(**user.__root__[0].__dict__)

    def save(self, obj):
        return obj.save()

    def update_fields(self, obj: UserPydantic, **kwargs) -> UserPydantic | None:
        instance: User | None = self.model.query.filter_by(id=obj.id).first()
        if instance:
            for key, val in kwargs.items():
                try:
                    setattr(instance, key, val)
                except AttributeError as error:
                    raise error
            db.session.commit()
            db.session.refresh(instance)
            return UserPydantic(**instance.__dict__)
        return None

    def all(self):
        return self.model.all()


class UserSessionDBRepo(BaseRepo):
    model = UserSession

    def filter(self, **kwargs) -> Optional[UserSessionListPydantic]:
        filter_res: Iterable | None = self.model.filter_by(**kwargs)
        if filter_res:
            new_res: UserSessionListPydantic = UserSessionListPydantic(
                __root__=[obj.__dict__ for obj in filter_res]
            )
            return new_res
        return None

    def create(self, **kwargs) -> UserSessionPydantic:
        self.model.create(**kwargs)
        user_session: Optional[UserSessionListPydantic] = self.filter(
            status=SessionStatusStates.ACTIVE.value,
            **kwargs
        )
        return UserSessionPydantic(**user_session.__root__[0].__dict__)

    def save(self, obj):
        return obj.save()

    def update_fields(self, obj: UserSessionPydantic, **kwargs) -> UserSessionPydantic | None:
        instance: UserSession | None = self.model.query.filter_by(id=obj.id).first()
        if instance:
            for key, val in kwargs.items():
                try:
                    setattr(instance, key, val)
                except AttributeError as error:
                    raise error
            db.session.commit()
            db.session.refresh(instance)
            return UserSessionPydantic(**instance.__dict__)
        return None

    def all(self):
        ...


class GameDBRepo(BaseRepo):
    model = Game

    def filter(self, **kwargs) -> Optional[GameListPydantic]:
        query = self.model.query
        for key, val in kwargs.items():
            if "__in" in key:
                field = key.split("__")[0]
                query = query.filter(getattr(self.model, field).in_(val))
            else:
                query = query.filter(getattr(self.model, key) == val)

        filter_res: list = query.all()
        if filter_res:
            new_res: GameListPydantic = GameListPydantic(
                __root__=[obj.__dict__ for obj in filter_res]
            )
            return new_res
        return None

    def create(self, **kwargs) -> GamePydantic:
        self.model.create(**kwargs)
        game: Optional[GameListPydantic] = self.filter(**kwargs)
        return GamePydantic(**game.__root__[0].__dict__)

    def save(self, obj):
        return obj.save()

    def update_fields(self, obj: GamePydantic, **kwargs) -> GamePydantic | None:
        instance: Game | None = self.model.query.filter_by(id=obj.id).first()

        if instance:
            for key, val in kwargs.items():
                try:
                    setattr(instance, key, val)
                except AttributeError as error:
                    raise error
            db.session.commit()
            db.session.refresh(instance)
            return GamePydantic(**instance.__dict__)
        return None

    def all(self):
        ...