from csvpath.matching.productions.expression import Expression
from csvpath.matching.productions.equality import Equality
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.header import Header
from csvpath.matching.productions.term import Term
from csvpath.matching.functions.function import Function
from typing import Any, List


class ExpressionEncoder:
    def list_to_json(self, alist: List[Any]) -> str:
        json = "[ "
        for _ in alist:
            json = f"{json} {self.to_json(_)} "
        json = f"{json} ] "
        return json

    def simple_list_to_json(self, alist: List[Any]) -> str:
        json = "[ "
        for i, _ in enumerate(alist):
            json = f"{json} {self.to_json(_)} "
            if i < len(alist) - 1:
                json = f"{json}, "
        json = f"{json} ] "
        return json

    def valued_list_to_json(self, alist: List[List[Any]]) -> str:
        json = "[ "
        for i, _ in enumerate(alist):
            json = f"{json} {self.to_json(_[0])} "
            if i < len(alist) - 1:
                json = f"{json}, "
        json = f"{json} ] "
        return json

    def to_json(self, o):
        if o is None:
            return "None"
        json = ""
        return self._encode(json, o)

    def _encode(self, json: str, o) -> str:
        if isinstance(o, Expression):
            return self.expression(json, o)
        elif isinstance(o, Equality):
            return self.equality(json, o)
        elif isinstance(o, Function):
            return self.function(json, o)
        elif isinstance(o, Header):
            return self.header(json, o)
        elif isinstance(o, Variable):
            return self.variable(json, o)
        elif isinstance(o, Term):
            return self.term(json, o)
        elif o is None:
            return f'{json} "None" '
        else:
            raise Exception(f"what am I {o}")

    def matchable(self, json: str, m) -> str:
        json = f'{json} "base_class":"matchable", '
        json = f'{json} "parent_class":"{m.parent.__class__}", '
        json = f'{json} "value":"{m.value}", '
        json = f'{json} "name":"{m.name}", '
        json = f'{json} "children": [ '
        for i, _ in enumerate(m.children):
            json = self._encode(json, _)
            if i < len(m.children) - 1:
                json = f"{json}, "
        json = f"{json} ] "
        return json

    def expression(self, json: str, e) -> str:
        json = f"{json} " + '{ "type":"expression", '
        json = self.matchable(json, e)
        json = f"{json} " + "} "
        return json

    def equality(self, json: str, e) -> str:
        json = f"{json} " + '{ "type":"equality", '
        json = self.matchable(json, e)
        json = f'{json}, "op":"{e.op}" '
        json = f"{json} " + "} "
        return json

    def function(self, json: str, f) -> str:
        json = f"{json} " + '{ "type":"function", '
        json = self.matchable(json, f)
        json = f"{json} " + "} "
        return json

    def header(self, json: str, h) -> str:
        json = f"{json} " + '{ "type":"header", '
        json = self.matchable(json, h)
        json = f"{json} " + "} "
        return json

    def variable(self, json: str, v) -> str:
        json = f"{json} " + '{ "type":"variable", '
        json = self.matchable(json, v)
        json = f"{json} " + "} "
        return json

    def term(self, json: str, t) -> str:
        json = f"{json} " + '{ "type":"term", '
        json = self.matchable(json, t)
        json = f"{json} " + "} "
        return json
