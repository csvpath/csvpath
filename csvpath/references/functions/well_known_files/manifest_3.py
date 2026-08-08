from ...reference_3 import Reference3
from ..function_3 import Function3


class Manifest3(Function3):
    #
    # the first real metadata-file function -- resolves to the manifest
    # data of the enclosing named-file/named-paths group, or of whatever
    # more specific scope has already been identified alongside it (see
    # "creating references v3.txt"'s "Resolve terminating at name_one,
    # with file pointer" row).
    #
    # ROLE is VALUE, not POINTER -- corrected after realizing the
    # original POINTER assignment was wrong: :manifest() never narrows
    # or selects anything itself, in any of its usages. Even bare
    # ("$acme.files.:manifest()") it isn't resolving scope down from
    # multiple candidates -- root_major already fully identifies the one
    # named-file: :manifest() just accesses its manifest. This only
    # became visible as a problem once :manifest() needed to sit
    # *beside* a real version-selecting pointer in the same chain (e.g.
    # "$acme.files.a.:last():manifest()") -- as POINTER it would have
    # been double-counted by ReferenceFunctionFactory.build_chain()'s
    # "at most one pointer per chain" rule, even though nothing is
    # actually being narrowed twice. VALUE is excluded from that count,
    # same as a computed value like a future :year() would be.
    #
    # Wired in for two name_one-terminal shapes: bare/sole-content
    # (e.g. "$acme.files.:manifest()" -- the whole raw manifest.json) and
    # combined with real path/version narrowing in name_three, where it
    # resolves to the matched entry/entries instead (see
    # FilesReferenceFinder3/CsvpathsReferenceFinder3's own handling).
    #
    NAME = "manifest"
    SUMMARY = (
        "Points at the manifest data for the enclosing named-file or "
        "named-paths group -- the whole file when nothing else narrows "
        "scope, or the matched entry/entries when combined with real "
        "path/version narrowing."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
