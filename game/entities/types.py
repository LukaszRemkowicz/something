from collections import namedtuple

Managers = namedtuple("Managers", ["UserManager", "UserSessionManager", "GridManager"])
SessionStatus = namedtuple("SessionStatus", "active session_data status_code")
