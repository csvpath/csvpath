from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


class FilePath3(Function3):
    #
    # Named-File Manifest (table 1)'s own "file" key -- the version
    # file's own path. Named FilePath3/:file_path() rather than :file(),
    # since :file() is already registered for a different, incompatible
    # purpose (File3 -- an arbitrary user-named RESULTS output file,
    # required string arg, no manifest read at all). Table 2's own
    # "file_path" key (the global arrivals ledger's spelling of the same
    # concept) is the LEDGER_KEY, so a '*' read (':manifest():
    # file_path()'), which reads the ledger, finds it. a per-name
    # manifest entry always has "file", so the fallback is never used
    # there.
    #
    NAME = "file_path"
    SUMMARY = "The path to the resolved named-file version's own stored bytes."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    # and :has_value()/:does_not_have_value(): "Every field matches exactly
    # one of the two" (NRE); other predicates on a string are not ruled
    ARG_TYPES = (str, HasValue3, DoesNotHaveValue3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "file",
    }
    LEDGER_KEY = {
        Reference3.FILES: "file_path",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_THREE,)}
