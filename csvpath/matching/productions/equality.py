from typing import Any, List
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.matchable import Matchable

class Equality(Matchable):

    def __init__(self, matcher):
        super().__init__(matcher)
        self.left:Any = None
        self.right:Any = None
        self.op:str = "=" # we assume = but if a function or other containing production
                     # wants to check we might have a different op

    def commas_to_list(self) -> List[Any]:
        ls = []
        self._to_list(ls, self)
        return ls

    def _to_list(self, ls:List, p) :
        if isinstance(p, Equality) and p.op == ',':
            self._to_list(ls, p.left)
            self._to_list(ls, p.right)
        else:
            ls.append(p)

    def set_left(self, left):
        self.left = left
        if self.left:
            self.add_child(self.left)

    def set_right(self, right):
        self.right = right
        if self.right:
            self.add_child(self.right)

    def set_operation(self, op):
        self.op = op


#------------------

    def mathic(self):
        return self.op != ','

    def perform_math(self):
        if self.op == ',' or self.op == '=':
            return
        else:
            if isinstance(self.left, Equality):
                pass
                #self.left.perform_math()
            if isinstance(self.right, Equality) and self.mathic():
                pass
                #self.right.perform_math()
            self.left.value = self.math(self.left.to_value(),  self.right.to_value())
            if isinstance( self.left, Variable):
                v = self.left.value
                self.matcher.set_variable(self.left.name, value=v)

        self.value = None
        self.to_value()

    def math(self, lv, rv):
        if self.op == '-':
            return lv - rv
        elif self.op == '+':
            return lv + rv
        elif self.op == '*':
            return lv * rv
        elif self.op == '/':
            return lv / rv
        else:
            raise Exception(f'unknown op: {self.op}')


#------------------

    def __str__(self) -> str:
        return f"""{self.__class__}: {self.left}={self.right}"""

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        if not self.left or not self.right:
            return False
        if not self.value:
            b = None
            if isinstance( self.left, Variable):
                v = self.right.to_value(skip=skip)
                self.matcher.set_variable(self.left.name, value=v)
                b = True
            else:
                left = self.left.to_value(skip=skip)
                right = self.right.to_value(skip=skip)
                if left.__class__ == right.__class__:
                    b = self.left.to_value(skip=skip) == self.right.to_value(skip=skip)
                elif (left.__class__ == str and right.__class__==int) or (right.__class__ == str and left.__class__==int):
                    b = f"{left}" == f"{right}"
                else:
                    b = f"{left}" == f"{right}"
            self.value = b
        return self.value

    def to_value(self, *, skip=[]) -> Any:
        if self.value is None:
            if self.mathic():
                pass
                #self.perform_math()
            self.value = self.matches(skip=skip)
        return self.value

