from ..reference_3 import Reference3
from .function_3 import Function3


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
