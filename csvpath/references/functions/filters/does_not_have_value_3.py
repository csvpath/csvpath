from ...reference_3 import Reference3
from ..function_3 import Function3
from .has_value_3 import HasValue3
from .predicate_function_3 import PredicateFunction3


class DoesNotHaveValue3(PredicateFunction3):
    # the exact opposite of :has_value(), see has_value_3.py: matches "",
    # [], {}, null and a field that is not present. Every field matches
    # exactly one of the two.
    NAME = "does_not_have_value"
    SUMMARY = (
        'Matches "", [], {}, null or a missing field -- a predicate argument, '
        "not usable on its own."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False

    def matches(self, value) -> bool:
        return not HasValue3.has_value(value)
