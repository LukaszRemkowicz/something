from collections import namedtuple
from enum import Enum

Managers = namedtuple("Managers", ["UserManager", "UserSessionManager", "GridManager"])
SessionStatus = namedtuple("SessionStatus", "active session_data status_code")


class SessionStatusStates(Enum):
    ACTIVE = "active"
    FINISHED = "finished"
    NEW = "new"


class GameStatus(Enum):
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    NOT_STARTED = "not_started"
