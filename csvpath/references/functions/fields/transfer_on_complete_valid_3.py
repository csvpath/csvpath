from ...reference_3 import Reference3
from ..function_3 import Function3


class TransferOnCompleteValid3(Function3):
    #
    # see transfer_on_complete_all_3.py for the shared arg-keyed design
    # this follows.
    #
    NAME = "transfer_on_complete_valid"
    SUMMARY = (
        "The file/transfer_to pairs configured to transfer only when "
        "the csvpath statement is valid, for the named csvpath "
        "statement identity within the resolved named-paths group -- "
        "read from definition.json's transfers.path_transfers."
        "<identity>.on_complete_valid. Requires a csvpath statement "
        "identity argument."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    SOURCE = "definition"
    KEY = {
        Reference3.CSVPATHS: "transfers.path_transfers.{}.on_complete_valid",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
