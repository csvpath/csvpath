from ...reference_3 import Reference3
from ..function_3 import Function3


class Definition3(Function3):
    #
    # the second metadata-file function, mirroring Manifest3 exactly --
    # points at the enclosing named-file/named-paths group's own
    # definition.json (its stored configuration: sources, on_arrival
    # behavior, scripts, webhooks, etc -- see NamedFileDescriber/
    # NamedPathsDescriber, both JSON_FILE = "definition.json", stored at
    # the same home directory as manifest.json). Unlike manifest.json,
    # definition.json is genuinely optional -- a named-file/group that
    # was never explicitly configured has no definition.json on disk at
    # all, and it is not currently versioned (always the single current
    # definition, regardless of which version of the file/group you are
    # looking at -- versioning description files is a real future need,
    # just not yet prioritized). Named-results has no definition.json
    # equivalent, so this is FILES/CSVPATHS only, unlike Manifest3.
    #
    # ROLE is VALUE, not POINTER, for the same reason Manifest3's own
    # ROLE was corrected: :definition() never narrows or selects
    # anything, even bare -- it only ever accesses what root_major
    # already fully identifies. This one was missed in that earlier fix
    # (only Manifest3 got corrected) -- caught while re-checking every
    # existing "accessor" function's role for consistency ahead of
    # adding the well-known-file functions below, which share the
    # exact same trait.
    #
    NAME = "definition"
    SUMMARY = (
        "Points at the whole definition.json for the enclosing named-file "
        "or named-paths group -- its stored configuration (sources, "
        "on_arrival behavior, scripts, webhooks, etc). Not currently "
        "versioned; resolves to None if the group/file was never "
        "explicitly configured (no definition.json written yet)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
