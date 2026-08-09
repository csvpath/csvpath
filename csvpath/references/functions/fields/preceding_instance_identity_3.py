from ...reference_3 import Reference3
from ..function_3 import Function3


class PrecedingInstanceIdentity3(Function3):
    #
    # only written into the manifest when source_mode_preceding is true
    # (see result_registrar.py's metadata_update) -- absent otherwise,
    # which _extract_field_value's tolerant missing-key handling already
    # treats as None, not an error.
    #
    NAME = "preceding_instance_identity"
    SUMMARY = (
        "The identity of the preceding instance whose data.csv this "
        "instance actually read, when source_mode_preceding is true -- "
        "None otherwise. Carries issue #223: this value can be wrong "
        "when statements are skipped/reordered, see that issue for "
        "detail."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "preceding_instance_identity",
    }
