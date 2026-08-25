from ...reference_3 import Reference3
from ..function_3 import Function3


class ReferenceField3(Function3):
    #
    # Named-File Manifest (table 1)'s own "reference" key -- named
    # ReferenceField3 (not Reference3) to avoid colliding with the
    # unrelated top-level Reference3 class (the parsed reference object
    # graph, csvpath/references/reference_3.py) -- NAME is still the
    # plain "reference" the manifest key itself uses.
    #
    NAME = "reference"
    SUMMARY = (
        "A complete, fingerprint-based reference to this version's own "
        "bytes -- as exact as the version's uuid for retrieving the "
        "registered content, though not always the same registration "
        "event that produced the fingerprint if identical bytes were "
        "registered more than once under different paths."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "reference",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_THREE,)}
