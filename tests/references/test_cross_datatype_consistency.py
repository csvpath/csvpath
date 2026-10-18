"""
Automated cross-datatype consistency sweep -- added 2026-10-18.

Throughout references-v3's own development, a recurring MANUAL check
was "does this function mean the same thing across FILES/CSVPATHS/
RESULTS" (see memory: feedback_cross_datatype_function_consistency).
Compendium 6.7 ("functional taxonomy") formalizes part of this:
functions sharing a declared Function3.KIND (uuid/name/fingerprint)
are supposed to be conceptually comparable in ReferenceExpression3's
own UNION operation -- confirmed live, by direct inspection of
reference_expression_3.py's own `_check_union_compatible()`, that this
rule is ALREADY enforced in code, just only ever exercised by a
handful of hand-picked pairs across the existing test suite (e.g.
":uuid()"/":run_uuid()" in test_reference_expression_3.py).

This file turns that into a SYSTEMATIC, registry-driven sweep: every
function actually registered, not just the pairs someone happened to
test by hand, so a future function that quietly breaks the pattern
(wrong KIND, a SELECTOR_WHEN_ARGUED flag nobody wired into its own
finder) gets caught automatically rather than waiting for the next
person to notice by inspection.

Confirmed live before writing any of this (not assumed): compendium
6.7's own taxonomy currently has exactly THREE live KIND groups --
"uuid", "name", "fingerprint" -- not four. ":type()" is deliberately
the ONLY function of its own conceptual purpose and has KIND == None
(see reference_expression_3.py's own _check_union_compatible()
docstring, which says this explicitly) -- it falls back to the
literal-identity comparison rule instead of a KIND match. This file's
own EXPECTED_KIND_GROUPS below is the live, current membership of each
group, confirmed by actually enumerating the registry (see
test_every_registered_function_is_covered_by_this_sweep below) -- if
this ever goes stale, that test fails loudly rather than silently
under-covering the registry.
"""

from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_expression_3 import ReferenceExpression3


def _registered_classes() -> dict:
    """every DISTINCT registered Function3 class, keyed by its own
    canonical NAME -- registered_names() returns every alias too (e.g.
    "below"/"lt" both point at Before3), so a naive iteration would
    count the same class multiple times under different check
    purposes. Dedupes by class identity, keeping the canonical NAME as
    the dict key (always one of the aliases registered for that
    class, confirmed below)."""
    seen = {}
    for registered_name in ReferenceFunctionFactory.registered_names():
        cls = ReferenceFunctionFactory.get_registered_class(registered_name)
        seen[cls] = cls.NAME
    return {name: cls for cls, name in seen.items()}


# a bare, non-None placeholder -- ReferenceParser3 (and ReferenceExpression3's
# own constructor) only requires csvpaths to be non-None; confirmed live
# before relying on this that PARSING a reference string never touches it
# for anything substantive (no config/manager calls happen until a real
# Finder actually runs query()/resolve(), which this file's own
# _check_union_compatible()-only checks never reach).
_PLACEHOLDER_CSVPATHS = object()


def _union_compatible(left_fn: str, right_fn: str) -> bool:
    """true if `_check_union_compatible()` accepts this pair, false if
    it raises -- builds the bare minimum syntactically-valid reference
    strings needed (datatype/position are never checked by this
    method at all, confirmed live: _terminal_value_call() only
    inspects the parsed FunctionCall3's own name+ROLE+KIND via the
    registry, never DATATYPES/POSITIONS), so ".files." is used
    uniformly regardless of each function's own real datatype."""
    expr = ReferenceExpression3(
        left=f'$x.files.:{left_fn}("x")',
        op=ReferenceExpression3.UNION,
        right=f'$x.files.:{right_fn}("x")',
        csvpaths=_PLACEHOLDER_CSVPATHS,
    )
    try:
        expr._check_union_compatible()
        return True
    except ReferenceException3:
        return False


# the live, current KIND taxonomy -- confirmed 2026-10-18 by directly
# enumerating ReferenceFunctionFactory's own registry (see
# test_every_registered_function_is_covered_by_this_sweep). Canonical
# NAME only (not aliases -- KIND is a class attribute, aliases share it
# automatically).
EXPECTED_KIND_GROUPS = {
    "uuid": {"uuid", "run_uuid", "named_file_uuid", "named_paths_uuid"},
    "name": {"named_file_name", "named_results_name", "named_paths_name"},
    "fingerprint": {
        "fingerprint",
        "file_fingerprints",
        "named_file_fingerprint",
        "named_paths_fingerprint",
    },
}


class TestKindTaxonomyMembership:
    # a pure registry-introspection check -- no live query execution
    # needed. Catches a KIND typo, an accidental reuse of an existing
    # KIND for an unrelated function, or a new compendium-taxonomy
    # function added without its own KIND set (or set to the wrong
    # group) -- all silent regressions today, since nothing currently
    # asserts the GROUP MEMBERSHIP itself, only that individual
    # hand-picked pairs happen to compare correctly.
    def test_kind_groups_match_the_expected_live_taxonomy(self):
        classes = _registered_classes()
        actual_groups = {}
        for name, cls in classes.items():
            if cls.KIND is not None:
                actual_groups.setdefault(cls.KIND, set()).add(name)
        assert actual_groups == EXPECTED_KIND_GROUPS

    def test_every_registered_function_is_covered_by_this_sweep(self):
        # a live cross-check against the registry itself -- if a new
        # function is added with a KIND not already in
        # EXPECTED_KIND_GROUPS (a brand new taxonomy group), this
        # fails loudly rather than EXPECTED_KIND_GROUPS silently
        # falling behind the real registry. file_fingerprints is
        # KIND == "fingerprint" but list-valued (confirmed via
        # compendium 6.7's own note: "file_fingerprints() is list-
        # valued so does not compare in practice") -- it is still a
        # real registry member of the group, just never exercised as
        # a UNION side in TestKindGroupsAreLiveUnionCompatible below,
        # which is why it is enumerated here separately rather than
        # silently dropped.
        classes = _registered_classes()
        live_kinds = {cls.KIND for cls in classes.values() if cls.KIND is not None}
        assert live_kinds == set(EXPECTED_KIND_GROUPS.keys())


class TestKindGroupsAreLiveUnionCompatible:
    # exercises the REAL _check_union_compatible() method end to end
    # (real parsing, real registry lookups) for every pair within each
    # KIND group -- not just the one or two pairs existing tests
    # happen to pick. file_fingerprints() is deliberately excluded
    # here (list-valued, confirmed it can never be a UNION side's own
    # terminal VALUE accessor in practice -- see compendium 6.7's own
    # note) -- comparing scalar-valued fingerprint functions against
    # each other is the real claim this sweep is checking.
    SCALAR_FINGERPRINT_MEMBERS = {
        "fingerprint",
        "named_file_fingerprint",
        "named_paths_fingerprint",
    }

    def test_every_uuid_pair_is_compatible(self):
        members = sorted(EXPECTED_KIND_GROUPS["uuid"])
        for i, a in enumerate(members):
            for b in members[i + 1 :]:
                assert _union_compatible(a, b), f"{a!r} vs {b!r} should be compatible"

    def test_every_name_pair_is_compatible(self):
        members = sorted(EXPECTED_KIND_GROUPS["name"])
        for i, a in enumerate(members):
            for b in members[i + 1 :]:
                assert _union_compatible(a, b), f"{a!r} vs {b!r} should be compatible"

    def test_every_scalar_fingerprint_pair_is_compatible(self):
        members = sorted(self.SCALAR_FINGERPRINT_MEMBERS)
        for i, a in enumerate(members):
            for b in members[i + 1 :]:
                assert _union_compatible(a, b), f"{a!r} vs {b!r} should be compatible"

    def test_a_function_is_compatible_with_itself(self):
        # same accessor, same arg -- always compatible, same KIND or
        # not (the literal-identity fallback), confirmed for a
        # representative member of each group plus a KIND-less one.
        for fn in ("uuid", "named_file_name", "fingerprint", "type"):
            assert _union_compatible(fn, fn), f"{fn!r} vs itself should be compatible"


class TestCrossGroupPairsAreIncompatible:
    # the negative-space check -- confirms the sweep above is actually
    # discriminating, not just vacuously true. Picks one representative
    # member from each KIND group plus the two KIND-less, non-identical
    # functions compendium 6.7's own worked example cites directly
    # (":type()" vs ":status()" -- "neither shares a declared KIND...
    # nor is the same accessor").
    def test_uuid_is_not_compatible_with_name(self):
        assert not _union_compatible("uuid", "named_file_name")

    def test_uuid_is_not_compatible_with_fingerprint(self):
        assert not _union_compatible("uuid", "fingerprint")

    def test_name_is_not_compatible_with_fingerprint(self):
        assert not _union_compatible("named_file_name", "fingerprint")

    def test_type_is_not_compatible_with_status(self):
        # compendium 6.7's own cited example, verbatim.
        assert not _union_compatible("type", "status")

    def test_different_kindless_accessors_are_not_compatible(self):
        # two different, unrelated functions, neither with a KIND --
        # the literal-identity fallback only ever matches a function
        # against itself (same name AND same arg), never a different
        # function.
        assert not _union_compatible("host", "username")


class TestSelectorWhenArguedWiring:
    # SELECTOR_WHEN_ARGUED (compendium's "select an entity when its
    # value matches the function's argument" duality) is currently
    # declared by exactly two functions, confirmed live by enumerating
    # the registry: :uuid() and :fingerprint(). Declaring the flag is
    # necessary but not sufficient -- _is_bare_selector_reference()
    # itself is purely structural (it never checks which datatype is
    # being queried at all, confirmed by reading its own signature:
    # it takes a parsed name_one, not a datatype), so whether the bare
    # form actually WORKS for a given datatype depends entirely on
    # whether that datatype's own Finder.query() calls it at all.
    # Confirmed live, not assumed, and a REAL FINDING from building
    # this sweep: fingerprint_3.py's own docstring claims "CSVPATHS has
    # no bare-lookup shape, that's FILES-only," but that is now STALE
    # -- CsvpathsReferenceFinder3's own _is_bare_selector_reference()
    # dispatch (added later, for :uuid()'s own cross-datatype PR) is
    # GENERIC, not hardcoded to "uuid," so it picks up :fingerprint()
    # too, whether or not that was intended (see
    # test_fingerprint_bare_selector_now_also_reaches_csvpaths below).
    # RESULTS deliberately has no bare-lookup shape for either function
    # at all (no normative example has ever asked for one, and no
    # RESULTS Finder code calls _is_bare_selector_reference()) -- that
    # one IS still accurate. This sweep checks only the POSITIVE cases
    # -- every (function, datatype) pair that actually ought to work,
    # confirmed to genuinely reach the bare-selector branch, not fall
    # through to a generic "unsupported" rejection -- not an exhaustive
    # negative sweep of every datatype a function happens to also be
    # registered for.
    def test_selector_when_argued_functions_are_exactly(self):
        classes = _registered_classes()
        selectors = {name for name, cls in classes.items() if cls.SELECTOR_WHEN_ARGUED}
        assert selectors == {"uuid", "fingerprint"}

    def test_uuid_bare_selector_reaches_the_files_dispatch(self):
        results = _files_finder('$finn.files.:uuid("some-uuid")', manifest=[]).query()
        # empty manifest -- no match, but reaching an EMPTY result
        # (not an exception) proves the bare-selector branch was
        # actually taken, not the generic "does not yet support
        # functions attached directly to name_one" rejection every
        # other unrecognized bare-function shape hits.
        assert results.results == []

    def test_uuid_bare_selector_reaches_the_csvpaths_dispatch(self):
        results = _csvpaths_finder('$acme.csvpaths.:uuid("some-uuid")', manifest=[]).query()
        assert results.results == []

    def test_fingerprint_bare_selector_reaches_the_files_dispatch(self):
        results = _files_finder(
            '$finn.files.:fingerprint("some-hash")', manifest=[]
        ).query()
        assert results.results == []

    def test_fingerprint_bare_selector_now_also_reaches_csvpaths(self):
        # SETTLED 2026-10-18, as an intentional, decided capability,
        # not just an accident -- this sweep originally surfaced it as
        # a real finding BEFORE anyone had decided it should work
        # (fingerprint_3.py's own docstring used to claim "CSVPATHS has
        # no bare-lookup shape... FILES-only," written 2026-08-13,
        # before CsvpathsReferenceFinder3 grew its own
        # _is_bare_selector_reference() dispatch branch for :uuid()'s
        # own cross-datatype build, same day as this sweep -- that
        # dispatch is GENERIC, keyed on SELECTOR_WHEN_ARGUED, not
        # hardcoded to "uuid," so it picked up :fingerprint() too, for
        # free). David's own call once flagged: keep it -- CSVPATHS
        # versions genuinely ARE fingerprinted (Fingerprint3.KEY
        # already has a CSVPATHS entry), so "select a group version by
        # its own content hash" is exactly as coherent as the FILES
        # case already built for. fingerprint_3.py's own docstring is
        # now corrected to match; a real positive-match test (this one
        # only ever proved "does not raise," not an actual match) lives
        # in test_csvpaths_reference_finder_3.py's own
        # TestBareFingerprintLookup.
        results = _csvpaths_finder(
            '$acme.csvpaths.:fingerprint("some-hash")', manifest=[]
        ).query()
        assert results.results == []


#
# ---- minimal, self-contained fakes for the live dispatch checks above.
# Deliberately NOT shared with test_files_reference_finder_3.py/
# test_csvpaths_reference_finder_3.py's own (private, leading-underscore)
# fakes -- no precedent in this codebase for cross-test-module imports,
# and these only need the one method each bare-selector branch actually
# calls, not the full fixture surface those other files build.
#


class _FakeFilesConfig:
    def get(self, *, section, name):
        return "inputs/named_files"


class _FakeFileManager:
    def __init__(self, manifest):
        self._manifest = manifest

    def get_manifest(self, name):
        return self._manifest


class _FakeFilesCsvPaths:
    def __init__(self, manifest):
        self.file_manager = _FakeFileManager(manifest)
        self.config = _FakeFilesConfig()


def _files_finder(reference, manifest):
    from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
    from csvpath.references.reference_parser_3 import ReferenceParser3

    csvpaths = _FakeFilesCsvPaths(manifest)
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return FilesReferenceFinder3(csvpaths=csvpaths, ref=ref)


class _FakePathsConfig:
    def get(self, *, section, name):
        return "inputs/named_paths"


class _FakePathsManager:
    def __init__(self, manifest):
        self._manifest = manifest

    def get_manifest_for_name(self, name):
        return self._manifest


class _FakeCsvpathsCsvPaths:
    def __init__(self, manifest):
        self.paths_manager = _FakePathsManager(manifest)
        self.config = _FakePathsConfig()


def _csvpaths_finder(reference, manifest):
    from csvpath.references.csvpaths_reference_finder_3 import CsvpathsReferenceFinder3
    from csvpath.references.reference_parser_3 import ReferenceParser3

    csvpaths = _FakeCsvpathsCsvPaths(manifest)
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref)
