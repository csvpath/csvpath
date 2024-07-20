from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.functions.header import Header
from csvpath.matching.functions.variable import Variable
from csvpath.matching.productions.equality import Equality
from csvpath.matching.productions.term import Term


class Any(Function):
    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return False
        if self.children and len(self.children) > 1:
            ChildrenException("Stop must have only 1 or 0 children")
        if self.match is None:
            self.match = False

            om = self.has_onmatch()
            if om and not self.line_matches():
                pass
            else:
                if len(self.children) == 1:
                    if isinstance(self.children[0], Equality):
                        self.equality()
                    elif isinstance(self.children[0], Variable):
                        # any(variable())
                        self.variable()
                    elif isinstance(self.children[0], Header):
                        # any(header())
                        self.header()
                    else:
                        # any("True")
                        self.check_value()
                else:
                    # any()
                    for h in self.matcher.line:
                        if h is None:
                            continue
                        elif h is f"{h}".strip() == "":
                            continue
                        else:
                            self.match = True
                            break
                    if self.match is False:
                        for v in self.matcher.csvpath.variables.values():
                            if v is None:
                                continue
                            elif v is f"{v}".strip() == "":
                                continue
                            else:
                                self.match = True
                                break
        return self.match

    def check_value(self):
        value = self.children[0].to_value()
        for h in self.matcher.line:
            if f"{h}" == f"{value}":
                self.match = True
                break
            if self.match is False:
                for v in self.matcher.csvpath.variables.values():
                    if f"{v}" == f"{value}":
                        self.match = True
                        break

    def header(self):
        for h in self.matcher.line:
            if h is None:
                continue
            elif h is f"{h}".strip() == "":
                continue
            else:
                self.match = True
                break

    def variable(self):
        for v in self.matcher.csvpath.variables.values():
            if v is None:
                continue
            elif v is f"{v}".strip() == "":
                continue
            else:
                self.match = True
                break

    def equality(self):
        value = self.children[0].right.to_value()
        if isinstance(self.children[0].left, Header):
            for h in self.matcher.line:
                if f"{h}" == f"{value}":
                    self.match = True
                    break
        elif isinstance(self.children[0].left, Variable):
            for v in self.matcher.csvpath.variables.values():
                if f"{v}" == f"{value}":
                    self.match = True
                    break
        else:
            raise ChildrenException(
                "Left side of equality child of any() must be header() or variable()"
            )
