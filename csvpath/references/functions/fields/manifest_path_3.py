from ...reference_3 import Reference3
from ..function_3 import Function3


class ManifestPath3(Function3):
    #
    # not applicable to FILES -- table 1 has no equivalent stored field.
    # RESULTS instance scope IS present in the real manifest (result_
    # registrar.py writes it), despite manifest_field_functions_
    # proposal.md flagging it as an open gap when that doc was written
    # -- confirmed against current code, not the doc, before including
    # it.
    #
    NAME = "manifest_path"
    SUMMARY = (
        "The filesystem path to the resolved entity's own manifest.json, "
        "as recorded inside that same manifest."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "manifest_path",
        Reference3.RESULTS: "manifest_path",
        Reference3.RESULT: "manifest_path",
    }
    POSITIONS = {
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }
