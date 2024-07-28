from typing import Any
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.expression_utility import ExpressionUtility


class Variable(Matchable):
    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(matcher, value=value, name=name)
        #
        # onmatch is a qualifier, but it was created first, so is more specific.
        # this handling of qualifiers is not like the Qualifiers enum. should be updated.
        #
        # self.onmatch = False
        # dot = name.find(".")
        # print(f"Variable.init: dot: {dot}, name: {name}")

        n, qs = ExpressionUtility.get_name_and_qualifiers(name)
        self.name = n
        self.qualifiers = qs
        """
        if dot > -1:
            self.name = name[0:dot]
            om = name[dot + 1 :]
            om = om.strip()
            print(f"Variable.init: om: {om}")
            if om == "onmatch":
                self.onmatch = True
            elif om == "onchange":
                self.onchange = True
        """

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
            self.value = self.matcher.get_variable(self.name)
        return self.value
