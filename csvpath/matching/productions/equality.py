from typing import Any, List
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.productions.header import Header
from csvpath.matching.productions.term import Term
from csvpath.matching.functions.function import Function, ChildrenException


class Equality(Matchable):
    def __init__(self, matcher):
        super().__init__(matcher)
        self.op: str = (
            "="  # we assume = but if a function or other containing production
        )
        # wants to check we might have a different op

    def reset(self) -> None:
        self.value = None
        self.match = None
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

    def __str__(self) -> str:
        return f"""{self.__class__}: {self.left}={self.right}"""

    def _left_nocontrib(self, m) -> bool:
        if isinstance(m, Equality):
            return self._left_nocontrib(m.left)
        else:
            return m.nocontrib

    # ------------------

    def _do_assignment(self, *, skip=[]) -> bool:
        if isinstance(self.left, Variable) and self.op == "=":
            b = None
            v = self.right.to_value(skip=skip)
            oc = self.left.has_onchange()
            ov = ""
            if oc:
                ov = self.matcher.get_variable(self.left.name)
                if f"{v}" != f"{ov}":
                    b = True
                else:
                    b = False
            #
            # we can be both onmatch and latch, and
            # also onchange, though that adds no value given latch
            if self.left.onmatch or (
                self.right.name == "count" and len(self.right.children) == 0
            ):
                if (
                    self.left.latch
                    and self.matcher.get_variable(self.left.name) is not None
                ):
                    b = True
                else:
                    #
                    # register to set if all else matches. doesn't matter if
                    # onchange
                    #
                    self.matcher.set_if_all_match(self.left.name, value=v)
                    if not oc:
                        b = True
            else:
                if (
                    self.left.latch
                    and self.matcher.get_variable(self.left.name) is not None
                ):
                    b = True
                else:
                    t = self.left.first_non_term_qualifier(None)
                    self.matcher.set_variable(self.left.name, value=v, tracking=t)
                    if not oc:
                        b = True
            return b
        else:
            raise ChildrenException("Left must be a variable and op must be =")

    def _do_when(self, *, skip=[]) -> bool:
        b = None
        if self.op == "->":
            if self.left.matches(skip=skip) is True:
                b = True
                self.right.matches(skip=skip)
            else:
                if self._left_nocontrib(self.left):
                    b = True
                else:
                    b = False
        else:
            raise ChildrenException("Not a when operation")  # this can't really happen
        return b

    def _do_equality(self, *, skip=[]) -> bool:
        b = None
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
        return b

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        if not self.left or not self.right:
            return False
        if not self.match:
            b = None
            if isinstance(self.left, Variable) and self.op == "=":
                b = self._do_assignment(skip=skip)
            elif self.op == "->":
                b = self._do_when(skip=skip)
            else:
                b = self._do_equality(skip=skip)
            self.match = b
        return self.match

    def to_value(self, *, skip=[]) -> Any:
        if self.value is None:
            self.value = self.matches(skip=skip)
        return self.value
