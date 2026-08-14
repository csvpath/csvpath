from ...reference_3 import Reference3
from ..function_3 import Function3


class Index3(Function3):
    NAME = "index"
    SUMMARY = (
        "The item at a 0-based position in the current scope, in "
        "arrival/registration order."
    )
    ROLE = Function3.POINTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (int,)
    ARG_REQUIRED = True
    #
    # position only applies when used as a top-level pointer -- when
    # nested inside :from()/:to()'s own arg (e.g. ":from(:index(2))"),
    # it is unwrapped via .arg and never reaches a position check at all.
    #
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
