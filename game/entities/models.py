from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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


class User(db.Model, BaseMixin):
    __tablename__ = 'users'
    id = Column(db.Integer, primary_key=True)
    password = Column(db.String)
    email = Column(db.String, unique=True)
    credits = Column(db.Integer, default=0)


class UserSession(db.Model, BaseMixin):
    __tablename__ = 'session'
    id = Column(db.Integer, primary_key=True)
    score = Column(db.Integer)
    user_id = Column(db.Integer, ForeignKey('users.id'))
    user = relationship("User", backref="UserSession")


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    board = db.Column(db.String(9), nullable=True)
    current_player = db.Column(db.String(1), nullable=False, default='X')
    winner = db.Column(db.Integer, nullable=True)

    def __init__(self):
        self.board = ' ' * 9
