from ..reference_3 import Reference3
from .function_3 import Function3


class Manifest3(Function3):
    #
    # the first real metadata-file function -- resolves to the raw
    # contents of the enclosing named-file/named-paths group's own
    # manifest.json, the append-only record of every version ever
    # registered/loaded under that name (see "creating references
    # v3.txt"'s "Resolve terminating at name_one, with file pointer"
    # row). ROLE is POINTER, matching the established taxonomy for
    # well-known-file functions ("In name_three, a pointer resolves to
    # a well-known metadata file (e.g. :errors())") -- it resolves the
    # current scope down to exactly one concrete resource, it just
    # doesn't do it by list-position the way :first()/:last()/:index()
    # do. Only wired in today as a name_one-terminal, bare/sole-content
    # reference (e.g. "$acme.files.:manifest()") -- see
    # FilesReferenceFinder3/CsvpathsReferenceFinder3's own
    # _is_bare_pointer_reference-gated query() branch. Not yet wired in
    # for name_three (files' name_three is reserved for version
    # selection; csvpaths' name_three doesn't support a function chain
    # at all yet).
    #
    NAME = "manifest"
    SUMMARY = (
        "Points at the whole manifest.json for the enclosing named-file "
        "or named-paths group -- the append-only record of every version "
        "ever registered/loaded under that name."
    )
    ROLE = Function3.POINTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
