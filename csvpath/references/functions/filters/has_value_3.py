from ...reference_3 import Reference3
from ..function_3 import Function3
from .predicate_function_3 import PredicateFunction3


class HasValue3(PredicateFunction3):
    #
    # see true_3.py for the shared predicate-function design this follows.
    # compendium 6.36 (David, 2026-11-03): a field has a value when it
    # holds a primitive, including 0 and false, or a list or dict that is
    # not empty. "", [], {}, null and a field that is not present do not.
    # :has_value()/:does_not_have_value() replace :none()/:not_none()/
    # :empty()/:not_empty(), whose overlapping tests meant, e.g., that
    # :not_empty() matched a missing field. A field read gives None for a
    # missing key, so null and not-present are the same here on purpose.
    #
    NAME = "has_value"
    SUMMARY = (
        "Matches a primitive (including 0 and false) or a non-empty list or "
        "dict -- a predicate argument, not usable on its own."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False

    _SIZED = (str, bytes, list, tuple, dict, set)

    @staticmethod
    def has_value(value) -> bool:
        """the one rule both :has_value() and :does_not_have_value() use."""
        if value is None:
            return False
        if isinstance(value, HasValue3._SIZED):
            return len(value) > 0
        return True

    def matches(self, value) -> bool:
        return HasValue3.has_value(value)
