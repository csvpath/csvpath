from ...reference_3 import Reference3
from ..function_3 import Function3


class All3(Function3):
    #
    # :all() is NOT equivalent to "*" (see reference_grammar_3.py's
    # module docstring and "creating references v3.txt"'s NOTES): "*"
    # flattens a wildcard position into a pooled search space that a
    # pointer then reduces to one answer; ":all()" switches into
    # grouped/unreduced mode instead. For csvpaths specifically (no
    # path dimension to group by), that collapses to a simpler case:
    # ":all()" just means "do not reduce -- return every version," the
    # same outcome as writing no pointer at all. Its role is
    # CONTEXT_SETTER (it narrows the current scope without resolving to
    # a specific item) even though the narrowing is a no-op here -- it
    # exists so a reference can explicitly ask for "everything" using a
    # real function, since the grammar requires name_one to contain one
    # for csvpaths (literal/"*" path-building is not meaningful there).
    #
    NAME = "all"
    SUMMARY = (
        "Explicitly asks for every match, unreduced -- the complete-"
        "instruction counterpart to a bare '*', which is a dangling "
        "fragment on its own."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
    }
