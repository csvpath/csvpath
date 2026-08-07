from ...reference_3 import Reference3
from ..function_3 import Function3


class Origin3(Function3):
    #
    # see uuid_3.py for the shared field-accessor design this follows.
    # the function name David originally asked for -- unifying "from"
    # (Named-File Manifest) and "source_path" (Named-Paths Manifest),
    # two different literal keys for the same concept: where the
    # registered content originally came from before being copied in.
    # Deliberately NOT the same concept as the Result Instance
    # Manifest's origin_data_file, which is about which physical file a
    # run actually read, not where the registered content originally
    # came from -- see manifest_field_functions_proposal.md's Part A
    # note on this function.
    #
    NAME = "origin"
    SUMMARY = (
        "The original source path of the resolved entity's content, "
        "before it was copied/loaded into the named-file or named-paths "
        "group -- table 1's 'from' for FILES, table 3's 'source_path' "
        "for CSVPATHS."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "from",
        Reference3.CSVPATHS: "source_path",
    }
