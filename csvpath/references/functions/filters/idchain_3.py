import re

from ...reference_3 import Reference3, Regex3
from ...reference_exceptions_3 import ReferenceException3
from ..function_3 import Function3
from .predicate_function_3 import PredicateFunction3


class Idchain3(Function3):
    #
    # the first metadata-FIELD function -- addresses one specific error
    # entry (or entries) within errors.json by the match component that
    # produced it, e.g. ":errors(:idchain('add[0]string[2]'))". Despite
    # sounding like it walks a live Matcher parse tree, it does not --
    # Error.to_json()'s own "source" field already holds exactly this
    # chain string (Matchable.my_chain, generated once, at the moment
    # the error was recorded), so this is a plain field-match filter,
    # the same idea as :type() filtering manifest entries by their own
    # "type" field, confirmed directly against the real Error class
    # rather than assumed. Only meaningful nested inside :errors() (see
    # Errors3.ARG_TYPES) -- not usable on its own or in any other slot.
    # ROLE is VALUE, matching every other accessor/field function built
    # so far: it does not narrow/select anything itself, it is a value
    # fed to :errors()'s own filtering logic.
    #
    # This is the FILTER half of the broader "position decides meaning"
    # rule (David, 2026-08-21) -- being NESTED as :errors()'s own
    # argument is what makes this narrow errors.json's own entries
    # rather than gate the whole result. See Errors3's own comment for
    # the GATE half (a separate function CHAINED AFTER :errors(),
    # carrying its own predicate on an unrelated sibling field --
    # NOT YET BUILT, see deferred_work_bucket_list.md).
    #
    # arg may be a plain str (exact match against an entry's "source",
    # the original behavior), a Regex3 (":idchain(/pattern/)") for a
    # minimally-searchable match -- David's own call after weighing
    # search()/match()/fullmatch(): search(), so the pattern does not
    # need to anchor to the whole idchain string, just find something
    # within it (e.g. matching one match-component among several
    # chained together) -- or, added 2026-08-26, a PredicateFunction3
    # (":idchain(:not_none())", compendium 5.31/5.36/4.13) -- "any
    # idchain at all," not an empty-argument special case, per David's
    # 2026-08-21 framing. The grammar already allowed a REGEX arg
    # everywhere a STRING is allowed, including here -- this is the
    # first real consumer of Regex3 as an actual matching value rather
    # than just a parsed/held object, so the compile-and-apply behavior
    # lives here (matches()), not on the finder that calls it.
    #
    NAME = "idchain"
    SUMMARY = (
        "Addresses one specific match component within a well-known "
        "file's own entries (e.g. errors.json) by its idchain string, "
        "either an exact match (a plain string), a search (a /regex/), "
        "or a predicate function (e.g. :not_none()) -- only meaningful "
        "nested inside :errors()."
    )
    ROLE = Function3.VALUE
    # metadata_kind() override -- added 2026-08-28. Idchain3 has no
    # SOURCE of its own (it never reads a manifest/definition key by a
    # dotted path the way an ordinary field accessor does), so nothing
    # would otherwise mark a reference containing it METADATA_FIELD --
    # but per the "position decides meaning" rule above, being NESTED
    # as :errors()'s own argument is exactly what narrows that whole-
    # resource read down to a field-level one. This is the one function
    # in the registry that needed an explicit override for this reason
    # specifically (every other METADATA_FIELD function gets there for
    # free via its own SOURCE) -- see Function3.RESOLVES_AS's own
    # docstring for the full accounting.
    RESOLVES_AS = Reference3.METADATA_FIELD
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (str, Regex3, PredicateFunction3)
    ARG_REQUIRED = True

    def __init__(self, *, arg=None) -> None:
        super().__init__(arg=arg)
        self._compiled = None
        if isinstance(arg, Regex3):
            try:
                self._compiled = re.compile(arg.pattern)
            except re.error as e:
                raise ReferenceException3(f":idchain() regex is invalid: {e}") from e

    def matches(self, value: str) -> bool:
        """true if `value` (an error entry's own "source" idchain
        string) matches this idchain's arg -- a nested predicate
        function's own matches() (e.g. :not_none() -- "any idchain at
        all"), exact equality for a plain string, or a regex search
        (not anchored to the start/whole string) when the arg is a
        Regex3."""
        if isinstance(self._arg, PredicateFunction3):
            return self._arg.matches(value)
        if value is None:
            return False
        if self._compiled is not None:
            return self._compiled.search(value) is not None
        return value == self._arg
