from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.predicate_function_3 import PredicateFunction3


class NamedFileSize3(Function3):
    #
    # Results Run Manifest (table 5)'s own "named_file_size" -- the byte
    # size of the named-file version used, read from the filesystem at
    # the moment the run started. Not actually optional per the manifest
    # doc (results_registrar.py sets it unconditionally, falling back to
    # 0 if the file cannot be found) -- resolved the same as any other
    # field regardless.
    #
    NAME = "named_file_size"
    SUMMARY = "The byte size of the named-file version used as input to the resolved run."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    ARG_TYPES = (int, PredicateFunction3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "named_file_size",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
