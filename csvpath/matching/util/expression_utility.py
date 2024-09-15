import hashlib
import math
from typing import Tuple, Any, List


class ExpressionUtility:
    @classmethod
    def all(cls, objects: List, classlist: tuple = None) -> bool:
        if objects is None:
            return False
        if not isinstance(objects, (list, tuple)):
            return True
        if len(objects) == 0:
            return True
        #
        # check first item
        #
        if classlist is not None:
            tup = classlist
            if not isinstance(classlist, tuple):
                tup = tuple(classlist)
            if not isinstance(objects[0], tup):
                return False
        #
        # check all items against each other
        #
        for i, o in enumerate(objects):
            if i == 0:
                continue
            if isinstance(o, type(objects[i - 1])):
                continue
            return False
        return True

    @classmethod
    def is_none(cls, v: Any) -> bool:
        if v is None:
            return True
        elif v == "None":
            return True
        elif f"{v}" == "nan":
            return True
        elif f"{v}".strip() == "":
            return True
        return False

    @classmethod
    def isnan(cls, v) -> bool:
        try:
            return math.isnan(v)
        except TypeError:
            return False

    @classmethod
    def to_int(cls, v: Any) -> float:
        if v is None:
            return 0
        if v is True:
            return 1
        elif v is False:
            return 0
        if type(v) is int:
            return v
        v = f"{v}".strip()
        if v == "":
            return 0
        try:
            v = int(v)
            return v
        except ValueError:
            if v.find(",") == len(v) - 3:
                a = v[0 : v.find(",")]
                a += "."
                a += v[v.find(",") + 1 :]
                v = a
            v = v.replace(",", "")
            v = v.replace(";", "")
            v = v.replace("$", "")
            v = v.replace("€", "")
            v = v.replace("£", "")
            if f"{v}".find(".") > -1:
                v = float(v)
            # if this doesn't work, handle upstack
            return int(v)

    @classmethod
    def to_float(cls, v: Any) -> float:
        if v is None:
            return float(0)
        if type(v) is int:
            return float(v)
        if v is True:
            return float(1)
        elif v is False:
            return float(0)
        v = f"{v}".strip()
        if v == "":
            return float(0)
        try:
            v = float(v)
            return v
        except Exception:
            if v.find(",") == len(v) - 3:
                a = v[0 : v.find(",")]
                a += "."
                a += v[v.find(",") + 1 :]
                v = a
            v = v.replace(",", "")
            v = v.replace(";", "")
            v = v.replace("$", "")
            v = v.replace("€", "")
            v = v.replace("£", "")
        # if this doesn't work, handle upstack
        return float(v)

    @classmethod
    def ascompariable(cls, v: Any) -> Any:
        if v is None:
            return v
        elif v is False or v is True:
            return v
        s = f"{v}".lower().strip()
        if s == "true":
            return True
        elif s == "false":
            return False
        elif isinstance(v, int) or isinstance(v, float):
            return v
        else:
            try:
                return float(v)
            except Exception:
                return s

    @classmethod
    def asbool(cls, v) -> bool:
        ret = None
        if v in [False, None] or cls.isnan(v):
            ret = False
        elif v in [True, [], (), {}]:
            # an empty set is a valid, positive thing in its own right
            ret = True
        elif f"{v}".lower().strip() == "false":
            ret = False
        elif f"{v}".strip() == "nan" or f"{v}".strip() == "NaN":
            # we don't lowercase. nan is very specific.
            ret = False
        elif f"{v}".lower().strip() == "true":
            ret = True
        else:
            try:
                ret = bool(v)
            except (TypeError, ValueError):
                ret = True  # we're not None so we exist
        return ret

    @classmethod
    def get_name_and_qualifiers(cls, name: str) -> Tuple[str, list]:
        aname = name
        dot = f"{name}".find(".")
        quals = []
        if dot > -1:
            aname = name[0:dot]
            somequals = name[dot + 1 :]
            cls._next_qual(quals, somequals)
        return aname, quals

    @classmethod
    def _next_qual(cls, quals: list, name) -> None:
        dot = name.find(".")
        if dot > -1:
            aqual = name[0:dot]
            name = name[dot + 1 :]
            quals.append(aqual)
            cls._next_qual(quals, name)
        else:
            quals.append(name)

    @classmethod
    def get_id(cls, thing):
        # gets a durable ID so funcs like count() can persist
        # throughout the scan. for most purposes this is more
        # than we need.
        id = str(thing)
        p = thing.parent
        while p:
            id = id + str(p)
            if p.parent:
                p = p.parent
            else:
                break
        return hashlib.sha256(id.encode("utf-8")).hexdigest()

    @classmethod
    def get_my_expression(cls, thing):
        p = thing.parent
        ret = p
        while p:
            p = p.parent
            if p:
                ret = p
        return ret
