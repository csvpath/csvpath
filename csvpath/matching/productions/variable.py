from typing import Any
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.expression_utility import ExpressionUtility


class Variable(Matchable):
    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(matcher, value=value, name=name)
        n, qs = ExpressionUtility.get_name_and_qualifiers(name)
        self.name = n
        self.qualifiers = qs

    def __str__(self) -> str:
        return f"""{self.__class__}: {self.name}"""

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()

    def matches(self, *, skip=[]) -> bool:
        if self.match is None:
            if self.asbool:
                v = self.to_value(skip=skip)
                self.match = ExpressionUtility.asbool(v)
            else:
                self.match = self.value is not None
        return self.match

    def to_value(self, *, skip=[]) -> Any:
        if not self.value:
            track = self.first_non_term_qualifier(None)
            self.value = self.matcher.get_variable(self.name, tracking=track)
        return self.value
