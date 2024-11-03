import hashlib
import math
import datetime
import dateutil.parser
from typing import Tuple, Any, List
from .exceptions import MatchException


class EmptyString(str):
    pass


class ExpressionUtility:

    EMPTY_STRING = EmptyString()
    """ an empty string between two delimiters is essentially the same as NULL.
        in some cases we want an empty string to just be an empty string. see
        length(). to do that, we put args.EMPTY_STRING into the actuals list. """

    @classmethod
    def _numeric_string(self, i) -> str:
        s = f"{i}"
        s = s[len(s) - 1]
        si = int(s)
        if abs(si) == 1:
            return f"{i}st"
        elif abs(si) == 2:
            return f"{i}nd"
        elif abs(si) == 3:
            return f"{i}rd"
        else:
            return f"{i}th"

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
    def is_number(cls, v: Any) -> bool:
        if v is None:
            return False
        if v is True or v is False:
            return False
        if f"{v}".strip() == "":
            return False
        try:
            cls.to_int(v)
            return True
        except Exception:
            pass
        try:
            cls.to_float(v)
            return True
        except Exception:
            return False

    @classmethod
    def is_none(cls, v: Any) -> bool:
        if v is None:
            return True
        elif v == "None":
            return True
        elif cls.isnan(v) or v == "nan":
            return True
        elif f"{v}".strip() == "":
            return True
        return False

    @classmethod
    def is_empty(cls, v):
        ret = cls.is_none(v)
        if not ret and (isinstance(v, list) or isinstance(v, tuple)):
            if len(v) == 0:
                ret = True
            else:
                for item in v:
                    ret = cls.is_empty(item)
                    if not ret:
                        break
        elif not ret and isinstance(v, dict):
            ret = len(v) == 0
        return ret

    @classmethod
    def isnan(cls, v) -> bool:
        try:
            return math.isnan(v)
        except TypeError:
            return False

    @classmethod
    def to_int(cls, v: Any, should_i_raise=True) -> float:
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
            pass
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
        try:
            if f"{v}".find(".") > -1:
                v = float(v)
            # if this doesn't work, handle the error upstack
            return int(v)
        except ValueError as e:
            if should_i_raise is True:
                raise ValueError("ExpressionUtility cannot convert '{v}' to int") from e
            else:
                return v

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
    def to_date(cls, v: Any) -> datetime.date:
        if isinstance(v, datetime.datetime):
            return v.date()
        if isinstance(v, datetime.date):
            return v
        if v is not None:
            try:
                adate = dateutil.parser.parse(f"{v}")
                return adate.date()
            except Exception:
                pass
        return v

    @classmethod
    def to_datetime(cls, v: Any) -> datetime.datetime:
        if isinstance(v, datetime.datetime):
            return v
        if v is not None:
            try:
                return dateutil.parser.parse(f"{v}")
            except Exception:
                pass
        return v

    @classmethod
    def is_date_type(cls, v) -> bool:
        v = cls.to_date(v)
        if isinstance(v, (datetime.date, datetime.datetime)):
            return True
        return False

    @classmethod
    def to_bool(cls, v: Any) -> bool:
        if v is True:
            return True
        if v is False:
            return False
        if v is None:
            return False
        if v == 0 or v == "0":
            return False
        if v == 1 or v == "1":
            return True
        if f"{v}".strip().lower() == "true":
            return True
        if f"{v}".strip().lower() == "false":
            return False
        return v

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
    def is_one_of(cls, a, acts: tuple) -> bool:
        if acts is None:
            return False
        if a is None and None not in acts:
            return False
        if a is None and None in acts:
            return True
        if len(acts) == 0:
            return False
        actst = acts[:]
        if None in actst:
            actst.remove(None)
        #
        # in some cases we use "" as a signal that we don't
        # want to treat "" as None. that can result in it showing
        # up here.
        #
        if cls.EMPTY_STRING in actst:
            actst.remove(cls.EMPTY_STRING)
        actst = tuple(actst)
        if isinstance(a, actst):
            # empty == NULL in CSV so we disallow an empty string here
            if (
                isinstance(a, str)
                and cls.is_empty(a)
                and None not in acts
                and cls.EMPTY_STRING not in acts
            ):
                return False
            else:
                return True
        for act in acts:
            if act is None:
                if cls.is_none(a):
                    return True
            elif act == int:
                try:
                    cls.to_int(a)
                    return True
                except Exception:
                    continue
            elif act == float:
                try:
                    cls.to_float(a)
                    return True
                except Exception:
                    continue
            elif act == datetime.date:
                _ = ExpressionUtility.to_date(a)
                if isinstance(_, datetime.date):
                    return True
            elif act == datetime.datetime:
                _ = ExpressionUtility.to_date(a)
                if isinstance(_, datetime.datetime):
                    return True
            elif act == list:
                if isinstance(a, list):
                    return True
            elif act == tuple:
                if isinstance(a, tuple):
                    return True
            elif act == dict:
                if isinstance(a, dict):
                    return True
            elif act == bool:
                # to_bool returns a if a is not booleanizable
                _ = ExpressionUtility.to_bool(a)
                if _ in [True, False]:
                    return True
        return False

    @classmethod
    def _parse_quoted(cls, name: str):
        c = None
        names = []
        aname = ""
        QUOTED = 1
        UNQUOTED = 0
        state = UNQUOTED
        for i, c in enumerate(name):
            if c == '"':
                if state == UNQUOTED:  # entering
                    state = QUOTED
                    if aname != "":
                        names.append(aname)
                else:  # exiting
                    state = UNQUOTED
                    if aname != "":
                        names.append(aname)
                aname = ""
            elif c == ".":
                if state == QUOTED:
                    aname = aname + c
                else:
                    if aname != "":
                        names.append(aname)
                    aname = ""
            else:
                aname = aname + c
        if aname is not None and aname.strip() != "":
            names.append(aname)
        return names[0], names[1:] if len(names) > 0 else []

    @classmethod
    def get_name_and_qualifiers(cls, name: str) -> Tuple[str, list]:
        aname = None
        quals = None
        if name.find('"') > -1:
            aname, quals = cls._parse_quoted(name)
        else:
            aname = name
            dot = f"{name}".find(".")
            quals = []
            if dot > -1:
                aname = name[0:dot]
                somequals = name[dot + 1 :]
                cls._next_qual(quals, somequals)
        if aname is None or aname.strip() == "":
            raise ValueError("Name variable 'aname' cannot be None or empty")
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
    def my_chain(cls, thing):
        ancs = []
        p = thing.parent
        while p is not None:
            ancs.append(p)
            p = p.parent
        chain = cls.name_or_class(thing)
        for o in ancs:
            n = cls.name_or_class(o)
            if n != "":
                chain = f"{n}.{chain}"
        return chain

    @classmethod
    def name_or_class(cls, thing, show_eq_and_exp=False):
        if not show_eq_and_exp and f"{type(thing)}".find("Equality") > -1:
            return ""
        if not show_eq_and_exp and f"{type(thing)}".find("Expression") > -1:
            return ""
        if not hasattr(thing, "name"):
            return cls.simple_class_name(thing)
        if f"{type(thing)}".find("Term") != -1:
            return thing.to_value()
        if thing.name is None:
            return cls.simple_class_name(thing)
        return thing.name

    @classmethod
    def simple_class_name(cls, thing):
        ts = f"{type(thing)}"
        return ts[ts.rfind(".") + 1 : ts.rfind("'")]

    @classmethod
    def get_my_expression(cls, thing):
        p = thing.parent
        ret = p
        while p:
            p = p.parent
            if p:
                ret = p
        return ret

    @classmethod
    def get_ancestor(cls, thing, aclass):
        """looks for an ancestor of thing that matches a class or classname"""
        p = thing.parent
        while p is not None:
            if isinstance(aclass, str):
                ps = f"{type(p)}"
                if ps.find(aclass) > -1:
                    return p
            elif isinstance(p, aclass):
                return p
            p = p.parent
        return None

    @classmethod
    def get_my_expressions_index(cls, thing) -> int:
        e = cls.get_my_expression(thing)
        for i, es in enumerate(thing.matcher.expressions):
            if es[0] == e:
                return i

    @classmethod
    def any_of_my_descendants(cls, expression, skips) -> bool:
        for c in skips:
            if cls.get_my_expression(c) == expression:
                return True
        return False
