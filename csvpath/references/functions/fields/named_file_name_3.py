from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedFileName3(Function3):
    #
    # at RESULTS/RESULT scope this reads a genuinely stored field --
    # which named-file a run/instance consumed, operational data that
    # cannot be derived any other way. At FILES scope it means something
    # different: the resolved entity's own name, which is already known
    # the moment a reference is parsed (reference.root_major) -- storing
    # it a second time in the Named-File Manifest would just be a
    # duplicate of something the finder already has in hand, so
    # FilesReferenceFinder3 computes it directly rather than reading it
    # from any manifest. Settled 2026-08-09, see
    # manifest_field_functions_proposal.md.
    #
    NAME = "named_file_name"
    SUMMARY = (
        "RESULTS/RESULT: the name of the named-file a run/instance "
        "consumed as its input. FILES: the resolved named-file's own "
        "name."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS, Reference3.FILES)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "name"
    KEY = {
        Reference3.RESULTS: "named_file_name",
        Reference3.RESULT: "named_file_name",
    }
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }
