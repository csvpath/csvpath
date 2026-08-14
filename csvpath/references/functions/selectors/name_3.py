from ...reference_3 import Reference3
from ..function_3 import Function3


class Name3(Function3):
    #
    # matches an exact literal name at this position -- specifically for
    # names that cannot appear as a bare PATH_SEGMENT (e.g. a real
    # filename with a "." in it, which the grammar reserves as the
    # name_one/name_three separator). str arg only for now -- the
    # grammar also allows "*", "@var", and a regex here, but those need
    # machinery (wildcard-as-arg semantics, runtime variable lookup,
    # regex matching) this first pass does not need yet.
    #
    NAME = "name"
    SUMMARY = (
        "Matches an exact literal name at this position -- for names "
        "(e.g. a filename) that cannot appear in a bare path segment."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    #
    # CSVPATHS deliberately maps to an EMPTY tuple, not an absent key --
    # DATATYPES lists csvpaths (it type-checks fine as an argument-typed
    # function), but name_one has no path-building dimension for
    # csvpaths (STRUCTURE table: name_one is purely a version-selecting
    # function chain there) -- :name() has never had anywhere legal to
    # go. Before 2026-08-14 this was enforced by nothing at all:
    # CsvpathsReferenceFinder3._resolve_versions() had no unrecognized-
    # function guard, so "$acme.csvpaths.:name(\"x\")" silently no-opped
    # instead of raising, contradicting the class's own docstring
    # ("literal/path-building content... are not meaningful for
    # csvpaths and are rejected"). This is the fix -- see
    # ReferenceFinder3._check_position().
    #
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_ONE,),
        Reference3.CSVPATHS: (),
    }
