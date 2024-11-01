# pylint: disable=C0114
from typing import Any
from .matchable import Matchable
from ..util.expression_utility import ExpressionUtility


class Header(Matchable):
    """a header is analogous to a column in a spreadsheet or
    RDBMS but with CSV characteristics"""

    NEVER = -9999999999

    def __str__(self) -> str:
        return f"""{self._simple_class_name()}({self.qualified_name}) """

    def __init__(self, matcher, *, value: Any = None, name: str = None) -> None:
        # header names can be quoted like "Last Year Number"
        if isinstance(name, str):
            name = name.strip()
            # if name[0] == '"' and name[len(name) - 1] == '"':
            #    name = name[1 : len(name) - 1]
        super().__init__(matcher, value=Header.NEVER, name=name)

    def reset(self) -> None:
        self.value = Header.NEVER
        self.match = None
        super().reset()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:
            ret = self._noop_value()
            self.valuing().result(ret).because("skip")
            return ret
        if self.value == Header.NEVER:
            ret = Header.NEVER
            if isinstance(self.name, int) or self.name.isdecimal():
                if int(self.name) >= len(self.matcher.line):
                    ret = None
                else:
                    ret = self.matcher.line[int(self.name)]
            else:
                n = self.matcher.header_index(self.name)
                if n is None:
                    ret = None
                elif self.matcher.line and len(self.matcher.line) > n:
                    ret = self.matcher.line[n]
                else:
                    self.matcher.csvpath.logger.debug(
                        f"Header.to_value: miss because n >= {len(self.matcher.line)}"
                    )
            if self.asbool:
                self.value = ExpressionUtility.asbool(ret)
            else:
                self.value = ret
        if isinstance(self.value, str):
            self.value = self.value.strip()
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:
            ret = self._noop_match()
            self.matching().result(ret).because("skip")
            return ret
        if self.match is None:
            v = self.to_value(skip=skip)
            if self.asbool:
                v = self.to_value(skip=skip)
                self.match = ExpressionUtility.asbool(v)
            else:
                self.match = not ExpressionUtility.is_none(v)  # v is not None
        return self.match
