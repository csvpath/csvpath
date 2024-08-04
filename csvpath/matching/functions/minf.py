from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality
from ..expression_utility import ExpressionUtility
from ..productions.expression import Matchable
from statistics import mean, median


class MinMax(Function):
    """
    # TODO:
    # longest value
    # quintile
    # decile
    # std div
    """

    MAX = True
    MIN = False

    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name, child)

    def get_the_value(self) -> Any:
        if isinstance(self.children[0], Equality):
            return self.children[0].left.to_value()
        else:
            return self.children[0].to_value()

    def get_the_value_conformed(self) -> Any:
        v = self.get_the_value()
        return ExpressionUtility.ascompariable(v)

    def get_the_name(self) -> Any:
        if isinstance(self.children[0], Equality):
            return self.children[0].left.name
        else:
            return self.children[0].name

    def get_the_line(self) -> int:
        if isinstance(self.children[0], Equality):
            v = self.children[0].right.to_value()
            v = f"{v}".strip()
            if v == "match":
                return self.matcher.csvpath.current_match_count()
            elif v == "scan":
                return self.matcher.csvpath.current_scan_count()
            else:
                return self.matcher.csvpath.current_line_number()
        else:
            return self.matcher.csvpath.current_line_number()

    def is_match(self) -> bool:
        if self.has_onmatch():
            return True
        elif isinstance(self.children[0], Equality):
            v = self.children[0].right.to_value()
            v = f"{v}".strip()
            return v == "match"
        else:
            return False

    def line_matches(self):
        es = self.matcher.expressions
        for e in es:
            if not e[0].matches(skip=[self]):
                return False
        return True

    def _ignore(self):
        if (
            self.get_the_name() in self.matcher.csvpath.headers
            and self.matcher.csvpath.current_line_number() == 0
        ):
            return True
        if self.is_match() and not self.line_matches():
            return True
        return False

    def _store_and_compare(self, v, maxormin: bool) -> Any:
        self.matcher.set_variable("min", tracking=f"{self.get_the_line()}", value=v)
        all_values = self.matcher.get_variable(
            "min" if maxormin is MinMax.MIN else "max"
        )
        m = None
        for k, v in enumerate(all_values.items()):
            v = v[1]
            if not m or ((v < m) if maxormin is MinMax.MIN else (v > m)):
                m = v
        return m


class Min(MinMax):
    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name, child)

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if self.children and not len(self.children) == 1:
            raise ChildrenException("must have a child")
        if not self.value:
            # skip lines we should ignore
            if self._ignore():
                return self.value
            # track and compare
            v = self.get_the_value_conformed()
            self.matcher.set_variable("min", tracking=f"{self.get_the_line()}", value=v)
            m = self._store_and_compare(v, MinMax.MIN)
            self.value = m
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return True


class Max(MinMax):
    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name, child)

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if self.children and not len(self.children) == 1:
            raise ChildrenException("must have a child")
        if not self.value:
            # skip lines we should ignore
            if self._ignore():
                return self.value
            # track and compare
            v = self.get_the_value_conformed()
            self.matcher.set_variable("max", tracking=f"{self.get_the_line()}", value=v)
            m = self._store_and_compare(v, MinMax.MAX)
            self.value = m
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return True


class Average(MinMax):
    def __init__(
        self, matcher: Any, name: str, child: Matchable = None, ave_or_med="average"
    ) -> None:
        super().__init__(matcher, name, child)
        self.ave_or_med = ave_or_med

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return self.value
        if self.children and not len(self.children) == 1:
            raise ChildrenException("must have a child")
        if self.value is None:
            v = self.get_the_value()
            # if we're watching a header and we're in the header row skip it.
            if (
                self.get_the_name() in self.matcher.csvpath.headers
                and self.matcher.csvpath.current_line_number() == 0
            ):
                return self.value
            # if the line must match and it doesn't stop here and return
            if self.is_match() and not self.line_matches():
                return self.value
            n = self.first_non_term_qualifier(self.ave_or_med)
            # set the "average" or "median" variable tracking the value by line, scan, or match count
            self.matcher.set_variable(n, tracking=f"{self.get_the_line()}", value=v)
            # get value for all the line counts
            all_values = self.matcher.get_variable(n)
            m = []
            for k, v in enumerate(all_values.items()):
                v = v[1]
                try:
                    v = float(v)
                    m.append(v)
                except Exception:
                    pass
                if self.ave_or_med == "average":
                    self.value = mean(m)
                else:
                    self.value = median(m)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return True
