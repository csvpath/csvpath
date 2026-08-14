from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedFileHome3(Function3):
    #
    # the named-file's own root directory (the container shared by every
    # version ever registered under this name), distinct from :home()'s
    # FILES meaning (file_home -- where this one specific version's bytes
    # live). FileRegistrar never stores this in the Named-File Manifest
    # (table 1) -- it would just duplicate what FilesReferenceFinder3
    # already computes to even find that manifest in the first place
    # (file_manager.named_file_home(name)) -- so it is computed directly
    # rather than read. Settled 2026-08-09, see
    # manifest_field_functions_proposal.md.
    #
    NAME = "named_file_home"
    SUMMARY = "The named-file's own root directory, shared by every version registered under this name."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "computed"
    KEY = {}
    POSITIONS = {Reference3.FILES: (Reference3.NAME_THREE,)}
