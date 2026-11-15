from ...reference_3 import Reference3
from ..function_3 import Function3


class GroupHome3(Function3):
    #
    # split out of :home() (2026-08-26, see :home()'s own docstring and
    # the "split :home()'s field-read job" bucket-list entry) -- reads
    # the "named_paths_home" key off whatever named-paths group version
    # a pointer already selected. CSVPATHS has no zero-level/path-depth
    # concept at all (no path dimension to place-hold for), so unlike
    # FILES/RESULTS this is CSVPATHS' entire share of :home()'s old job
    # -- there is no placeholder role left behind for :home() itself to
    # keep doing here.
    #
    NAME = "group_home"
    SUMMARY = "The path to the resolved named-paths group version's own home directory."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "named_paths_home",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
