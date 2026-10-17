import re

from ...reference_3 import Reference3, Regex3
from ...reference_exceptions_3 import ReferenceException3
from ..function_3 import Function3
from .predicate_function_3 import PredicateFunction3


class Message3(Function3):
    #
    # the direct sibling of Idchain3 -- normative_reference_examples.txt
    # places them right next to each other ("find errors... at a
    # specific idchain" / "what errors... matched a customer"):
    #   :errors(:idchain("customer[0]id[0]"))
    #   :errors(:message(/customer: 319/))
    # Error.to_json() writes a real "message" field (confirmed directly
    # against error.py, not assumed) -- this is a plain field-match
    # filter over errors.json's own entries, same mechanism as Idchain3,
    # just keyed on "message" instead of "source". Built 2026-10-17.
    #
    # Same "position decides meaning" rule as Idchain3 (David,
    # 2026-08-21) -- nested as :errors()'s own argument, this FILTERS
    # which entries of errors.json's own content come back; a function
    # CHAINED AFTER :errors() instead would GATE the whole result (not
    # yet built, see deferred_work_bucket_list.md).
    #
    NAME = "message"
    SUMMARY = (
        "Addresses errors.json entries by their own \"message\" field, "
        "either an exact match (a plain string), a search (a /regex/), "
        "or a predicate function (e.g. :not_none()) -- only meaningful "
        "nested inside :errors()."
    )
    ROLE = Function3.VALUE
    # metadata_kind() override -- same reasoning as Idchain3's own:
    # no SOURCE of its own, so nothing would otherwise mark a reference
    # containing it METADATA_FIELD; being NESTED as :errors()'s own
    # argument is what narrows that whole-resource read to a field-level
    # one (see Function3.RESOLVES_AS's own docstring).
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
                raise ReferenceException3(f":message() regex is invalid: {e}") from e

    def matches(self, value: str) -> bool:
        """true if `value` (an error entry's own "message" string)
        matches this function's arg -- a nested predicate function's
        own matches() (e.g. :not_none() -- "any message at all"), exact
        equality for a plain string, or a regex search (not anchored to
        the start/whole string) when the arg is a Regex3. Identical
        logic to Idchain3.matches() -- kept as its own copy rather than
        a shared helper, since the two fields (source/message) are
        looked up by the caller, not by this class, and there is no
        other state to share."""
        if isinstance(self._arg, PredicateFunction3):
            return self._arg.matches(value)
        if value is None:
            return False
        if self._compiled is not None:
            return self._compiled.search(value) is not None
        return value == self._arg
