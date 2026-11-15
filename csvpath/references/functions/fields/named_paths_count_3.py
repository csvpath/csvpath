from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.predicate_function_3 import PredicateFunction3


class NamedPathsCount3(Function3):
    #
    # see uuid_3.py for the shared field-accessor design this follows.
    # single-context (CSVPATHS only), per
    # manifest_field_functions_proposal.md's Part B.
    #
    NAME = "named_paths_count"
    SUMMARY = (
        "The number of csvpath statements in the resolved named-paths "
        "group version."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    ARG_TYPES = (int, PredicateFunction3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "named_paths_count",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
