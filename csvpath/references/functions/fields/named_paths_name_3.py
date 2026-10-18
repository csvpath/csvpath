from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedPathsName3(Function3):
    #
    # CSVPATHS self-reference (this group's own registered name, read
    # off its own manifest) plus RESULTS run scope (which named-paths
    # group the run belongs to). Not instance scope -- the Result
    # Instance Manifest does not carry this field, confirmed against
    # result_registrar.py's metadata_update().
    #
    # ARG_TYPES widened 2026-10-18 (was: `()`, bare-only) --
    # normative_reference_examples.txt's own worked example ("$*.
    # results.:manifest():named_paths_name(\"orders\"):yesterday()")
    # needs a string argument to GATE a pooled RESULTS candidate list
    # by this field -- same generic field_call/_matches_field_
    # predicate mechanism :error_count()/:named_file_name()/:uuid()
    # already use, no RESULTS-side code needed. Part of compendium
    # 6.7's "name" functional group (:named_paths_name()/:named_
    # results_name()/:named_file_name()) -- the same retrieve/select
    # duality rule as the "uuid" group already built. CSVPATHS has no
    # equivalent GATE mechanism at all (confirmed live before this
    # widening: an argument there was silently ignored, returning the
    # group's own real name regardless) -- CsvpathsReferenceFinder3._
    # resolve_versions() now explicitly rejects an argument here
    # instead, since filtering a group's own versions by its OWN name
    # (always identical to root_major) would be redundant anyway.
    #
    NAME = "named_paths_name"
    SUMMARY = (
        "The name of the resolved named-paths group -- its own name for "
        "CSVPATHS, or the run's named-paths group for RESULTS run "
        "scope. An optional string argument GATES a pooled RESULTS "
        "candidate list by this field (not supported for CSVPATHS -- "
        "redundant there, since a literal root already names the group "
        "directly)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "name"
    KEY = {
        Reference3.CSVPATHS: "named_paths_name",
        Reference3.RESULTS: "named_paths_name",
    }
    POSITIONS = {
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        # RESULTS: KEY only has a RESULTS entry, no RESULT (instance)
        # entry -- run scope only.
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
