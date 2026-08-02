from typing import Any

from ..reference_3 import InterpolatedString3
from ..reference_exceptions_3 import ReferenceException3


#
# Function3 is the base class for real, behavior-having references-v3
# functions -- distinct from FunctionCall3 (reference_3.py), which is
# just the parsed name+arg shape the transformer builds. A Function3 is
# constructed by ReferenceFunctionFactory.build(), given an already-
# resolved arg (a nested FunctionCall3 gets compiled into a Function3
# first -- see the factory).
#
# per "requirements for functions.txt": functions are looked up and
# validated at runtime (not baked into the grammar), self validating,
# self describing/inspectable, take at most 1 arg, and self-report
# their role -- CONTEXT_SETTER (narrows/sets scope without resolving to
# an item, e.g. :before()/:after()), POINTER (resolves scope to exactly
# 0 or 1 item, e.g. :last(), :first(), :index(n)), or VALUE (computes a
# value -- usually clock/calendar-derived, e.g. :year() -- that behaves
# like a computed literal wherever it is used; it does not operate on
# scope at all, unlike the other two roles). There is deliberately no
# code shared with csvpath.matching.functions -- this class does not
# subclass or import anything from there.
#
class Function3:
    CONTEXT_SETTER = "context_setter"
    POINTER = "pointer"
    VALUE = "value"

    #
    # subclasses override all of these.
    #
    NAME: str = None
    SUMMARY: str = None
    ROLE: str = None
    DATATYPES: tuple = ()
    ARG_TYPES: tuple = ()
    ARG_REQUIRED: bool = False

    def __init__(self, *, arg: Any = None) -> None:
        self._arg = arg

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def arg(self) -> Any:
        return self._arg

    def check_valid(self) -> None:
        """structural check; doesn't test or use the arg's value. mirrors
        csvpath.matching.productions.matchable.Matchable.check_valid()'s
        parse-time-not-runtime-values pattern, scaled down for a single,
        declaratively-typed arg instead of Args/ArgSet's multi-arg
        overload sets."""
        if self.ARG_REQUIRED and self._arg is None:
            raise ReferenceException3(f":{self.NAME}() requires an argument")
        if not self.ARG_TYPES and self._arg is not None:
            raise ReferenceException3(f":{self.NAME}() does not take an argument")
        if self.ARG_TYPES and self._arg is not None:
            # any function that accepts a plain str also accepts an
            # interpolated one -- callers should never need to remember
            # to list InterpolatedString3 separately just to support
            # "{...}" interpolation in a string arg.
            allowed = self.ARG_TYPES
            if str in allowed and InterpolatedString3 not in allowed:
                allowed = (*allowed, InterpolatedString3)
            if not isinstance(self._arg, allowed):
                raise ReferenceException3(
                    f":{self.NAME}() argument must be one of {self.ARG_TYPES}, "
                    f"got {type(self._arg)}"
                )
        if isinstance(self._arg, (Function3, InterpolatedString3)):
            self._arg.check_valid()

    def describe(self) -> dict:
        """machine-actionable self-description -- also human-readable
        via SUMMARY. this is what a future type-ahead layer's registry
        query is meant to read (see references_notes/
        autocomplete_prototype.py's registry shape: name/summary/
        datatypes)."""
        return {
            "name": self.NAME,
            "summary": self.SUMMARY,
            "role": self.ROLE,
            "datatypes": self.DATATYPES,
        }

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Function3)
            and other.name == self.name
            and other.arg == self._arg
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(arg={self._arg!r})"
