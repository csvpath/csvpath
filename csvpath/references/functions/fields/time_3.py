from ...reference_3 import Reference3
from ..function_3 import Function3


class Time3(Function3):
    #
    # see uuid_3.py for the shared field-accessor design this follows.
    # "time" is the cleanest case in the manifest catalog -- the literal
    # key is identical across every manifest that has it, no per-
    # datatype renaming needed.
    #
    NAME = "time"
    SUMMARY = (
        "The moment the resolved named-file/named-paths version was "
        "registered/loaded, read straight off its manifest entry."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "time",
        Reference3.CSVPATHS: "time",
    }
