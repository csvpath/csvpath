from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality, Term


class Lookup(Function):
    def to_value(self, *, skip=[]) -> Any:
        if not self.value:
            if len(self.children) != 1:
                raise ChildrenException("no children. there must be 1 child")
            child = self.children[0]
            if not isinstance(child, Equality):
                raise ChildrenException("Must be an equality child with op=','")

            siblings = child.commas_to_list()
            if len(siblings) != 4:
                raise ChildrenException(
                    "Must be 4 sibling children of Lookup separated by ','"
                )
            #
            # name of collection & collector
            # value to look_up
            # column to look to
            # column with the new value, if found
            #
            cs = self.matcher.csvpath.csvpaths
            if cs is None:
                raise Exception("No CsvPaths found")

            name = siblings[0].to_value()
            value = siblings[1].to_value()
            lookup_col = siblings[2].to_value()
            return_col = siblings[3].to_value()

            lines = cs.get_named_collection(name)
            c = cs.get_named_collector(name)
            if not isinstance(lookup_col, int):
                lookup_col = c.header_index(lookup_col)
            if not isinstance(return_col, int):
                return_col = c.header_index(return_col)

            if lookup_col >= len(lines) or lookup_col < 0:
                raise Exception(f"The lookup column index is not valid: {lookup_col}")
            if return_col >= len(lines) or return_col < 0:
                raise Exception(f"The return column index is not valid: {return_col}")

            for _ in lines:
                if f"{_[lookup_col]}".strip() == f"{value}".strip():
                    self.value = _[return_col]
                    break
                if self.value is None:
                    self.value is value
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return True
