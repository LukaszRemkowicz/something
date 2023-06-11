import random
from datetime import datetime

from entities.types import GameStatus, SessionStatusStates
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy_json import mutable_json_type

db: SQLAlchemy = SQLAlchemy()


class BaseMixin:
    @classmethod
    def create(cls, **kwargs) -> None:
        """Save object to database"""
        if kwargs:
            instance = cls(**kwargs)  # noqa
            db.session.add(instance)
            db.session.commit()

    @classmethod
    def save(cls):
        db.session.commit()

    @classmethod
    def filter_by(cls, **kwargs):
        return cls.query.filter_by(**kwargs)  # noqa


class User(db.Model, BaseMixin):
    __tablename__ = "users"
    id = Column(db.Integer, primary_key=True)
    password = Column(db.String)
    email = Column(db.String, unique=True)
    credits = Column(db.Integer, default=10)

    __table_args__ = (CheckConstraint(credits >= 0, name="positive_credits_check"),)


class UserSession(db.Model, BaseMixin):
    __tablename__ = "session"
    id = Column(db.Integer, primary_key=True)
    score = Column(
        db.Integer, doc="User score per session. One point per win.", default=0
    )
    user_id = Column(db.Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User", backref="UserSession")
    status = Column(
        db.String,
        default=SessionStatusStates.ACTIVE.value,
        doc="Session status. Active or Finished.",
    )
    created_at = Column(db.DateTime, default=datetime.now)
    ended_at = Column(db.DateTime, nullable=True)


class Game(db.Model, BaseMixin):
    __tablename__ = "game"
    id = db.Column(db.Integer, primary_key=True)
    board = db.Column(
        mutable_json_type(dbtype=JSONB, nested=True),
        nullable=True,
        doc="Game board. Nested JSON with 3x3 matrix.",
    )
    user_id = db.Column(db.Integer, ForeignKey("users.id", ondelete="CASCADE"))
    symbol = db.Column(
        db.String(1),
        nullable=False,
        default=lambda: random.choice(["X", "O"]),
        doc="User symbol. Randomly selected between X or O.",
    )
    winner = db.Column(
        db.Boolean,
        nullable=True,
        doc="Game winner. True if user won, False if user lost, None if draw.",
    )
    session_id = db.Column(
        db.Integer, ForeignKey("session.id", ondelete="SET NULL"), nullable=True
    )
    status = Column(
        db.String,
        default=GameStatus.NOT_STARTED.value,
        doc="Session status. Active or Finished.",
    )
    user = relationship("User")
    session = relationship("UserSession")


models_union = User | UserSession | Game
