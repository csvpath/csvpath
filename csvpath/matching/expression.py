from dataclasses import dataclass
from typing import Any
from csvpath.parser_utility import ParserUtility
from ply.yacc import YaccProduction

class Matchable:
    def matches(self) -> bool:
        return True # leave this for now for testing

class Valued(Matchable):
    def to_value(self) -> Any:
        return None

@dataclass
class Expression(Matchable):
    matcher:Any
    value:Any

    def __str__(self) -> str:
        return f"""Exp value: {self.value} """

    def matches(self) -> bool:
        if self.value:
            return self.value.matches()
        else:
            print(f"WARNING: Expression.matches: self.value is None!")


class Function(Valued):

    def __init__(self, matcher:Any, name:str, p:YaccProduction )->None:
        self.matcher = matcher # atm, circular dep
        self.name:str = name
        self.function_or_equality = p
        self.parent:YaccProduction = None
        self.id:str = None

    def __str__(self) -> str:
        return f"""\nFunc: {self.name}({self.function_or_equality}) """

    def to_value(self) -> bool:
        id = self.get_id()
        if self.function_or_equality:
            if not self.function_or_equality.matches():
                return False
        print("WARNING: function getting to_value defaulting to True")
        return True # leave this for now for testing

    def get_id(self):
        return ParserUtility.get_id(self)

@dataclass
class Equality(Matchable):
    matcher:Any
    left:Any
    right:Any
    parent:Any = None

    def __str__(self) -> str:
        return f"""Equality: {self.left}={self.right} """

    def matches(self) -> bool:
        if not self.left or not self.right:
            return False
        return self.left.to_value() == self.right.to_value()


@dataclass
class Term(Valued):
    matcher:Any
    value:Any

    def __str__(self) -> str:
        return f"""Term: {self.value} """

    def to_value(self) -> Any:
        return self.value



class Variable(Valued):
    matcher:Any
    name:Any
    parent:Any = None

    def __init__(self, matcher, name) -> None:
        self.matcher = matcher
        self.name = name

    def __str__(self) -> str:
        return f"""Var: {self.name} """

    def to_value(self) -> Any:
        # need a way to auto increment vars - e.g. count(x=y)
        var = self.matcher.get_variable(self.name)
        return var

@dataclass
class Header(Valued):
    matcher:Any
    name:Any
    parent:Any = None

    def __str__(self) -> str:
        return f"""Header: {self.name} """

    def to_value(self) -> Any:
        if isinstance(self.name, int):
            if self.name >= len(self.matcher.line) :
                return None
            else:
                return self.matcher.line[self.name]
        else:
            #
            # need some defensiveness here!
            #
            n = self.matcher.headers.index(self.name)
            return self.matcher.line[n]

    def matches(self) -> bool:
        return not self.to_value is None


