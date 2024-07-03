from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.equality import Equality
import json

class IsInstance(Function):

    def to_value(self) -> Any:
        return self.matches()

    def matches(self) -> bool:
        if len(self.children) != 1:
            raise ChildrenException("no children. there must be 1 equality child with 2 non-equality children")
        child = self.children[0]
        if not isinstance(child, Equality):
            raise ChildrenException("must be 1 equality child with 2 non-equality children")
        left = child.left
        right = child.right
        thevalue = left.to_value()
        thetype = right.to_value()

        print(f"IsInstance.to_value: {thevalue}, {thetype}")
        if thetype == "int":
            return self.to_int(thevalue)
        elif thetype == "float":
            return self.to_fload(thevalue)
        elif thetype == "str":
            return self.to_str(thevalue)
        elif thetype == "complex":
            return self.to_complex(thevalue)
        elif thetype == "bool":
            return self.to_bool(thevalue)
        elif thetype == "json":
            return self.to_json(thevalue)
        elif thetype == "usd":
            return self.to_usd(thevalue)
        elif thetype == "datetime":
            ret =  self.to_usd(thevalue)
            print (f"datetime is good!")
            return ret
        else:
            raise Exception(f'''the type must one of:
                                "int","float","str","bool",
                                "complex","json","usd",
                                "datetime, not {right}"
                                ''')

    def to_int(self, v) -> bool:
        try:
            int(v)
        except:
            return False
        return True

    def to_float(self, v) -> bool:
        try:
            float(v)
        except:
            return False
        return True

    def to_str(self, v) -> bool:
        return isinstance(v, str)

    def to_complex(self, v) -> int:
        try:
            complex(v)
        except:
            return False
        return True

    def to_bool(self, v) -> bool:
        try:
            bool(v)
        except:
            return False
        return True

    def to_json(self, v) -> bool:
        try:
            json.loads(v)
        except:
            return False
        return True

    def to_usd(self, v) -> bool:
        try:
            float(f"{v}".replace('$', '').replace(',', ''))
        except:
            return False
        return True

    def to_datetime(self, v) -> bool:
        try:
            print(f"IsInstance.to_datetime: {v}")
            dateutil.parser.parse(f"{v}")
            print(f"ok date!")
        except Exception as e:
            print(e)
            return False
        return True

