from ...reference_3 import Reference3
from ..function_3 import Function3
from .predicate_function_3 import PredicateFunction3


class False3(PredicateFunction3):
    # see true_3.py for the shared predicate-function design this follows.
    NAME = "false"
    SUMMARY = "Matches the JSON false / Python False value -- a predicate argument, not usable on its own."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False

    def matches(self, value) -> bool:
        return value is False
