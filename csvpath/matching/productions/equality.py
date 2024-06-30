from typing import Any
from csvpath.matching.productions.expression import Matchable

class Equality(Matchable):

    def __init__(self, matcher):
        super().__init__(matcher)
        left:Any = None
        right:Any = None

    def set_left(self, left):
        self.left = left
        if self.left:
            self.add_child(self.left)

    def set_right(self, right):
        self.right = right
        if self.right:
            self.add_child(self.right)

    def __str__(self) -> str:
        return f"""{self.__class__}: {self.left}={self.right}"""

    def matches(self) -> bool:
        if not self.left or not self.right:
            return False
        print(f"Equality.matches: {self.left.to_value()} == {self.right.to_value()}")
        print(f"Equality.matches: left,right classes: {self.left.__class__} == {self.right.__class__}")
        print(f"Equality.matches: left,right value classes: {self.left.to_value().__class__} == {self.right.to_value().__class__}")
        left = self.left.to_value()
        right = self.right.to_value()
        b = None
        if left.__class__ == right.__class__:
            print("Equality.matches: left,right value classes are same")
            b = self.left.to_value() == self.right.to_value()
        elif (left.__class__ == str and right.__class__==int) or (right.__class__ == str and left.__class__==int):
            print("Equality.matches: left,right value classes are int/str. doing str compare.")
            b = f"{left}" == f"{right}"
        else:
            print("Equality.matches: left,right value classes are ?/?. doing str compare.")
            b = f"{left}" == f"{right}"
        print(f"Equality.matches: b: {b}")
        return b

    def to_value(self) -> Any:
        return self.matches()


