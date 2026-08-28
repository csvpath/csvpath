from ...reference_3 import Reference3
from ..function_3 import Function3


class Meta3(Function3):
    #
    # resolves to the parsed JSON contents of meta.json -- the run
    # instance's own metadata (paths_name, file_name, run_time,
    # run_index, identity, the csvpath statement's own metadata comment,
    # and its runtime_data -- ResultSerializer._save, always written).
    # See Errors3 for the shared name_three shape this rides alongside.
    #
    NAME = "meta"
    SUMMARY = (
        "The parsed contents of a run instance's meta.json -- run/"
        "identity metadata plus the csvpath statement's own metadata "
        "and runtime data."
    )
    ROLE = Function3.VALUE
    # metadata_kind() override -- a whole-resource read, not a
    # single field, see Function3.RESOLVES_AS's own docstring for
    # why this class needs one (added 2026-08-28).
    RESOLVES_AS = Reference3.METADATA_FILE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
