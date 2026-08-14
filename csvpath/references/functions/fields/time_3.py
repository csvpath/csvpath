from ...reference_3 import Reference3
from ..function_3 import Function3


class Time3(Function3):
    #
    # see uuid_3.py for the shared field-accessor design this follows.
    # "time" is the cleanest case in the manifest catalog -- the literal
    # key is identical across every manifest that has it, no per-
    # datatype renaming needed. RESULTS scopes widened in now that the
    # run-vs-instance dispatch (Reference3.RESULT) exists.
    #
    NAME = "time"
    SUMMARY = (
        "The moment the resolved entity's manifest entry was created -- "
        "registration/load time for named-file/named-paths versions, "
        "start time for a results run or instance."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "time",
        Reference3.CSVPATHS: "time",
        Reference3.RESULTS: "time",
        Reference3.RESULT: "time",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
