from ...reference_3 import Reference3
from ..function_3 import Function3


class TransferOnCompleteAll3(Function3):
    #
    # transfers_3.py's own "transfers" object is keyed by csvpath
    # statement identity (confirmed against paths_descriptor.py's
    # GroupTransfers.path_transfers: dict[str, Transfers]), each value
    # a fixed four-state Transfers object (on_complete_all/valid/
    # invalid/error, each a list of {file, transfer_to} pairs). The
    # arg here is that identity, not an arbitrary connection name the
    # way sources/destinations are -- same "{}"-placeholder KEY
    # mechanism either way (see source_address_3.py).
    #
    NAME = "transfer_on_complete_all"
    SUMMARY = (
        "The file/transfer_to pairs configured to transfer regardless "
        "of outcome, for the named csvpath statement identity within "
        "the resolved named-paths group -- read from definition.json's "
        "transfers.path_transfers.<identity>.on_complete_all. Requires "
        "a csvpath statement identity argument."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    SOURCE = "definition"
    KEY = {
        Reference3.CSVPATHS: "transfers.path_transfers.{}.on_complete_all",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
