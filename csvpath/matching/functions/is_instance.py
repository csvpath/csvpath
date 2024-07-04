from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.equality import Equality
import json
from dateutil import parser
from numbers import Number

class IsInstance(Function):

    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self,*, skip=[]) -> bool:
        if self in skip:
            return True
        if len(self.children) != 1:
            raise ChildrenException("no children. there must be 1 equality child with 2 non-equality children")
        child = self.children[0]
        if not isinstance(child, Equality):
            raise ChildrenException("must be 1 equality child with 2 non-equality children")
        left = child.left
        right = child.right
        thevalue = left.to_value(skip=skip)
        thetype = right.to_value(skip=skip)

        ret = False
        if thetype == "int":
            try :
                v = int(thevalue)
                ret = f"{v}" == f"{thevalue}"
            except:
                pass
        elif thetype == "float":
            try:
                v = float(thevalue)
                ret = f"{v}" == f"{thevalue}"
            except:
                pass
        elif thetype == "str":
            v = str(thevalue)
            ret = f"{v}" == f"{thevalue}"
        elif thetype == "complex":
            try:
                v = complex(thevalue)
                ret = f"{v}" == f"{thevalue}"
            except:
                pass
        elif thetype == "bool":
            v = isinstance( thevalue, bool)
            if not v:
                if thevalue == 1 or thevalue == 0:
                    v = True
                if thevalue == "None":
                    v = True
            ret = v
            """
            # improving the lexer to support JSON isn't worth it at this time.
            elif thetype == "json":
                try:
                    json.loads(thevalue)
                except:
                    ret = False
                ret = True
            """
        elif thetype == "usd":
            ret = self.to_usd(thevalue)
        elif thetype == "datetime":
            ret =  self.to_datetime(thevalue)
        else:
            raise Exception(f'''the type must one of:
                                "int","float","str","bool",
                                "complex","json","usd",
                                "datetime, not {right}"
                                ''')
        return ret

    def to_usd(self, v) -> bool:
        if isinstance(v, Number):
            return False
        try:
            float(f"{v}".replace('$', '').replace(',', ''))
        except:
            return False
        v = v.strip().lower()
        if v[0] == '$':
            return True
        return False

    def to_datetime(self, v) -> bool:
        try:
            parser.parse(f"{v}")
        except Exception as e:
            print(e)
            return False
        return True

