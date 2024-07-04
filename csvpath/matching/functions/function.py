from typing import Any
from csvpath.matching.productions.expression import Matchable
from csvpath.matching.expression_utility import ExpressionUtility

class NoChildrenException(Exception):
    pass

class ChildrenException(Exception):
    pass

class Function(Matchable):

    def __init__(self, matcher:Any, name:str, child:Matchable=None)->None:
        super().__init__(matcher, name=name)
        self.matcher = matcher # atm, circular dep
        self._function_or_equality = child
        if child:
            self.add_child(child)

    def __str__(self) -> str:
        return f"""\n{self.__class__}{self.name}({self._function_or_equality})"""

    def to_value(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        id = self.get_id()
        if self._function_or_equality:
            if not self._function_or_equality.matches(skip=skip):
                return False
        print("WARNING: function getting to_value defaulting to True")
        return True # leave this for now for testing



