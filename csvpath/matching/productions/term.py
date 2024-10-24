# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions.matchable import Matchable


class Term(Matchable):
    """represents any plain int, string, or regex value"""

    def __str__(self) -> str:
        return f"""{self._simple_class_name()}({self.value})"""

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        if isinstance(value, str):
            value = value.lstrip('"').rstrip('"')
        super().__init__(matcher=matcher, name=name, value=value)

    def reset(self) -> None:  # pylint: disable=W0246
        super().reset()
        # re: W0246: Matchable handles this class's children

    def to_value(self, *, skip=None) -> Any:
        """
        stripping out whitespace makes sense for headers. not for terms. if we have a
        term we created it ourselves intentionally with the whitespace. still need a
        configuration for headers tho. this comment can be removed when things settle
        down.
        if isinstance(self.value, str):
            self.value = self.value.strip()
        """
        return self.value
