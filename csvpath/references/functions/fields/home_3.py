from ...reference_3 import Reference3
from ..function_3 import Function3


class Home3(Function3):
    #
    # see uuid_3.py for the shared field-accessor design this follows.
    # the raw manifests already use a consistent "_home" suffix for this
    # concept across every datatype (file_home, named_paths_home,
    # run_home, instance_home) -- strong natural fit for one shared name,
    # per manifest_field_functions_proposal.md's Part A. RESULTS scopes
    # widened in now that the run-vs-instance dispatch (Reference3.RESULT)
    # exists.
    #
    NAME = "home"
    SUMMARY = (
        "The path to the resolved entity's own root/working directory -- "
        "file_home for a named-file version, named_paths_home for a "
        "named-paths group, run_home for a results run, instance_home "
        "for a results instance."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "file_home",
        Reference3.CSVPATHS: "named_paths_home",
        Reference3.RESULTS: "run_home",
        Reference3.RESULT: "instance_home",
    }
    #
    # CSVPATHS has no "bare :home() as zero-level selector" case (that
    # is FILES/RESULTS-only -- CSVPATHS' name_one has no path dimension
    # to be zero-level of) -- always the ordinary field-accessor position.
    # FILES has BOTH: the bare, name_one, zero-level-selector shape
    # (":home().:last()") and the ordinary field-accessor position
    # (name_three, beside a matched pointer, e.g.
    # ":name('orders.csv').:last():home()").
    #
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
    }
