from typing import Any, List, Dict
from .function import Function
from ..productions import Equality, Term
import hashlib

# from ..util.lark_print_parser import LarkPrintParser, LarkPrintTransformer
from ..util.print_parser import PrintParser


class Print(Function):
    def check_valid(self) -> None:
        self.validate_one_or_two_args(
            one=[Term], left=[Term], right=[Function, Equality]
        )
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            child = None
            if isinstance(self.children[0], Equality):
                child = self.children[0].left
            else:
                child = self.children[0]
            string = child.to_value()
            parser = PrintParser(self.matcher.csvpath)
            self.value = parser.transform(string)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            right = None
            if isinstance(self.children[0], Equality):
                right = self.children[0].right
            om = self.has_onmatch()
            if not om or self.line_matches():
                if self.onchange:
                    id = self.get_id()
                    v = self.matcher.get_variable(id)
                    me = self.to_value()
                    me = hashlib.sha256(me.encode("utf-8")).hexdigest()
                    if me == v:
                        pass
                    else:
                        self.matcher.csvpath.print(f"{self.to_value()}")
                    self.matcher.set_variable(id, value=me)
                else:
                    self.matcher.csvpath.print(f"{self.to_value()}")
                if right:
                    right.matches(skip=skip)
            self.match = True
        return self.match
