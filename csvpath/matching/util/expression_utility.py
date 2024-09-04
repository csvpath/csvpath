import hashlib

from typing import Tuple, Any


class ExpressionUtility:
    @classmethod
    def is_none(self, v: Any) -> bool:
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
    def to_int(self, v: Any) -> float:
        if v is None:
            return 0
        if v is True:
            return 1
        elif v is False:
            return 0
        if type(v) is int:
            # still convert jic
            return int(v)
        v = f"{v}".strip()
        if v == "":
            return 0
        try:
            v = int(v)
            return v
        except ValueError:
            v = v.replace(",", "")
            v = v.replace(";", "")
            v = v.replace("$", "")
            v = v.replace("€", "")
            v = v.replace("£", "")
            if f"{v}".find(".") > -1:
                v = float(v)
            # if this doesn't work we'll handle the higher in the stack
            return int(v)

    @classmethod
    def to_float(self, v: Any) -> float:
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
            v = v.replace(",", "")
            v = v.replace(";", "")
            v = v.replace("$", "")
            v = v.replace("€", "")
            v = v.replace("£", "")
        #
        # if this doesn't work we'll presumably handle the error above
        #
        return float(v)

    @classmethod
    def ascompariable(self, v: Any) -> Any:
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
        if v is None:
            ret = False
        elif v is False:
            ret = False
        elif f"{v}".lower().strip() == "false":
            ret = False
        elif v is True:
            ret = True
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
        quals = None
        if dot > -1:
            quals = []
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
    def is_simple_name(cls, s: str) -> bool:
        ret = False
        if s.isdigit():
            return False
        elif s.isalnum():
            ret = True
        elif s.find(".") > -1:
            dotted = True
            dots = s.split(".")
            for d in dots:
                dotted = cls._is_underscored_or_simple(d)
                if dotted is False:
                    break
            ret = dotted
        else:
            ret = cls._is_underscored_or_simple(s)
        return ret

    @classmethod
    def _is_underscored_or_simple(cls, s: str) -> bool:
        us = s.split("_")
        ret = True
        for u in us:
            if u.strip() == "":
                continue
            if not u.isalnum():
                ret = False
                break
        return ret

    @classmethod
    def get_id(self, thing):
        # gets a durable ID so funcs like count() can persist throughout the scan
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
    def get_my_expression(self, thing):
        p = thing.parent
        ret = p
        while p:
            p = p.parent
            if p:
                ret = p
        return ret
