# pylint: disable=C0114
from typing import Type, List, Any, Self
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.productions.term import Term
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.header import Header
from csvpath.matching.functions.function import Function
from csvpath.matching.productions.reference import Reference
from csvpath.matching.productions.equality import Equality
from ..util.exceptions import ChildrenException
from csvpath.util.config_exceptions import ConfigurationException

#   from csvpath.util.log_utility import LogUtility
#   LogUtility.log_brief_trace()


class Arg:
    def __init__(self, *, types: list[Type] = None, actuals: list[Type] = None):
        self.is_noneable = False
        self.types: list[Type] = types
        self.actuals: list[Type] = actuals

    def __str__(self) -> str:
        return f"Arg (types:{self._types}, actuals:{self._actuals})"

    @property
    def is_noneable(self) -> bool:
        return self._noneable

    @is_noneable.setter
    def is_noneable(self, n: bool) -> None:
        self._noneable = n

    @property
    def types(self) -> list[Type]:
        return self._types

    @types.setter
    def types(self, ts: list[Type]) -> None:
        # should validate that ts is a list of classes but some research needed
        if Any in ts:
            ts.remove(Any)
            ts.append(Term)
            ts.append(Function)
            ts.append(Header)
            ts.append(Variable)
            ts.append(Reference)
            ts.append(Equality)
        if None in ts:
            self.is_noneable = True
            ts.remove(None)
        self._types = ts

    @property
    def actuals(self) -> list[Type]:
        return self._actuals

    @actuals.setter
    def actuals(self, acts: list[Type]) -> None:
        # should validate that ts is a list of classes but some research needed
        #
        # handle Any and None
        self._actuals = acts


class ArgSet:
    def __init__(self, maxlength=-1):
        self._args = []
        self._max_length = maxlength
        self._min_length = -1

    def __str__(self) -> str:
        args = ""
        for a in self._args:
            args = f"{args} {a},"
        return f"ArgSet (args:{args} max:{self._max_length})"

    # ----------------------------
    # setup time
    # ----------------------------

    def arg(self, *, types: list[Type] = None, actuals: list[Type] = None) -> Arg:
        arg = Arg(types=types, actuals=actuals)
        self._args.append(arg)
        if len(self._args) > self._max_length:
            self._max_length = len(self._args)
        return arg

    def length(self, maxlength=-1) -> Self:
        self._max_length = maxlength
        return self

    def _set_min_length(self):
        self._min_length = 0
        for a in self._args:
            # print(f"Argset: set min: a: {a}: noneable: {a.is_noneable}")
            # none in types == no Matchable
            # none in actuals == None value returned by Matchable
            if a.is_noneable is True:
                break
            else:
                # if None not in a._types:
                self._min_length += 1

    # ----------------------------
    # validate at parse time
    # ----------------------------

    def _validate_length(self, siblings: List[Matchable]) -> None:
        self._set_min_length()
        # print(f"argset.val_len: minlen: {self._min_length}, maxlen: {self._max_length}")
        s = len(siblings)
        # print(f"argset.val_len: s: {s}")
        if s < self._min_length or (s > len(self._args) and self._max_length != -1):
            return False
            """
            msg = "Expected number of arguments is {self._min_length} to"
            msg = "{msg} {self._max_length if self._max_length == -1 else 'any number'}"
            raise ChildrenException(msg)
            """
        return True

    def _pad_or_shrink(self, siblings: List[Matchable]) -> None:
        # already validated min_length. we know we have that
        # likewise max
        if len(self._args) == 0:
            for s in siblings:
                a = self.arg()
                a.types = [Any]  # we have a sib so None doesn't make sense
                a.actuals = [Any, None]

    def validate(self, siblings: List[Matchable]) -> None:
        # print(f"argset: validating: sibs: {siblings}")
        b = self._validate_length(siblings)
        # print(f"argset: vlen b: {b}")
        if b is False:
            return False
        self._pad_or_shrink(siblings)
        # print(f"argset: args: {self}")
        for i, s in enumerate(siblings):
            # print(f"argset: s: {s}; types: {self._args[i].types}")
            if not issubclass(s.__class__, tuple(self._args[i].types)):
                return False
        return True

    # ----------------------------
    # match actuals line-by-line
    # ----------------------------

    def matches(self, actuals: List[Any]):
        for i, a in enumerate(actuals):
            for j, arg in enumerate(self._args):
                # has to be class ~ class
                if Any in arg.actuals:
                    continue
                if a.__class__ not in arg.actuals:
                    return False
        return True


class Args:
    def __init__(self):
        self._argsets = []

    def argset(self, maxlength: int = -1) -> ArgSet:
        a = ArgSet(maxlength)
        self._argsets.append(a)
        return a

    def validate(self, siblings: List[Matchable]) -> None:
        # print(f"args.validate: sibs: {siblings}")
        if len(self._argsets) == 0 and len(siblings) == 0:
            return
        if len(self._argsets[0]._args) == 0 and len(siblings) == 0:
            return
        # print(f"args.validate: asets: {self._argsets}")
        for aset in self._argsets:
            if aset.validate(siblings):
                return
        msg = "Wrong type or number of args."
        raise ChildrenException(msg)

    def matches(self, actuals: List[Any]) -> None:
        if len(self._argsets) == 0 and len(actuals) == 0:
            return
        for aset in self._argsets:
            if aset.matches(actuals):
                return
        msg = "Wrong values of args."
        raise ChildrenException(msg)
