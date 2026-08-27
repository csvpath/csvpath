import re

from ...reference_3 import Reference3, Regex3
from ...reference_exceptions_3 import ReferenceException3
from ..function_3 import Function3


class Name3(Function3):
    #
    # matches an exact literal name at this position -- specifically for
    # names that cannot appear as a bare PATH_SEGMENT (e.g. a real
    # filename with a "." in it, which the grammar reserves as the
    # name_one/name_three separator). Also matches a /regex/ (added
    # 2026-08-27, see the "name_one path segment cannot be a regex"
    # bucket-list entry) -- the grammar already allowed a REGEX arg
    # everywhere a STRING is allowed, this just wires it up here too.
    # Comparison itself lives in ReferenceFinder3._segment_matches(),
    # shared by every finder's own path-matching primitive, reusing
    # :idchain()'s own already-settled Regex3 semantics (search(), not
    # anchored -- see idchain_3.py's own docstring for why) rather than
    # inventing a second convention. "@var" here is a separate, still-
    # open gap (runtime variable lookup as some OTHER function's own
    # direct argument) -- not addressed by this.
    #
    NAME = "name"
    SUMMARY = (
        "Matches an exact literal name, or searches a /regex/, at this "
        "position -- for names (e.g. a filename) that cannot appear in "
        "a bare path segment."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (str, Regex3)
    ARG_REQUIRED = True
    #
    # CSVPATHS deliberately maps to an EMPTY tuple, not an absent key --
    # DATATYPES lists csvpaths (it type-checks fine as an argument-typed
    # function), but name_one has no path-building dimension for
    # csvpaths (STRUCTURE table: name_one is purely a version-selecting
    # function chain there) -- :name() has never had anywhere legal to
    # go. Before 2026-08-14 this was enforced by nothing at all:
    # CsvpathsReferenceFinder3._resolve_versions() had no unrecognized-
    # function guard, so "$acme.csvpaths.:name(\"x\")" silently no-opped
    # instead of raising, contradicting the class's own docstring
    # ("literal/path-building content... are not meaningful for
    # csvpaths and are rejected"). This is the fix -- see
    # ReferenceFinder3._check_position().
    #
    POSITIONS = {
        # FILES/RESULTS: name_one PATH-BUILDING position (a segment
        # within name_one.path, alongside literal/'*' segments -- see
        # the shared ReferenceFinder3._compile_path_pattern(), which
        # already enforces this on its own; not part of the trailing
        # function-chain _check_position() validates).
        Reference3.FILES: (Reference3.NAME_ONE,),
        Reference3.CSVPATHS: (),
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }

    def check_valid(self) -> None:
        """same ARG_TYPES/ARG_REQUIRED check every function gets, plus
        an eager regex-syntax check when the arg is a Regex3 -- fail at
        build time (ReferenceFunctionFactory.build() already calls this
        right after constructing), not later, deep inside path-matching,
        the first time a candidate happens to be compared against it."""
        super().check_valid()
        if isinstance(self._arg, Regex3):
            try:
                re.compile(self._arg.pattern)
            except re.error as e:
                raise ReferenceException3(f":name() regex is invalid: {e}") from e
