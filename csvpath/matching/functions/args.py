# pylint: disable=C0114
from typing import Type, List, Any, Self
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.productions.term import Term
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.header import Header
from csvpath.matching.functions.function import Function
from csvpath.matching.productions.reference import Reference
from csvpath.matching.productions.equality import Equality
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..util.exceptions import ChildrenException
from csvpath.util.config_exception import ConfigurationException
from csvpath.util.printer import Printer

#   from csvpath.util.log_utility import LogUtility
#   LogUtility.log_brief_trace()


class Arg:
    def __init__(self, *, types: list[Type] = None, actuals: list[Type] = None):
        self.is_noneable = False
        self._types = None
        self._x_actuals = None
        self.types: list[Type] = types or [None]
        self.actuals: list[Type] = actuals or []

    def __str__(self) -> str:
        return f"Arg (types:{self.types}, actuals:{self.actuals})"

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
        return self._x_actuals

    @actuals.setter
    def actuals(self, acts: list[Type]) -> None:
        self._x_actuals = acts

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
    def __init__(self, maxlength=-1, *, parent=None):
        self._args = []
        self._max_length = maxlength
        self._min_length = -1
        self._parent = parent

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
        return True

    def _pad_or_shrink(self, siblings: List[Matchable]) -> None:
        # already validated min_length. we know we have that
        # likewise max
        if len(self._args) < len(siblings) and (
            self.max_length == -1 or self.max_length >= len(siblings)
        ):
            #
            # we pad the args
            #
            lastindex = len(self._args) - 1
            for i, s in enumerate(siblings):
                if i >= len(self._args):
                    a = self.arg()
                    last = self._args[lastindex]
                    a.types = last.types  # we have a sib so None doesn't make sense
                    a.actuals = last.actuals[:] if last.actuals is not None else None
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
            if not isinstance(s, t):
                return False
        return True

    # ----------------------------
    # match actuals line-by-line
    # ----------------------------

    def matches(self, actuals: List[Any]):
        mismatches = []
        found = len(actuals) == 0
        a = None
        i = 0
        self._parent._csvpath.logger.debug(
            "Beginning matches on arg actuals to expected actuals"
        )
        self._parent._csvpath.logger.debug("Actuals: %s", str(actuals))
        for i, a in enumerate(actuals):
            if i >= len(self._args):
                #
                # this happens when we cannot pad an argset (because a non-1
                # limit was set) and there is another argset that has more args.
                # we need to add a message to the mismatch list to indicate that
                # there was no match. since there may be a match on another arg
                # we'll want to not provide the mismatches unless we completely
                # fail to match.
                #
                mismatches.append(
                    f"No match for argset {self._parent.argsets.index(self)}. More actuals than args."
                )
                break
            arg = self._args[i]
            #
            # we can't validate arg if we have no actuals expectations.
            # this is a way to disable line-by-line validation -- just
            # remove the expectations from the args
            #
            self._parent._csvpath.logger.debug("Checking arg[%i]: %s", i, arg)
            if not arg or not arg.actuals or len(arg.actuals) == 0:
                if self._parent and self._parent._csvpath:
                    self._parent._csvpath.logger.debug(
                        "No expectations to validate actual values against"
                    )
                found = True
                break
            if Any in arg.actuals:
                self._parent._csvpath.logger.debug("Found Any so we're done")
                found = True
                break
            _ = ExpressionUtility.is_one_of(a, arg.actuals)
            print(f"{a} is_one_of {arg.actuals} returns {_}")
            self._parent._csvpath.logger.debug(
                "'%s' is_one_of %s returns %s", a, str(arg.actuals), _
            )
            if _ is True:
                found = True
                break
            found = False
            break
        if not found:
            mismatches.append(f"{type(a)}({a}) not allowed in arg {i}")
        else:
            mismatches = []
        return mismatches


class Args:
    EMPTY_STRING = ExpressionUtility.EMPTY_STRING

    def __init__(self, *, matchable=None):
        self._argsets = []
        self._matchable = matchable
        self._csvpath = (
            matchable.matcher.csvpath if matchable and matchable.matcher else None
        )
        #
        # validation happens before any lines are considered.
        # it is a static structure check -- did we find the correct
        # arguments for the functions when we parsed the csvpath?
        #
        self.validated = False
        #
        # matching checks the validated arguments -- the siblings --
        # values against the types expected. if we're expecting a
        # child.to_value(skips=skips) to result in an int, did it?
        #
        self.matched = False

    def argset(self, maxlength: int = -1) -> ArgSet:
        a = ArgSet(maxlength, parent=self)
        self._argsets.append(a)
        return a

    @property
    def matchable(self) -> Matchable:
        return self._matchable

    @property
    def argsets(self) -> list[ArgSet]:
        return self._argsets

    def validate(self, siblings: List[Matchable]) -> None:
        if len(self._argsets) == 0 and len(siblings) == 0:
            return
        if len(self._argsets[0]._args) == 0 and len(siblings) == 0:
            return
        #
        # we want to check all the argsets even if we find a match
        # because we need them all to be shrunk or padded for the actuals
        # matching. we only do this part once, so it's not a big lift.
        #
        good = False
        for aset in self._argsets:
            if aset.validate(siblings):
                good = True
        if not good:
            msg = "Wrong type or number of args."
            raise ChildrenException(msg)
        self.validated = True

    def matches(self, actuals: List[Any]) -> None:
        if len(self._argsets) == 0 and len(actuals) == 0:
            return
        mismatches = []
        mismatch_count = 0
        for aseti, aset in enumerate(self._argsets):
            ms = aset.matches(actuals)
            if len(ms) > 0:
                mismatch_count += 1
                mismatches += ms
        if mismatch_count == len(self._argsets):
            c = ""
            if mismatch_count == 1:
                c = "all"
            elif mismatch_count == 2:
                c = "both"
            else:
                c = f"all {mismatch_count}"
            pm = f"Mismatches with args expectations in {self.matchable.name} for {c} arg sets: {mismatches}"
            if self._csvpath:
                pm = f"{pm} at line {self._csvpath.line_monitor.physical_line_number}"
                self._csvpath.report_validation_errors(pm)
            if self._csvpath is None or self._csvpath.raise_validation_errors:
                msg = f"Wrong values of args: {actuals}. {pm}."
                raise ChildrenException(msg)
        self.matched = True