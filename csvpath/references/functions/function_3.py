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

    #
    # {datatype: (position, ...)} -- which of Reference3.NAME_ONE/
    # NAME_TWO/NAME_THREE this function is legal to appear in, per
    # datatype it applies to. Added 2026-08-14, rolled out incrementally
    # per Finder (CSVPATHS first -- see ReferenceFinder3._check_position()
    # and CsvpathsReferenceFinder3's own call sites) rather than all at
    # once. Unlike DATATYPES (descriptive only -- confirmed nothing reads
    # it except Function3.describe(), a future type-ahead layer's own
    # registry query, not a runtime gate), POSITIONS is the ENFORCED
    # source of truth once a Finder calls _check_position() with it:
    # replaces the scattered, inconsistent "is this recognized" guards
    # each Finder used to hand-write on its own. A datatype key absent
    # from this dict, or present but empty, both mean "not legal here"
    # -- the difference is only documentation intent (declared-and-
    # rejected vs. not yet declared for that datatype/Finder). Never
    # declared for argument-only VALUE wrappers (e.g. :date(), :idchain())
    # -- those are never a top-level chain member to check a position
    # for; they only ever appear nested inside another function's own
    # arg.
    #
    POSITIONS: dict = {}

    #
    # field-accessor functions only (e.g. :uuid(), :time(), :on_arrival())
    # -- both left unset (None/{}) for every other function. SOURCE names
    # which well-known, per-entity resource this field lives in ("manifest"
    # or "definition"); KEY is a dict of datatype -> dotted key path within
    # that resource's dict for this specific field (e.g. {Reference3.FILES:
    # "on_arrival.named_paths_group"}). A finder uses these to resolve and
    # extract the field generically, without per-function special-casing --
    # see ReferenceFinder3._extract_field_value(). A third SOURCE value,
    # "computed", marks a field that is never stored at all -- its value
    # comes straight from the already-resolved reference/finder state
    # (e.g. named_file_home). KEY is left empty ({}) for these; the owning
    # finder computes the value itself, by function NAME, instead of doing
    # a manifest/definition lookup. See named_file_home_3.py and
    # FilesReferenceFinder3._extract_data().
    #
    SOURCE: str = None
    KEY: dict = {}

    #
    # optional fallback for SOURCE == "manifest" field accessors only --
    # {datatype: dotted key path} within that same entity's own global-
    # ledger entry, consulted only when KEY's own lookup in the entity's
    # own manifest/definition comes back None. Added 2026-08-25: some
    # fields exist only in the global ledger, never in the entity's own
    # manifest (e.g. a named-file's own manifest never records a pointer
    # back to itself -- see file_manifest_3.py, and issue #261 for the
    # related core-Framework gap this works around at the reference
    # layer). Per David's own framing: a reference resolves one
    # conceptual entity, not "one manifest entry here, another there" --
    # the caller should not need to know which physical file a field
    # actually lives in. Left empty ({}) for every function that does
    # not need it -- the common case, where a field is never absent
    # from its own entity's manifest. See ReferenceFinder3's own shared
    # fallback helper for how this is actually consulted.
    #
    LEDGER_KEY: dict = {}

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
