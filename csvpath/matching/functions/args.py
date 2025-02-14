# pylint: disable=C0114
from typing import Type, List, Any
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.productions.term import Term
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.header import Header
from csvpath.matching.functions.function import Function
from csvpath.matching.productions.reference import Reference
from csvpath.matching.productions.equality import Equality
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.util.config_exception import ConfigurationException
from ..util.exceptions import ChildrenException, MatchException
from .args_helper import ArgumentValidationHelper


class Arg:
    def __init__(
        self, *, name: str = None, types: list[Type] = None, actuals: list[Type] = None
    ):
        self.is_noneable = False
        self._types = None
        self._name = name
        self._x_actuals = None
        self.types: list[Type] = types or [None]
        self.actuals: list[Type] = actuals or []

    def __str__(self) -> str:
        return f"Arg (types:{self.types}, actuals:{self.actuals})"

    #
    # noneable means optional arg, not None value
    #
    @property
    def is_noneable(self) -> bool:
        return self._noneable

    @is_noneable.setter
    def is_noneable(self, n: bool) -> None:
        self._noneable = n

    @property
    def name(self) -> str:
        return self._name

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

    def arg(
        self, *, name: str = None, types: list[Type] = None, actuals: list[Type] = None
    ) -> Arg:
        arg = Arg(name=name, types=types, actuals=actuals)
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
    def length(self, maxlength=-1):
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

    def validate_structure(self, siblings: List[Matchable]) -> None | str:
        b = self._validate_length(siblings)
        if b is False:
            return "incorrect number of args"
        self._pad_or_shrink(siblings)
        for i, s in enumerate(siblings):
            t = tuple(self._args[i].types)
            if not isinstance(s, t):
                ii = i + 1
                return f"arg {ii} is an unexpected type: {type(s)}"
        return None

    # ----------------------------
    # match actuals line-by-line
    # ----------------------------

    def matches(self, actuals: List[Any]):
        mismatches = []
        found = len(actuals) == 0
        a = None
        i = 0
        self._parent.csvpath.logger.debug(
            "Beginning matches on arg actuals to expected actuals for argset %s",
            self.argset_number,
        )
        self._parent.csvpath.logger.debug("Actuals: %s", str(actuals))
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
                m = "Args do not match expected"
                if len(self._parent.argsets) > 1:
                    m = f"{m} in argset {self.argset_number}"
                mismatches.append(m)
                break
            arg = self._args[i]
            #
            # in principle we would want to avoid any case where we don't have an arg
            # or the arg's actuals are none
            # -- and ---
            # if the arg exists but has [] elements treat it as a requirement that no
            # optional values should be passed in on that arg in that particular use
            # case.
            #
            # however, that approach a) breaks stuff i'd like to not break atm, and b)
            # the only use case today (in empty()) is obviated by a second arg set
            # that would in essence override the [] actuals in the first argset. so
            # we have no case. given that, letting this idea go until it resurfaces
            # in a more practical way.
            #
            self._parent.csvpath.logger.debug("Checking arg[%i]: %s", i, arg)
            #
            # start orig w/orig comment:
            # we can't validate arg if we have no actuals expectations.
            # this is a way to disable line-by-line validation -- just
            # remove the expectations from the args
            #
            if not arg or not arg.actuals or len(arg.actuals) == 0:
                if self._parent and self._parent.csvpath:
                    self._parent.csvpath.logger.debug(
                        "No expectations to validate actual values against in argset {self.argset_number}"
                    )
                found = True
                break
            #
            # end orig
            #
            if Any in arg.actuals:
                self._parent.csvpath.logger.debug("Found Any so we're done")
                found = True
                continue
            _ = ExpressionUtility.is_one_of(a, arg.actuals)
            self._parent.csvpath.logger.debug(
                "'%s' is_one_of %s returns %s", a, str(arg.actuals), _
            )
            if _ is True:
                found = True
                continue
            found = False
            break
        if not found:
            self._parent.csvpath.logger.debug(
                "%s(%s) not allowed in arg %s of argset %s",
                type(a),
                a,
                i,
                self.argset_number,
            )
            mismatches.append(
                f"{type(a)}({a}) not allowed in arg {i + 1} of {len(actuals)}"
            )
        if len(actuals) < self.min_length:
            self._parent.csvpath.logger.debug(
                "Values received %s are too few for argset %s",
                actuals,
                self.argset_number,
            )
            mismatches.append(f"Too few values received: {actuals}")
            found = False
        if found:
            mismatches = []
        return mismatches

    @property
    def argset_number(self) -> int:
        return self._parent.argsets.index(self)


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
        self._args_match = True
        #
        # this is a narrative description of what the function requires.
        # it won't be used in every error for every function because in
        # some cases it won't add much, but in more complex functions it
        # is going to be the best way to communicate to the user. In
        # principle we could somehow assemble the text on the fly from
        # looking at the data structure, but i haven't cracked that in
        # three attempts, so it falls to someone else.
        #
        # see types/datef.py for what this could look like.
        #
        self.explain = None

    @property
    def csvpath(self):
        return self._csvpath

    def reset(self) -> None:
        self._args_match = True
        self.matched = False

    @property
    def args_match(self) -> bool | None:
        """Only used in the runtime actuals matching. speaks
        to if the line should be considered matched or not.
        None is default
        True means matching succeeded
        False means matching failed
        """
        return self._args_match

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

    def _has_none(self, actuals: List[Any]):
        for _ in actuals:
            if ExpressionUtility.is_none(_):
                return True
        return False

    def validate(self, siblings: List[Matchable]) -> None:
        if len(self._argsets) == 0 and len(siblings) == 0:
            self.validated = True
            return
        if (
            len(self._argsets) > 0
            and len(self._argsets[0].args) == 0
            and len(siblings) == 0
        ):
            self.validated = True
            return
        #
        # we want to check all the argsets even if we find a match
        # because we need them all to be shrunk or padded for the actuals
        # matching. we only do this part once, so it's not a big lift.
        #
        good = False
        for aset in self._argsets:
            _m = aset.validate_structure(siblings)
            if _m is None:
                good = True
        if not good:
            msg = None
            if self.matchable:
                msg = f"Csvpath language problem in {self.matchable.my_chain}: {_m}"
            else:
                msg = "CsvPath Language syntax problem"
            self._matchable.matcher.csvpath.error_manager.handle_error(
                source=self._matchable, msg=msg
            )
            if self._matchable.matcher.csvpath.do_i_raise():
                #
                # ChildrenException because we're validating CsvPath syntax
                #
                raise ChildrenException(msg)
        self.validated = True

    def matches(self, actuals: List[Any]) -> None:
        if len(self._argsets) == 0 and len(actuals) == 0:
            self.matched = True
            return
        msg = None
        if self.matchable.notnone and self._has_none(actuals):
            #
            # this test allows any subclass of .types.Type to have a None value as long as it is not
            # in the 0th index. effectively, the notnone qualifier only applies to the first arg for
            # this class of object. this allows us to have, for e.g., an integer(#age, none(), 0)
            #
            if (
                hasattr(self.matchable, "my_type")
                and len(actuals) >= 1
                and not ExpressionUtility.is_none(actuals[0])
            ):
                self.matchable.matcher.csvpath.logger.debug(
                    f"{self.matchable.my_type} at {self.matchable.my_chain} is notnone but has a non-0-index None. Allowing it since it is a type."
                )
            else:
                msg = f"Cannot have None in {self.matchable.my_chain} because it has the notnone qualifier"
        else:
            #
            # if we have an equality testing equals as the matchable's child, we have the wrong
            # actuals. in that case the actuals is [bool] because Equality with == is always
            # true or false. we can pass [True] and get the right answer even if the ultimate
            # actual is False.
            #
            if (
                len(self.matchable.children) == 1
                and isinstance(self.matchable.children[0], Equality)
                and self.matchable.children[0].op == "=="
            ):
                actuals = [True]
            msg = ArgumentValidationHelper().validate(
                self, actuals, self.matchable.name
            )
        if msg is not None:
            self._matchable.matcher.csvpath.error_manager.handle_error(
                source=self._matchable, msg=msg
            )
            if self._matchable.matcher.csvpath.do_i_raise():
                #
                # MatchException because we're validating data during matching
                #
                raise MatchException(msg)
        #
        # self.matched = True means that we have run arg validation matching
        # on this match component. it does not mean that the match component
        # had no errors or "matched" either the line or the args.
        #
        self.matched = True
