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
        print(f"Equality: {self.left.to_value()} == {self.right.to_value()}")
        return self.left.to_value() == self.right.to_value()

    def to_value(self) -> Any:
        return self.matches()


