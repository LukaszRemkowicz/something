import os
import secrets
from enum import Enum
from typing import Optional

from pydantic import BaseSettings, SecretStr

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.dirname(ROOT_PATH)


def generate_secret_key() -> str:
    return secrets.token_hex(16)


class DatabaseSettings(BaseSettings):
    """Database settings"""

    host: str = "localhost"
    port: int = 5432
    username: str = "postgres"
    password: SecretStr = SecretStr("postgres")
    name: str = "postgres"


class Settings(BaseSettings):
    db: DatabaseSettings
    jwt: Optional[str]

    class Config:
        env_file = os.path.join(ROOT_PATH, "../.env")
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"

    @property
    def jwt_secret(self):
        if self.jwt:
            return self.jwt
        key: str = generate_secret_key()
        return key


settings = Settings()


def get_db_url() -> str:
    login_and_password: str = (
        f"{settings.db.username}:{settings.db.password.get_secret_value()}"
    )
    server_endpoint: str = f"{login_and_password}@{settings.db.host}/{settings.db.name}"
    url: str = f"postgresql+psycopg2://{server_endpoint}"
    return url


class PlayCredits(Enum):
    """Play credits enum"""

    WIN = 4
    PLAY = 3
