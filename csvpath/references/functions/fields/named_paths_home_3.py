from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedPathsHome3(Function3):
    #
    # CSVPATHS' counterpart to NamedFileHome3 -- the named-paths group's
    # own root directory (the container shared by every version ever
    # loaded under this name), distinct from :group_home()'s meaning
    # (also a root directory, but read as a field of an already-matched
    # version's manifest entry rather than computed from root_major
    # alone). PathsRegistrar never stores this as a manifest field (see
    # Table 4, Named-Paths Loads Manifest) -- it would just duplicate
    # what CsvpathsReferenceFinder3 already computes to even find that
    # manifest in the first place (paths_manager.named_paths_home(name)),
    # so it is computed directly rather than read, same reasoning as
    # NamedFileHome3. Added 2026-09-22, closing the deferred-work bucket
    # list gap of the same name.
    #
    # Only legal with a literal root_major -- '*'/:regex() traversal is
    # not supported (CsvpathsReferenceFinder3._compute_field() raises
    # clearly rather than guessing what "the home directory" would mean
    # across several groups at once).
    #
    NAME = "named_paths_home"
    SUMMARY = "The named-paths group's own root directory, shared by every version loaded under this name."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "computed"
    KEY = {}
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
