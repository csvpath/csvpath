from ...reference_3 import Reference3
from ..function_3 import Function3


class Home3(Function3):
    #
    # narrowed 2026-08-26 (see the "split :home()'s field-read job"
    # bucket-list entry) -- :home() used to do two jobs under one name:
    # reading whichever of four real manifest keys (file_home,
    # named_paths_home, run_home, instance_home) a pointer already
    # selected, AND acting as the zero-level ("no template") placeholder
    # when used bare, alone, as name_one's entire content -- the only
    # legal way to say "nothing narrows here" at a bare position (a
    # truly empty name_one is not legal grammar). The field-read job is
    # now :file_home()/:group_home()/:run_home()/:instance_home() (one
    # function per real key, see each one's own docstring) -- :home()
    # itself keeps ONLY the placeholder role, so it no longer declares
    # SOURCE/KEY at all (nothing reads a manifest field off it anymore).
    # CSVPATHS dropped entirely -- it has no path dimension, so no
    # zero-level concept to place-hold for; :group_home() is its own
    # entire share of the old job, with nothing left behind here.
    #
    NAME = "home"
    SUMMARY = (
        "The zero-level (no-template) placeholder, when used alone as "
        "name_one's entire content -- 'nothing narrows further, this "
        "entity's own home directory already is the whole result.' "
        "FILES and RESULTS only; CSVPATHS has no path dimension to be "
        "zero-level of."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
