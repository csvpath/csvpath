from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.predicate_function_3 import PredicateFunction3


class FilesComplete3(Function3):
    #
    # aggregate/individual pair, same shape as valid_3.py/completed_3.py.
    # name deliberately avoids reusing either source key
    # (all_expected_files/files_expected), since both are slightly
    # misleading in isolation per manifest_field_functions_proposal.md's
    # Part A.
    #
    NAME = "files_complete"
    SUMMARY = (
        "Run scope: true if every csvpath statement in the run has all "
        "of its expected files present. Instance scope: true if this "
        "one statement has all of its expected files present."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    ARG_TYPES = (PredicateFunction3,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "all_expected_files",
        Reference3.RESULT: "files_expected",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
