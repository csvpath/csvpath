from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.equality import Equality
import json
from dateutil import parser
from numbers import Number

class Or(Function):

    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        else:
            skip.append(self)
        if len(self.children) != 1:
            raise ChildrenException("no children. there must be 1 equality child with 2 non-equality children")
        child = self.children[0]
        if not isinstance(child, Equality):
            raise ChildrenException("must be 1 equality child with 2 non-equality children")

        siblings = child.commas_to_list()
        ret = False
        for sib in siblings:
            if sib.matches(skip=skip):
                ret = True
        return ret

        """
        es = self.matcher.expressions
        #breakpoint()
        for i, exp in enumerate(es):
            print(f"if all match: {i}:{left.name}: {exp.__class__}[1]:{exp[1]}")
            if self.parent == exp[0]:
                print("found my parent")
                continue
            elif exp[1]:
                print("found a True expression")
                continue
            elif exp[1] is False:
                print("found a False expression")
                return False
            else:
                print("found an expression to check")
                exp[1] = exp[0].matches(skip=skip)
                print(f"the result is {exp[1]}")

            if not exp[1]:
                return False
            else:
                print("doing matches() on my children")
                ret = child.matches(skip=skip)
        """
        return ret










