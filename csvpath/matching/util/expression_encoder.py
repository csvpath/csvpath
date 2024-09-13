from csvpath.matching.productions import (
    Expression,
    Equality,
    Variable,
    Header,
    Term,
    Reference,
)
from csvpath.matching.functions.function import Function
from typing import Any, List


class ExpressionEncoder:
    def __init__(self):
        self.indent = []

    def push(self, s="{"):
        c = "".join(self.indent)
        self.indent.append("  ")
        return f"{s}\n{c}"

    def pop(self, s="}"):
        self.indent.pop()
        c = "".join(self.indent)
        return f"\n{c}{s}"

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
            return "None"  # pragma: no cover
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
        elif isinstance(o, Reference):
            return self.reference(json, o)
        elif o is None:
            return f'{json} "None" '  # pragma: no cover
        else:
            return f'{json} "unknown child of type {o.__class__} " '

    def matchable(self, json: str, m) -> str:
        if m.value is not None:
            json = (
                f'{json} "value":"{self._no_quotes(m.value)}" {"," if m.name else ""} '
            )
        if m.name is not None:
            json = f'{json} "name":"{m.name}"'
            json = f'{json}, "qualified_name":"{m.qualified_name}"'
            json = f'{json} {"," if m.children and len(m.children) > 0 else ""} '
        if m.children and len(m.children) > 0:
            json = f'{json} "children": [ '
            for i, _ in enumerate(m.children):
                json = self._encode(json, _)
                if i < len(m.children) - 1:
                    json = f"{json}, "
            json = f"{json} ] "
        return json

    def _no_quotes(self, v: str) -> str:
        try:
            # unwrap, if needed, then replace any inside " with '
            if v[0] == '"' or v[0] == "'":
                v = v[1:]
            if v[len(v) - 1] == '"' or v[len(v) - 1] == "'":
                v = v[0 : len(v) - 1]
            return v.replace('"', "'")
        except Exception:
            return v

    def expression(self, json: str, e) -> str:
        json = f"{json} " + f'{self.push()} "type":"expression", '
        json = self.matchable(json, e)
        json = f'{json} "matcher_id":"{e.matcher._id}"'
        json = f"{json} " + f"{self.pop()} "
        return json

    def equality(self, json: str, e) -> str:
        json = f"{json} " + f'{self.push()} "type":"equality", '
        json = self.matchable(json, e)
        json = f'{json}, "op":"{e.op}" '
        json = f"{json} " + f"{self.pop()} "
        return json

    def function(self, json: str, f) -> str:
        json = f"{json} " + f'{self.push()} "type":"function", '
        json = self.matchable(json, f)
        json = f"{json} " + f"{self.pop()} "
        return json

    def header(self, json: str, h) -> str:
        json = f"{json} " + f'{self.push()} "type":"header", '
        json = self.matchable(json, h)
        json = f"{json} " + f"{self.pop()} "
        return json

    def variable(self, json: str, v) -> str:
        json = f"{json} " + f'{self.push()} "type":"variable", '
        json = self.matchable(json, v)
        json = f"{json} " + f"{self.pop()} "
        return json

    def term(self, json: str, t) -> str:
        json = f"{json} " + f'{self.push()} "type":"term", '
        json = self.matchable(json, t)
        json = f"{json} " + f"{self.pop()} "
        return json

    def reference(self, json: str, r) -> str:
        json = f"{json} " + f'{self.push()} "type":"reference", '
        json = self.matchable(json, r)
        json = f"{json} " + f"{self.pop()} "
        return json
