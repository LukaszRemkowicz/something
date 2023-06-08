from entities.entites import UserPydantic
from entities.models import User
from tests.factories import UserFactory


def user2pydantic(user: User | UserFactory) -> UserPydantic:
    """Convert User model instance to UserPydantic instance"""
    return UserPydantic(**user.__dict__)
