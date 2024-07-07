from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.equality import Equality
from dateutil import parser
from numbers import Number


class IsInstance(Function):
    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self.value is not None:
            return self.value
        elif self in skip:
            return True
        if len(self.children) != 1:
            raise ChildrenException(
                "no children. there must be 1 equality child with 2 non-equality children"
            )
        child = self.children[0]
        if not isinstance(child, Equality):
            raise ChildrenException(
                "must be 1 equality child with 2 non-equality children"
            )
        left = child.left
        right = child.right
        thevalue = left.to_value(skip=skip)
        thetype = right.to_value(skip=skip)
        self.value = self._get_match_value(thetype, thevalue)
        return self.value

    def _get_match_value(self, thetype, thevalue) -> bool:
        ret = False
        if thetype == "int":
            try:
                v = int(thevalue)
                ret = f"{v}" == f"{thevalue}"
            except Exception:
                pass
        elif thetype == "float":
            try:
                v = float(thevalue)
                ret = f"{v}" == f"{thevalue}"
            except Exception:
                pass
        elif thetype == "str":
            v = str(thevalue)
            ret = f"{v}" == f"{thevalue}"
        elif thetype == "complex":
            try:
                v = complex(thevalue)
                ret = f"{v}" == f"{thevalue}"
            except Exception:
                pass
        elif thetype == "bool":
            v = isinstance(thevalue, bool)
            if not v:
                if thevalue == 1 or thevalue == 0:
                    v = True
                if thevalue == "None":
                    v = True
            ret = v
        elif thetype == "usd":
            ret = self.to_usd(thevalue)
        elif thetype == "datetime":
            ret = self.to_datetime(thevalue)
        else:
            raise Exception(
                f"""the type must one of:
                                "int","float","str","bool",
                                "complex","usd","datetime, not {thetype}"
                                """
            )
        return ret

    def to_usd(self, v) -> bool:
        if isinstance(v, Number):
            return False
        try:
            float(f"{v}".replace("$", "").replace(",", ""))
        except Exception:
            return False
        v = v.strip().lower()
        if v[0] == "$":
            return True
        return False

    def to_datetime(self, v) -> bool:
        try:
            parser.parse(f"{v}")
        except Exception as e:
            print(e)
            return False
        return True
