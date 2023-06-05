from typing import Optional, List

from entities.models import User, db, UserSession

from entities.types import Managers


class GridManager:

    def __init__(self):
        self._fields: List[List[None]] = self.initialize_grid()

    def __str__(self):
        return "\n".join(["|".join([y or " " for y in x]) for x in self._fields])

    @staticmethod
    def initialize_grid() -> List[List[None]]:
        return [[None, None, None] for _ in range(3)]

    @property
    def fields(self):
        return self._fields

    def __setitem__(self, col, row, value):
        self._fields[col][row] = value

    def get_field(self, col, row):
        return self._fields[col][row]

