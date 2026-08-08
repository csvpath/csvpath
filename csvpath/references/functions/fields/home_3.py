from ...reference_3 import Reference3
from ..function_3 import Function3


class Home3(Function3):
    #
    # see uuid_3.py for the shared field-accessor design this follows.
    # the raw manifests already use a consistent "_home" suffix for this
    # concept across every datatype (file_home, named_paths_home,
    # run_home, instance_home) -- strong natural fit for one shared name,
    # per manifest_field_functions_proposal.md's Part A. RESULTS scopes
    # (run_home/instance_home) are deferred with the rest of RESULTS.
    #
    NAME = "home"
    SUMMARY = (
        "The path to the resolved entity's own root/working directory -- "
        "file_home for a named-file version, named_paths_home for a "
        "named-paths group."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "file_home",
        Reference3.CSVPATHS: "named_paths_home",
    }
