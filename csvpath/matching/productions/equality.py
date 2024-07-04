from typing import Any, List
from csvpath.matching.productions.expression import Matchable
from csvpath.matching.productions.variable import Variable

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

    def __str__(self) -> str:
        return f"""{self.__class__}: {self.left}={self.right}"""

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        if not self.left or not self.right:
            return False
        b = None
        if isinstance( self.left, Variable):
            self.matcher.print(f"Equality.matches: setting variable: {self.left.name} to {self.right.to_value(skip=skip)}")
            self.matcher.set_variable(self.left.name, value=self.right.to_value(skip=skip))
            b = True
        else:
            self.matcher.print(f"Equality.matches: {self.left.to_value(skip=skip)} == {self.right.to_value(skip=skip)}")
            self.matcher.print(f"Equality.matches: left,right classes: {self.left.__class__} == {self.right.__class__}")
            self.matcher.print(f"Equality.matches: left,right value classes: {self.left.to_value(skip=skip).__class__} == {self.right.to_value(skip=skip).__class__}")
            left = self.left.to_value(skip=skip)
            right = self.right.to_value(skip=skip)
            if left.__class__ == right.__class__:
                self.matcher.print("Equality.matches: left,right value classes are same")
                b = self.left.to_value(skip=skip) == self.right.to_value(skip=skip)
            elif (left.__class__ == str and right.__class__==int) or (right.__class__ == str and left.__class__==int):
                self.matcher.print("Equality.matches: left,right value classes are int/str. doing str compare.")
                b = f"{left}" == f"{right}"
            else:
                self.matcher.print("Equality.matches: left,right value classes are ?/?. doing str compare.")
                b = f"{left}" == f"{right}"
            self.matcher.print(f"Equality.matches: b: {b}")
        return b

    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)


