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
from csvpath.util.config_exception import ConfigurationException

#   from csvpath.util.log_utility import LogUtility
#   LogUtility.log_brief_trace()


class Arg:
    def __init__(self, *, types: list[Type] = None, actuals: list[Type] = None):
        self.is_noneable = False
        self.types: list[Type] = types or [None]
        self.actuals: list[Type] = actuals or [None]

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
        # ts can be None if constructed bare.
        if ts and Any in ts:
            ts.remove(Any)
            ts.append(Term)
            ts.append(Function)
            ts.append(Header)
            ts.append(Variable)
            ts.append(Reference)
            ts.append(Equality)
        if ts and None in ts:
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

    def __eq__(self, other):
        if self is other:
            return True
        if not type(self) is type(other):
            return False
        if other.is_noneable != self.is_noneable:
            return False
        if len(self.types) != len(other.types):
            return False
        if len(self.actuals) != len(other.actuals):
            return False
        for t in self.types:
            if t not in other.types:
                return False
        for a in self.actuals:
            if a not in other.actuals:
                return False
        return True


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
        if len(self._args) > self.max_length and self.max_length != -1:
            self.max_length = len(self._args)
        return arg

    @property
    def args(self) -> List[Arg]:
        return self._args

    @property
    def args_count(self) -> int:
        return len(self._args)

    @property
    def max_length(self) -> int:
        return self._max_length

    @max_length.setter
    def max_length(self, ml: int) -> None:
        self._max_length = ml

    @property
    def min_length(self) -> int:
        return self._min_length

    @min_length.setter
    def min_length(self, ml: int) -> None:
        self._min_length = ml

    # just for fluency
    def length(self, maxlength=-1) -> Self:
        self.max_length = maxlength
        return self

    def _set_min_length(self):
        self.min_length = 0
        foundnone = False
        for a in self._args:
            if a.is_noneable is True:
                foundnone = True
            else:
                if foundnone:
                    raise ConfigurationException(
                        "Cannot have a non-noneable arg after a nullable arg"
                    )
                self._min_length += 1

    # ----------------------------
    # validate at parse time
    # ----------------------------

    def _validate_length(self, siblings: List[Matchable]) -> None:
        self._set_min_length()
        s = len(siblings)
        if s < self._min_length or (s > len(self._args) and self.max_length != -1):
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
        if len(self._args) < len(siblings) and (
            self.max_length == -1 or self.max_length >= len(siblings)
        ):
            lastindex = len(self._args) - 1
            for i, s in enumerate(siblings):
                if i >= len(self._args):
                    a = self.arg()
                    last = self._args[lastindex]
                    a.types = last.types  # we have a sib so None doesn't make sense
                    a.actuals = last.actuals
                    if not a.types:
                        a.types = []
                    if not a.actuals:
                        a.actuals = []
                    if None not in a.types:
                        a.is_noneable = True
        elif (
            len(self._args) > len(siblings)
            # and we're in-bounds
            and len(siblings) > self.min_length
            and len(siblings) <= self.max_length
        ):
            args = []
            for a in range(0, len(siblings)):
                args.append(self._args[a])
            self._args = args
            self.max_length = len(self._args)

    def validate(self, siblings: List[Matchable]) -> None:
        b = self._validate_length(siblings)
        if b is False:
            return False
        self._pad_or_shrink(siblings)
        for i, s in enumerate(siblings):
            t = tuple(self._args[i].types)
            #
            # really need issubclass?
            #   not issubclass(s.__class__, t)
            if not isinstance(s, t):
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
        if len(self._argsets) == 0 and len(siblings) == 0:
            return
        if len(self._argsets[0]._args) == 0 and len(siblings) == 0:
            return
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
