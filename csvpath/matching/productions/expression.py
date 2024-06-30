from typing import Any
from csvpath.matching.expression_utility import ExpressionUtility

class Matchable:

    def __init__(self, matcher, *, value:Any=None, name:str=None):
        self.parent = None
        self.children = []
        self.matcher = matcher
        self.value = value
        self.name = name
        self._id:str = None
        if self.name and self.name.__class__ == str:
            self.name = self.name.strip()

    def __str__(self) -> str:
        return f"""{self.__class__}"""

    def matches(self) -> bool:
        return True # leave this for now for testing

    def to_value(self) -> Any:
        return None

    def set_parent(self, parent):
        self.parent = parent

    def add_child(self, child):
        if child:
            child.set_parent(self)
            if child not in self.children:
                self.children.append(child)

    def get_id(self, child=None):
        if not self._id:
            thing = self if not child else child
            self._id = ExpressionUtility.get_id( thing=thing )
        return self._id



class Expression(Matchable):

    def matches(self) -> bool:
        for child in self.children:
            if not child.matches():
                return False
        return True


