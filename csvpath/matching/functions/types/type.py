# pylint: disable=C0114
from ..function_focus import MatchDecider


class Type(MatchDecider):
    @property
    def my_type(self) -> str:
        t = f"{type(self)}".rstrip("'>")
        t = t[t.rfind("'") + 1 :]
        return t
