from typing import Any
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.util.expression_utility import ExpressionUtility
from . import ChildrenException


class Variable(Matchable):
    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(matcher, value=value, name=name)
        n, qs = ExpressionUtility.get_name_and_qualifiers(name)
        self.name = n
        self.qualifiers = qs
        if n is None:
            raise ChildrenException("Name cannot be None")
        elif n.strip() == "":
            raise ChildrenException("Name cannot be the empty string")

    def __str__(self) -> str:
        return f"""{self.__class__}: {self.name}"""

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:
            return self._noop_match()
        if self.match is None:
            if self.asbool:
                v = self.to_value(skip=skip)
                self.match = ExpressionUtility.asbool(v)
            else:
                self.match = self.value is not None
        return self.match

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:
            return self._noop_value()
        if not self.value:
            track = self.first_non_term_qualifier(None)
            self.value = self.matcher.get_variable(self.name, tracking=track)
            if self.value is None:
                # if it looks like a bool let's try that and
                # take the answer if not None.
                # in principle we could do this with numbers too.
                retry = None
                if track == "True":
                    retry = self.matcher.get_variable(self.name, tracking=True)
                elif track == "False":
                    retry = self.matcher.get_variable(self.name, tracking=False)
                if retry is not None:
                    self.value = retry
        return self.value
