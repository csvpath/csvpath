from typing import Any, List
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.productions.header import Header
from csvpath.matching.productions.term import Term
from csvpath.matching.functions.function import Function


class Equality(Matchable):
    def __init__(self, matcher):
        super().__init__(matcher)
        self.op: str = (
            "="  # we assume = but if a function or other containing production
        )
        # wants to check we might have a different op

    def reset(self) -> None:
        self.value = None
        super().reset()

    @property
    def left(self):
        return self.children[0]

    @left.setter
    def left(self, o):
        if not self.children:
            self.children = [None, None]
        while len(self.children) < 2:
            self.children.append(None)
        else:
            self.children[0] = o

    @property
    def right(self):
        return self.children[1]

    @right.setter
    def right(self, o):
        if not self.children:
            self.children = [None, None]
        while len(self.children) < 2:
            self.children.append(None)
        self.children[1] = o

    def other_child(self, o):
        if self.left == o:
            return (self.right, 1)
        elif self.right == o:
            return (self.left, 0)
        else:
            return None

    def is_terminal(self, o):
        return (
            isinstance(o, Variable)
            or isinstance(o, Term)
            or isinstance(o, Header)
            or isinstance(o, Function)
            or o is None
        )

    def both_terminal(self):
        return self.is_terminal(self.left) and self.is_terminal(self.right)

    def commas_to_list(self) -> List[Any]:
        ls = []
        self._to_list(ls, self)
        return ls

    def _to_list(self, ls: List, p):
        if isinstance(p, Equality) and p.op == ",":
            self._to_list(ls, p.left)
            self._to_list(ls, p.right)
        else:
            ls.append(p)

    def set_operation(self, op):
        self.op = op

    # ------------------

    def mathic(self):
        return self.op != ","

    def perform_math(self):
        if self.op == "," or self.op == "=":
            return
        else:
            if isinstance(self.left, Equality):
                pass
                # self.left.perform_math()
            if isinstance(self.right, Equality) and self.mathic():
                pass
                # self.right.perform_math()
            self.left.value = self.math(self.left.to_value(), self.right.to_value())
            if isinstance(self.left, Variable):
                v = self.left.value
                self.matcher.set_variable(self.left.name, value=v)
        self.value = None
        self.to_value()

    def math(self, lv, rv):
        if self.op == "-":
            return lv - rv
        elif self.op == "+":
            return lv + rv
        elif self.op == "*":
            return lv * rv
        elif self.op == "/":
            return lv / rv
        else:
            raise Exception(f"unknown op: {self.op}")

    # ------------------

    def __str__(self) -> str:
        return f"""{self.__class__}: {self.left}={self.right}"""

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        if not self.left or not self.right:
            return False
        if not self.value:
            b = None
            if isinstance(self.left, Variable):
                v = self.right.to_value(skip=skip)
                print(f"Equality.matches: left var onmatch: {self.left.onmatch}")
                if self.left.onmatch or (
                    self.right.name == "count" and len(self.right.children) == 0
                ):
                    #
                    # register to set if all else matches
                    #
                    self.matcher.set_if_all_match(self.left.name, value=v)
                else:
                    print(f"Equality.matches: left var: {self.left.name} = {v}")
                    self.matcher.set_variable(self.left.name, value=v)
                b = True
            else:
                left = self.left.to_value(skip=skip)
                right = self.right.to_value(skip=skip)
                if left.__class__ == right.__class__:
                    b = self.left.to_value(skip=skip) == self.right.to_value(skip=skip)
                elif (left.__class__ == str and right.__class__ == int) or (
                    right.__class__ == str and left.__class__ == int
                ):
                    b = f"{left}" == f"{right}"
                else:
                    b = f"{left}" == f"{right}"
            self.value = b
        return self.value

    def to_value(self, *, skip=[]) -> Any:
        if self.value is None:
            if self.mathic():
                pass
                # self.perform_math()
            self.value = self.matches(skip=skip)
        return self.value
