from ...reference_3 import Reference3
from ..function_3 import Function3
from .predicate_function_3 import PredicateFunction3


class NotNone3(PredicateFunction3):
    # see true_3.py for the shared predicate-function design this
    # follows. First real consumer wired up 2026-08-26: nested inside
    # :idchain() (e.g. ":errors(:idchain(:not_none()))"), filters
    # errors.json's own entries down to those that have any idchain
    # recorded at all -- see Idchain3.matches(), and compendium
    # 5.36/4.13's own worked example.
    NAME = "not_none"
    SUMMARY = "Matches any value that is not JSON null / Python None -- a predicate argument, not usable on its own."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False

    def matches(self, value) -> bool:
        return value is not None
