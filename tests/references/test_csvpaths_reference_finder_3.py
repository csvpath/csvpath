import pytest

from csvpath.references.csvpaths_reference_finder_3 import CsvpathsReferenceFinder3
from csvpath.references.reference_3 import Star3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.reference_results_3 import ReferenceResult3


#
# fixture: named-paths group "acme" with two loaded versions. version 0
# has two statements (one identified as "company_names", one unnamed --
# unnamed statements get the stringified load-time index as their
# identity, per PathsManager.add_named_paths); version 1 has one
# unnamed statement. group_file_path is identical across every version
# -- there is only one group.csvpath file, ever, regardless of version
# (confirmed against PathsRegistrar.metadata_update's real manifest
# schema).
#
GROUP_FILE_PATH = "named_paths/acme/group.csvpath"
ACME_MANIFEST = [
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v0-uuid",
        "named_paths": ["stmt text A", "stmt text B"],
        "named_paths_identities": ["company_names", "1"],
    },
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v1-uuid",
        "named_paths": ["stmt text C"],
        "named_paths_identities": ["0"],
    },
]


GROUP_HOME = "named_paths/acme"


class _FakePathsDescriber:
    def __init__(self, definition: dict, definitions_by_name: dict | None = None):
        self._definition = definition
        self._definitions_by_name = definitions_by_name

    def get_config(self, name):
        from csvpath.managers.paths.paths_descriptor import GroupConfig

        if self._definitions_by_name is not None:
            return GroupConfig(**self._definitions_by_name[name])
        return GroupConfig(**self._definition)


class _FakePathsManager:
    def __init__(
        self,
        manifest,
        home=GROUP_HOME,
        definition: dict | None = None,
        ledger=None,
        by_name: dict | None = None,
        definitions_by_name: dict | None = None,
    ):
        self._manifest = manifest
        self._home = home
        self._definition = definition or {}
        self._ledger = manifest if ledger is None else ledger
        # by_name: {name: manifest} -- only used by '*' traversal tests,
        # which need more than one distinct named-paths group. Every
        # other test uses the single manifest above.
        self._by_name = by_name
        # definitions_by_name: {name: definition} -- only used by '*'
        # traversal tests for definition.json-backed fields (:scripts()
        # etc), to prove the CORRECT group's own definition is read, not
        # just any -- added 2026-08-18 alongside _group_manifest_entry().
        self._definitions_by_name = definitions_by_name

    def get_manifest_for_name(self, name):
        if self._by_name is not None:
            return self._by_name[name]
        return self._manifest

    def named_paths_home(self, name):
        return self._home

    @property
    def named_paths_names(self):
        if self._by_name is not None:
            return list(self._by_name.keys())
        return []

    @property
    def paths_root_manifest(self):
        return self._ledger

    @property
    def describer(self):
        return _FakePathsDescriber(self._definition, self._definitions_by_name)


class _FakeConfig:
    def __init__(
        self,
        inputs_csvpaths_path: str | None = None,
        log_file: str | None = None,
    ):
        self.inputs_csvpaths_path = inputs_csvpaths_path
        self.log_file = log_file


class _FakeCsvPaths:
    def __init__(
        self,
        paths_manager,
        inputs_csvpaths_path: str | None = None,
        log_file: str | None = None,
    ):
        self.paths_manager = paths_manager
        self.config = _FakeConfig(inputs_csvpaths_path, log_file=log_file)


def _finder(
    reference: str,
    manifest: list = ACME_MANIFEST,
    definition: dict | None = None,
    inputs_csvpaths_path: str | None = None,
    ledger: list | None = None,
    by_name: dict | None = None,
    definitions_by_name: dict | None = None,
    log_file: str | None = None,
) -> CsvpathsReferenceFinder3:
    csvpaths = _FakeCsvPaths(
        _FakePathsManager(
            manifest,
            definition=definition,
            ledger=ledger,
            by_name=by_name,
            definitions_by_name=definitions_by_name,
        ),
        inputs_csvpaths_path=inputs_csvpaths_path,
        log_file=log_file,
    )
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref)


class TestVersionPointer:
    def test_last(self):
        results = _finder("$acme.csvpaths.:last()").query()
        assert results.files == [GROUP_FILE_PATH]
        assert results.uuids == ["v1-uuid"]

    def test_first(self):
        results = _finder("$acme.csvpaths.:first()").query()
        assert results.uuids == ["v0-uuid"]

    def test_index(self):
        results = _finder("$acme.csvpaths.:index(0)").query()
        assert results.uuids == ["v0-uuid"]

    def test_index_out_of_range_returns_empty_not_an_error(self):
        results = _finder("$acme.csvpaths.:index(99)").query()
        assert results.files == []

    def test_chained_functions_combine_with_name_ones_own_chain(self):
        # :last() occupies the sole path-segment, :index(0) is name_one's
        # own trailing function chain -- both get combined into one
        # chain; index(0) is the only pointer among the two once
        # combined... except :last() is ALSO a pointer, so this should
        # raise (two pointers, same chain).
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:last():index(0)").query()


class TestNoPointerReturnsEveryVersion:
    # a chain with no pointer at all (e.g. a bare :all()) does not
    # narrow to one version -- every version in the manifest comes
    # back, unreduced. This is how "Name_one used alone == list of
    # versions in the form: (path-to-group.csvpaths, uuid)" (STRUCTURE
    # table) is actually reached.
    def test_bare_all_returns_every_version(self):
        results = _finder("$acme.csvpaths.:all()").query()
        assert results.files == [GROUP_FILE_PATH, GROUP_FILE_PATH]
        assert results.uuids == ["v0-uuid", "v1-uuid"]

    def test_all_combined_with_name_three_filters_each_version(self):
        # only versions containing the matching identity come back --
        # "company_names" only exists in v0's identities.
        results = _finder("$acme.csvpaths.:all().company_names").query()
        assert results.uuids == ["v0-uuid"]

    def test_all_with_no_matches_at_all_returns_empty(self):
        results = _finder("$acme.csvpaths.:all().nope").query()
        assert results.files == []


class TestHaving:
    # ':having("identity")' -- added 2026-08-13, filters the version
    # list down to versions whose own "named_paths_identities" actually
    # contains that identity, before any pointer reduces further --
    # "company_names" only exists in ACME_MANIFEST's v0.
    def test_having_then_pointer_reduces_the_filtered_list(self):
        results = _finder("$acme.csvpaths.:having(\"company_names\"):last()").query()
        assert results.uuids == ["v0-uuid"]

    def test_having_alone_lists_matching_versions_unreduced(self):
        results = _finder('$acme.csvpaths.:having("company_names")').query()
        assert results.uuids == ["v0-uuid"]

    def test_having_with_no_matching_version_is_empty(self):
        results = _finder('$acme.csvpaths.:having("nope")').query()
        assert results.uuids == []

    def test_having_matches_an_unnamed_statements_stringified_index_too(self):
        # v1's sole statement is unnamed -- its identity is "0" (the
        # stringified load-time index), same convention name_three
        # identity lookups already use.
        results = _finder('$acme.csvpaths.:having("0"):last()').query()
        assert results.uuids == ["v1-uuid"]

    def test_having_requires_an_argument(self):
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:having():last()").query()


VERSION_RANGE_GROUP_FILE_PATH = "named_paths/dater/group.csvpath"
VERSION_RANGE_MANIFEST = [
    {
        "group_file_path": VERSION_RANGE_GROUP_FILE_PATH,
        "uuid": f"v{i}-uuid",
        "named_paths": [f"stmt {i} text"],
        "named_paths_identities": [str(i)],
        "time": f"2026-01-0{i + 1}T00:00:00+00:00",
    }
    for i in range(5)
]


class TestVersionRange:
    # ':from()'/':to()' as a name_one VERSION range -- added 2026-08-13,
    # David: a named-paths group's own load time is a real arrival-date
    # concept ("give me the versions loaded between date-one and
    # date-two"), the same one RESULTS'/FILES' own version-level ranges
    # already filter by. Windows the (possibly ':having()'-filtered)
    # manifest -- a real pointer riding alongside reduces the RANGE, not
    # the full candidate set, same as RESULTS/FILES.
    def test_from_index_negative_gives_the_last_n_versions(self):
        results = _finder(
            "$dater.csvpaths.:from(-2)", VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v3-uuid", "v4-uuid"]

    def test_from_and_to_together_is_an_inclusive_range(self):
        results = _finder(
            "$dater.csvpaths.:from(1):to(3)", VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v1-uuid", "v2-uuid", "v3-uuid"]

    def test_a_pointer_reduces_the_range_not_the_full_candidate_set(self):
        results = _finder(
            "$dater.csvpaths.:from(-3):last()", VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v4-uuid"]

    def test_date_mode_from_filters_by_the_versions_own_load_time(self):
        results = _finder(
            '$dater.csvpaths.:from(:date("2026-01-03"))', VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v2-uuid", "v3-uuid", "v4-uuid"]

    def test_date_mode_from_and_to_together_is_an_inclusive_range(self):
        results = _finder(
            '$dater.csvpaths.:from("2026-01-02"):to("2026-01-04")',
            VERSION_RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v1-uuid", "v2-uuid", "v3-uuid"]

    def test_mixing_index_mode_and_date_mode_bounds_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$dater.csvpaths.:from(1):to(:date("2026-01-01"))',
                VERSION_RANGE_MANIFEST,
            ).query()

    def test_a_malformed_date_bound_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$dater.csvpaths.:from("not-a-date")', VERSION_RANGE_MANIFEST
            ).query()

    def test_having_filters_before_the_range_windows(self):
        # ':having("4")' only matches v4, so the range (last 3) has just
        # that one entry to window -- confirms the two compose in the
        # order the docstring describes (having, then range, then
        # pointer), not independently.
        results = _finder(
            '$dater.csvpaths.:having("4"):from(-3)', VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v4-uuid"]

    def test_range_combined_with_star_traversal_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.csvpaths.:from(-2):last()",
                VERSION_RANGE_MANIFEST,
                by_name={"dater": VERSION_RANGE_MANIFEST},
            ).query()


class TestIdentityLookupOnNameThree:
    def test_matches_named_identity(self):
        results = _finder("$acme.csvpaths.:first().company_names").query()
        assert results.uuids == ["v0-uuid"]

    def test_matches_stringified_index_identity(self):
        results = _finder("$acme.csvpaths.:last().0").query()
        assert results.uuids == ["v1-uuid"]

    def test_no_matching_identity_returns_empty(self):
        results = _finder("$acme.csvpaths.:first().nope").query()
        assert results.files == []

    def test_name_three_does_not_change_path_or_uuid(self):
        # per the STRUCTURE table: querying at name_three gives the same
        # (path, uuid) as name_one alone for csvpaths -- name_three only
        # adds an existence constraint, it does not select a different
        # physical thing (there isn't one -- one file, one uuid per
        # version, regardless of which statement within it). identity
        # DOES differ (added 2026-08-13, see ReferenceResult3.identity's
        # own docstring) -- that is the whole point of it, not a bug.
        with_three = _finder("$acme.csvpaths.:first().company_names").query()
        without_three = _finder("$acme.csvpaths.:first()").query()
        assert with_three.files == without_three.files
        assert with_three.uuids == without_three.uuids
        assert with_three.results[0].identity == "company_names"
        assert without_three.results[0].identity is None


RANGE_GROUP_FILE_PATH = "named_paths/ranger/group.csvpath"
RANGE_MANIFEST = [
    {
        "group_file_path": RANGE_GROUP_FILE_PATH,
        "uuid": "range-uuid",
        "named_paths": [
            "stmt one text",
            "stmt two text",
            "stmt three text",
            "stmt four text",
            "stmt five text",
        ],
        "named_paths_identities": ["one", "two", "three", "four", "five"],
    },
]


class TestNameThreeRange:
    # ':from()'/':to()' as a name_three statement range -- added
    # 2026-08-13, David's own FlightPath v2 use case: rewind/replay
    # starting from a specific csvpath statement (e.g.
    # "$acme.csvpaths.:last().:from(:index(2))"). Windows the matched
    # version's own ordered "named_paths_identities" list; each windowed
    # result carries its OWN identity since csvpaths has no per-
    # statement uuid (see ReferenceResult3.identity's own docstring).
    def test_from_index_negative_gives_the_last_n(self):
        results = _finder(
            "$ranger.csvpaths.:first().:from(-2)", RANGE_MANIFEST
        ).query()
        assert [r.identity for r in results.results] == ["four", "five"]
        assert results.uuids == ["range-uuid", "range-uuid"]
        assert results.files == [RANGE_GROUP_FILE_PATH, RANGE_GROUP_FILE_PATH]

    def test_from_and_to_together_is_an_inclusive_range(self):
        results = _finder(
            "$ranger.csvpaths.:first().:from(:index(1)):to(:index(3))",
            RANGE_MANIFEST,
        ).query()
        assert [r.identity for r in results.results] == ["two", "three", "four"]

    def test_resolve_gives_each_windowed_statements_own_text(self):
        results = _finder(
            "$ranger.csvpaths.:first().:from(:index(1)):to(:index(2))",
            RANGE_MANIFEST,
        ).resolve()
        assert [r.data for r in results.results] == [
            "stmt two text",
            "stmt three text",
        ]

    def test_date_mode_is_not_supported(self):
        # csvpaths statements have no arrival date of their own -- only
        # index-mode bounds are meaningful.
        with pytest.raises(ReferenceException3):
            _finder(
                '$ranger.csvpaths.:first().:from(:date("2025-01-01"))',
                RANGE_MANIFEST,
            ).query()

    def test_combining_a_literal_identity_with_a_range_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$ranger.csvpaths.:first().one:from(-1)", RANGE_MANIFEST
            ).query()

    def test_an_unrecognized_function_on_name_three_is_rejected(self):
        # anything other than a literal identity or ':from()'/':to()'
        # is not yet supported on name_three -- e.g. a pointer riding
        # alongside the range, which FILES allows but csvpaths does not.
        with pytest.raises(ReferenceException3):
            _finder(
                "$ranger.csvpaths.:first().:from(-2):last()", RANGE_MANIFEST
            ).query()


class TestResolve:
    def test_resolving_a_named_identity_gives_its_statement_text(self):
        results = _finder("$acme.csvpaths.:first().company_names").resolve()
        assert results.results[0].data == "stmt text A"

    def test_resolving_a_stringified_index_identity_gives_its_statement_text(self):
        results = _finder("$acme.csvpaths.:last().0").resolve()
        assert results.results[0].data == "stmt text C"

    def test_resolving_with_no_name_three_gives_none(self):
        # a whole group version has no single unambiguous payload.
        results = _finder("$acme.csvpaths.:last()").resolve()
        assert results.results[0].data is None


class TestManifestFunction:
    # ":manifest()" is a name_one-terminal, bare/sole-content shape --
    # it bypasses _resolve_versions()'s version-selection pipeline
    # entirely and points at the named-paths group's own manifest.json
    # instead (one fixed resource per group, covering every version).
    def test_query_returns_the_manifest_path_with_no_uuid(self):
        results = _finder("$acme.csvpaths.:manifest()").query()
        assert results.files == [f"{GROUP_HOME}/manifest.json"]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_manifest_files_raw_bytes(self, tmp_path):
        content = b"[]"
        home = tmp_path / "acme"
        home.mkdir()
        (home / "manifest.json").write_bytes(content)
        csvpaths = _FakeCsvPaths(_FakePathsManager(ACME_MANIFEST, home=str(home)))
        ref = ReferenceParser3(string="$acme.csvpaths.:manifest()", csvpaths=csvpaths)
        finder = CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref)
        results = finder.resolve()
        assert results.results[0].data == content

    def test_manifest_beside_a_version_pointer_gives_the_one_matched_entry(self):
        # :manifest() never narrows/selects itself (VALUE role, not
        # POINTER -- see functions/manifest_3.py) -- it can ride
        # alongside :last() in the same combined chain without tripping
        # "at most one pointer per chain". :last() still reduces to one
        # version; :manifest() changes what that version resolves to.
        results = _finder("$acme.csvpaths.:last():manifest()").resolve()
        assert results.uuids == ["v1-uuid"]
        assert results.results[0].data == ACME_MANIFEST[1]

    def test_manifest_with_all_and_no_pointer_raises(self):
        # :all() (CONTEXT_SETTER) plus :manifest() (VALUE) -- neither is
        # a pointer, and ACME_MANIFEST has two versions. Resolving full
        # manifest content always touches exactly one entity (settled
        # 2026-08-07), so this is illegal -- a pointer is required to
        # pick one version. query() itself succeeds (moved 2026-08-26,
        # see the ":path()" retirement/Rule 1 bucket-list entry) -- only
        # resolve() raises, once something actually tries to read the
        # content.
        finder = _finder("$acme.csvpaths.:all():manifest()")
        assert len(finder.query()) > 1
        with pytest.raises(ReferenceException3):
            finder.resolve()

    def test_manifest_with_no_pointer_and_exactly_one_version_still_works(self):
        single_version = [ACME_MANIFEST[0]]
        results = _finder("$acme.csvpaths.:all():manifest()", single_version).resolve()
        assert results.uuids == ["v0-uuid"]
        assert results.results[0].data == single_version[0]


class TestGlobalLoadsLedger:
    # Rule 1a: "*" at root_major combined with a bare :manifest() is the
    # one exception to root_major=="*" being unsupported -- it resolves
    # to the Named-Paths Loads Manifest, a single global ledger at the
    # named-paths root tracking every load across every named-paths
    # group.
    def test_query_returns_the_global_ledger_path_with_no_uuid(self):
        results = _finder(
            "$*.csvpaths.:manifest()",
            inputs_csvpaths_path="inputs/named_paths",
        ).query()
        assert results.files == ["inputs/named_paths/manifest.json"]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_global_ledgers_raw_bytes(self, tmp_path):
        content = b'[{"named_paths_name": "acme"}, {"named_paths_name": "beta"}]'
        root = tmp_path / "named_paths"
        root.mkdir()
        (root / "manifest.json").write_bytes(content)
        finder = _finder(
            "$*.csvpaths.:manifest()", inputs_csvpaths_path=str(root)
        )
        results = finder.resolve()
        assert results.results[0].data == content

    def test_star_with_definition_is_still_not_supported(self):
        finder = _finder(
            "$*.csvpaths.:definition()",
            inputs_csvpaths_path="inputs/named_paths",
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_star_root_major_with_no_named_paths_groups_gives_empty_results(self):
        # '*' traversal is supported now (see TestStarTraversal below) --
        # with zero named-paths groups to enumerate (no by_name given
        # here), it correctly finds nothing rather than raising.
        finder = _finder(
            "$*.csvpaths.:last()", inputs_csvpaths_path="inputs/named_paths"
        )
        assert finder.query().results == []


LOADS_LEDGER = [
    {"named_paths_name": "acme", "uuid": "u-loads-1"},
    {"named_paths_name": "beta", "uuid": "u-loads-2"},
    {"named_paths_name": "gamma", "uuid": "u-loads-3"},
]


class TestGlobalLoadsLedgerOrdinalIndexing:
    # Rule 1b: a pointer (:first()/:last()/:index(n)) riding before the
    # bare :manifest() selects one entry out of the ledger by ordinal
    # position, instead of dumping the whole thing.
    def test_last_gives_the_most_recent_load(self):
        finder = _finder(
            "$*.csvpaths.:last():manifest()",
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        )
        results = finder.resolve()
        assert results.results[0].data == LOADS_LEDGER[-1]

    def test_index_gives_the_nth_load(self):
        finder = _finder(
            "$*.csvpaths.:index(0):manifest()",
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        )
        results = finder.resolve()
        assert results.results[0].data == LOADS_LEDGER[0]

    def test_out_of_range_index_gives_no_results(self):
        finder = _finder(
            "$*.csvpaths.:index(99):manifest()",
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        )
        results = finder.query()
        assert len(results.results) == 0

    def test_query_gives_the_ledger_path_with_the_entrys_own_uuid(self):
        finder = _finder(
            "$*.csvpaths.:last():manifest()",
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        )
        results = finder.query()
        assert results.files == ["inputs/named_paths/manifest.json"]
        assert results.results[0].uuid == "u-loads-3"

    def test_manifest_then_pointer_order_also_works(self):
        # order-insensitivity was missing on _pointer_before_manifest
        # and fixed 2026-08-10.
        finder = _finder(
            "$*.csvpaths.:manifest():last()",
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        )
        results = finder.query()
        assert results.results[0].uuid == "u-loads-3"


#
# named-paths group alpha (2 versions) + beta (1 version). beta is
# listed FIRST in STAR_BY_NAME on purpose -- naive concatenation with no
# time-sort would put alpha's own last entry last in the pooled list, so
# a test asserting beta's true-latest entry wins would fail if the
# flatten case's time-sort were ever removed/broken.
#
STAR_ALPHA_MANIFEST = [
    {
        "group_file_path": "named_paths/alpha/group.csvpath",
        "uuid": "a-v1",
        "time": "2026-01-01T00:00:00+00:00",
    },
    {
        "group_file_path": "named_paths/alpha/group.csvpath",
        "uuid": "a-v2",
        "time": "2026-01-02T00:00:00+00:00",
    },
]
STAR_BETA_MANIFEST = [
    {
        "group_file_path": "named_paths/beta/group.csvpath",
        "uuid": "b-v1",
        "time": "2026-01-03T00:00:00+00:00",
    },
]
STAR_BY_NAME = {"beta": STAR_BETA_MANIFEST, "alpha": STAR_ALPHA_MANIFEST}


def _star_finder(reference: str) -> CsvpathsReferenceFinder3:
    # inputs_csvpaths_path is needed even for genuine (non-Rule-1a/1b)
    # traversal now: _extract_data()'s Star3 branch always computes the
    # ledger's own fixed path to disambiguate against, whether or not
    # this particular reference turns out to be the ledger-ordinal case
    # (fixed 2026-08-26, see csvpaths_reference_finder_3.py).
    return _finder(
        reference, by_name=STAR_BY_NAME, inputs_csvpaths_path="inputs/named_paths"
    )


class TestStarTraversalFlatten:
    # bare pointer, no ':all()' -- every named-paths group's whole
    # manifest pools into one combined list, sorted by true
    # chronological order (each entry's own "time"), reduced by one
    # terminal pointer.
    def test_last_across_every_group_is_the_true_most_recent(self):
        # beta's only version (2026-01-03) is the global most-recent,
        # not alpha's own last version (2026-01-02) -- proves pooling
        # crosses groups and is truly time-sorted, not just
        # concatenated in enumeration order.
        results = _star_finder("$*.csvpaths.:last()").query()
        assert results.uuids == ["b-v1"]

    def test_first_across_every_group_is_the_true_earliest(self):
        results = _star_finder("$*.csvpaths.:first()").query()
        assert results.uuids == ["a-v1"]

    def test_index_selects_by_chronological_position(self):
        # chronological order: a-v1, a-v2, b-v1
        results = _star_finder("$*.csvpaths.:index(1)").query()
        assert results.uuids == ["a-v2"]

    # no "combined with :manifest()" test in this class: a bare pointer
    # plus a bare ':manifest()' (e.g. ":last():manifest()") is always
    # exactly the two-function shape _pointer_before_manifest() matches
    # -- it is intercepted by Rule 1b in query() before ever reaching
    # _query_star_traversal, regardless of root_major being '*'. See
    # TestGlobalLoadsLedger for that already-existing, unaffected
    # behavior. TestStarTraversalGroup's own ':all():last():manifest()'
    # test below is what actually proves this class's sibling fix (the
    # traversal-guard exemption fixed 2026-08-26).

    def test_name_three_combined_with_traversal_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _star_finder("$*.csvpaths.:last().0").query()


class TestStarTraversalPoolNoPointerIsOptional:
    # a pointer is now optional in POOL/FLATTEN mode too (settled
    # 2026-08-19) -- previously the one place csvpaths' own star
    # traversal still required one unconditionally, an inconsistency
    # with GROUP mode's own no-pointer precedent (which already listed
    # everything per group, unreduced) and with RESULTS'/
    # FilesReferenceFinder3's star traversal (neither ever requires
    # one). Absence means every candidate across every group comes
    # back, unreduced. Unlike RESULTS/FILES, csvpaths' name_one always
    # requires SOME function as its sole path segment (no bare/literal-
    # path-only shape exists here at all, confirmed live: "$*.csvpaths."
    # with nothing after does not even parse) -- so POOL-mode-no-
    # pointer is only reachable via a field accessor or ':having()'
    # occupying that slot, not a truly empty reference.
    def test_no_pointer_with_a_field_accessor_is_poolable(self):
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                    "named_paths_name": "alpha",
                }
            ],
            "beta": [
                {
                    "group_file_path": "named_paths/beta/group.csvpath",
                    "uuid": "b-v1",
                    "time": "2026-01-03T00:00:00+00:00",
                    "named_paths_name": "beta",
                }
            ],
        }
        results = _finder(
            "$*.csvpaths.:named_paths_name()", by_name=by_name
        ).resolve()
        assert sorted((r.uuid, r.data) for r in results.results) == [
            ("a-v1", "alpha"),
            ("b-v1", "beta"),
        ]

    def test_previously_masked_unrecognized_function_now_raises(self):
        # a real, previously-latent bug this same fix exposed and
        # closed: the old check only ever rejected ":manifest()"/
        # ':from()'/':to()' BY NAME (a blacklist) -- any other
        # unrecognized function (e.g. ':definition()', confirmed via
        # TestGlobalLoadsLedger's own test) silently fell through
        # unrejected once "no pointer" stopped forcing a raise for an
        # unrelated reason. Now whitelist-based (only a pointer/':all()'
        # /':having()'/a field accessor are exempted), closing that gap
        # generally, not just for the one name already known about.
        with pytest.raises(ReferenceException3):
            _star_finder("$*.csvpaths.:groups()").query()


class TestStarTraversalFieldAccessor:
    # closes the gap ReferenceExpression3 needed -- a registered field-
    # accessor function can now ride alongside the pointer in '*'
    # traversal (added 2026-08-18), resolving from whichever real group
    # matched via _group_manifest_entry(), which re-derives the matched
    # group's own name/manifest from the uuid the pointer already
    # selected -- unlike RESULTS, CSVPATHS genuinely needs this, since
    # get_manifest_for_name(reference.root_major) breaks when
    # root_major is the '*' token (no group is actually named "*").
    def test_flatten_shape_with_a_field_accessor_now_works(self):
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                    "named_paths_name": "alpha",
                }
            ],
            "beta": [
                {
                    "group_file_path": "named_paths/beta/group.csvpath",
                    "uuid": "b-v1",
                    "time": "2026-01-03T00:00:00+00:00",
                    "named_paths_name": "beta",
                }
            ],
        }
        results = _finder(
            "$*.csvpaths.:last():named_paths_name()", by_name=by_name
        ).resolve()
        assert len(results.results) == 1
        assert results.results[0].uuid == "b-v1"
        assert results.results[0].data == "beta"

    def test_grouped_shape_with_a_field_accessor_now_works(self):
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                    "named_paths_name": "alpha",
                },
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v2",
                    "time": "2026-01-02T00:00:00+00:00",
                    "named_paths_name": "alpha",
                },
            ],
            "beta": [
                {
                    "group_file_path": "named_paths/beta/group.csvpath",
                    "uuid": "b-v1",
                    "time": "2026-01-03T00:00:00+00:00",
                    "named_paths_name": "beta",
                }
            ],
        }
        results = _finder(
            "$*.csvpaths.:all():last():named_paths_name()", by_name=by_name
        ).resolve()
        assert len(results.results) == 2
        assert {r.data for r in results.results} == {"alpha", "beta"}
        assert {r.uuid for r in results.results} == {"a-v2", "b-v1"}

    def test_field_accessor_combined_with_manifest_now_also_works(self):
        # ':manifest()' is now exempted from _query_star_traversal's
        # unsupported-combination check too (fixed 2026-08-26, the same
        # change that let a bare pointer/':all()' combine with it) -- so
        # this three-function chain no longer raises. resolve_kind()
        # gives a field-accessor function priority over ':manifest()'
        # when both are present in the same terminal chain (see
        # reference_3.py's own resolve_kind docstring: METADATA_FIELD is
        # checked before METADATA_FILE), so named_paths_name()'s own
        # value wins here and ':manifest()' rides along harmlessly,
        # unused -- same outcome as test_flatten_shape_with_a_field_
        # accessor_now_works above, just proving the extra function does
        # not change it.
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                    "named_paths_name": "alpha",
                }
            ],
            "beta": [
                {
                    "group_file_path": "named_paths/beta/group.csvpath",
                    "uuid": "b-v1",
                    "time": "2026-01-03T00:00:00+00:00",
                    "named_paths_name": "beta",
                }
            ],
        }
        results = _finder(
            "$*.csvpaths.:last():named_paths_name():manifest()", by_name=by_name
        ).resolve()
        assert len(results.results) == 1
        assert results.results[0].uuid == "b-v1"
        assert results.results[0].data == "beta"

    def test_definition_sourced_field_reads_the_matched_groups_own_config(self):
        # :scripts() (SOURCE == "definition") is the other branch
        # _group_manifest_entry() serves -- it needs the matched GROUP
        # NAME, not just its manifest entry, to call describer.get_
        # config(name). Proves the correct group's own definition.json
        # is read, not alpha's by accident, by giving each group a
        # different "scripts" config and asserting on beta's value.
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                }
            ],
            "beta": [
                {
                    "group_file_path": "named_paths/beta/group.csvpath",
                    "uuid": "b-v1",
                    "time": "2026-01-03T00:00:00+00:00",
                }
            ],
        }
        definitions_by_name = {
            "alpha": {"scripts": {"on_complete_all": "alpha_notify.py"}},
            "beta": {"scripts": {"on_complete_all": "beta_notify.py"}},
        }
        results = _finder(
            "$*.csvpaths.:last():scripts()",
            by_name=by_name,
            definitions_by_name=definitions_by_name,
        ).resolve()
        assert len(results.results) == 1
        assert results.results[0].uuid == "b-v1"
        assert results.results[0].data == {"on_complete_all": "beta_notify.py"}


class TestGroupManifestEntry:
    # _group_manifest_entry() -- added 2026-08-18 alongside the field-
    # accessor exemption above, so both the METADATA_FIELD manifest-
    # sourced branch and the :scripts()/:webhooks()/:transfers()/
    # :destinations() definition-sourced branch can re-derive which real
    # group a star-traversal result came from, tested directly here
    # rather than only indirectly through resolve().
    def test_star_root_major_finds_the_correct_group(self):
        by_name = {
            "alpha": [{"group_file_path": "x", "uuid": "a-v1"}],
            "beta": [{"group_file_path": "y", "uuid": "b-v1"}],
        }
        finder = _finder("$*.csvpaths.:last()", by_name=by_name)
        name, entry = finder._group_manifest_entry(Star3(), "b-v1")
        assert name == "beta"
        assert entry["uuid"] == "b-v1"

    def test_star_root_major_with_unknown_uuid_gives_none_none(self):
        by_name = {"alpha": [{"group_file_path": "x", "uuid": "a-v1"}]}
        finder = _finder("$*.csvpaths.:last()", by_name=by_name)
        name, entry = finder._group_manifest_entry(Star3(), "missing-uuid")
        assert name is None
        assert entry is None

    def test_literal_root_major_looks_up_directly_no_group_search(self):
        # a literal root_major never needs to search every group -- this
        # mirrors what every non-star call site did inline before this
        # helper existed.
        finder = _finder("$acme.csvpaths.:last()")
        name, entry = finder._group_manifest_entry("acme", "v1-uuid")
        assert name == "acme"
        assert entry["uuid"] == "v1-uuid"


class TestStarTraversalGroup:
    # ':all()' present in the combined name_one chain -- the pointer is
    # applied independently within each group's own manifest, one
    # result per group.
    def test_all_with_last_gives_one_result_per_group(self):
        results = _star_finder("$*.csvpaths.:all():last()").query()
        assert len(results.results) == 2
        assert set(results.uuids) == {"a-v2", "b-v1"}

    def test_all_with_first_gives_each_groups_earliest_version(self):
        results = _star_finder("$*.csvpaths.:all():first()").query()
        assert len(results.results) == 2
        assert set(results.uuids) == {"a-v1", "b-v1"}

    def test_all_with_no_pointer_gives_every_version_unreduced(self):
        # extends csvpaths' own existing single-group precedent (bare
        # :all() with no pointer -- test_bare_all_returns_every_version
        # above) across every group, rather than deduping to anything.
        results = _star_finder("$*.csvpaths.:all()").query()
        assert len(results.results) == 3
        assert set(results.uuids) == {"a-v1", "a-v2", "b-v1"}

    def test_all_with_last_and_manifest_gives_each_groups_own_manifest_entry(self):
        # previously unsupported (raised); fixed 2026-08-26 -- see
        # TestStarTraversalFlatten's own manifest test for the FLATTEN-
        # mode sibling of this fix. Proves the GROUP-mode reduction
        # (one version per group) and the manifest-entry lookup compose
        # correctly together, not just each in isolation.
        results = _star_finder("$*.csvpaths.:all():last():manifest()").resolve()
        assert len(results.results) == 2
        data_by_uuid = {r.uuid: r.data for r in results.results}
        assert data_by_uuid == {
            "a-v2": STAR_ALPHA_MANIFEST[1],
            "b-v1": STAR_BETA_MANIFEST[0],
        }


class TestStarTraversalHaving:
    # ':having("identity")' combined with '*' traversal -- added
    # 2026-08-18, alongside RESULTS' own ':flatten()' fix. Closes a
    # real, previously-latent bug, not just a missing feature: before
    # this fix ':having()' was never checked for at all in
    # _query_star_traversal -- neither rejected as unsupported NOR
    # applied -- so it was silently DROPPED (confirmed live before
    # writing these: "$*.csvpaths.:all():having('orders')" returned
    # EVERY group's every version, unfiltered, not just the matching
    # ones).
    HAVING_BY_NAME = {
        "alpha": [
            {
                "group_file_path": "named_paths/alpha/group.csvpath",
                "uuid": "a-v1",
                "time": "2026-01-01T00:00:00+00:00",
                "named_paths_identities": ["orders"],
                "named_paths_name": "alpha",
            },
            {
                "group_file_path": "named_paths/alpha/group.csvpath",
                "uuid": "a-v2",
                "time": "2026-01-02T00:00:00+00:00",
                "named_paths_identities": ["other"],
                "named_paths_name": "alpha",
            },
        ],
        "beta": [
            {
                "group_file_path": "named_paths/beta/group.csvpath",
                "uuid": "b-v1",
                "time": "2026-01-03T00:00:00+00:00",
                "named_paths_identities": ["other"],
                "named_paths_name": "beta",
            }
        ],
    }

    def test_grouped_having_filters_out_non_matching_versions(self):
        # the actual bug this closes: without the fix, this returned all
        # three versions, unfiltered -- only a-v1 actually has "orders".
        results = _finder(
            "$*.csvpaths.:all():having(\"orders\")", by_name=self.HAVING_BY_NAME
        ).query()
        assert results.uuids == ["a-v1"]

    def test_grouped_having_with_pointer_gives_one_per_matching_group(self):
        # beta has no version with "orders" at all -- it contributes
        # nothing, not an empty/None placeholder.
        results = _finder(
            "$*.csvpaths.:having(\"orders\"):all():last()",
            by_name=self.HAVING_BY_NAME,
        ).query()
        assert results.uuids == ["a-v1"]

    def test_flatten_having_pools_filtered_versions_across_groups(self):
        # not grouped (no ':all()') -- filtered pool across every group,
        # reduced by the pointer, same as the ungrouped/flatten mode
        # already does for the unfiltered case.
        results = _finder(
            "$*.csvpaths.:having(\"orders\"):last()", by_name=self.HAVING_BY_NAME
        ).query()
        assert results.uuids == ["a-v1"]

    def test_having_combined_with_a_field_accessor_also_works(self):
        results = _finder(
            "$*.csvpaths.:having(\"orders\"):all():last():named_paths_name()",
            by_name=self.HAVING_BY_NAME,
        ).resolve()
        assert len(results.results) == 1
        assert results.results[0].uuid == "a-v1"
        assert results.results[0].data == "alpha"

    def test_having_with_no_matching_version_anywhere_is_empty(self):
        results = _finder(
            "$*.csvpaths.:all():having(\"nope\")", by_name=self.HAVING_BY_NAME
        ).query()
        assert results.results == []

    def test_bare_having_alone_with_no_pointer_lists_matching_versions(self):
        # a pointer is optional everywhere in csvpaths' star traversal
        # now (settled 2026-08-19, closing the one place it was still
        # required unconditionally) -- a bare ':having()' with no
        # pointer and no ':all()' means "every matching version, pooled
        # across every group, unreduced," the same POOL-mode-no-pointer
        # meaning a bare pointer-less reference now has too.
        results = _finder(
            "$*.csvpaths.:having(\"orders\")", by_name=self.HAVING_BY_NAME
        ).query()
        assert results.uuids == ["a-v1"]


class TestDefinitionFunction:
    # ":definition()" mirrors ":manifest()" exactly -- same bare, sole-
    # content shape, same query()/_extract_data() routing -- except
    # definition.json is genuinely optional, so resolving one that was
    # never written gives None rather than raising.
    def test_query_returns_the_definition_path_with_no_uuid(self):
        results = _finder("$acme.csvpaths.:definition()").query()
        assert results.files == [f"{GROUP_HOME}/definition.json"]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_definition_files_raw_bytes(self, tmp_path):
        content = b'{"_config": {}}'
        home = tmp_path / "acme"
        home.mkdir()
        (home / "definition.json").write_bytes(content)
        csvpaths = _FakeCsvPaths(_FakePathsManager(ACME_MANIFEST, home=str(home)))
        ref = ReferenceParser3(
            string="$acme.csvpaths.:definition()", csvpaths=csvpaths
        )
        finder = CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref)
        results = finder.resolve()
        assert results.results[0].data == content

    def test_resolve_gives_none_when_never_configured(self, tmp_path):
        home = tmp_path / "acme"
        home.mkdir()
        csvpaths = _FakeCsvPaths(_FakePathsManager(ACME_MANIFEST, home=str(home)))
        ref = ReferenceParser3(
            string="$acme.csvpaths.:definition()", csvpaths=csvpaths
        )
        finder = CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref)
        results = finder.resolve()
        assert results.results[0].data is None


RICH_MANIFEST = [
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v0-uuid",
        "named_paths": ["stmt text A", "stmt text B"],
        "named_paths_identities": ["company_names", "1"],
        "named_paths_count": 2,
        "time": "2026-01-01T00:00:00+00:00",
        "fingerprint": "aaaa",
        "source_path": "/staging/acme",
        "named_paths_home": GROUP_HOME,
    },
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v1-uuid",
        "named_paths": ["stmt text C"],
        "named_paths_identities": ["0"],
        "named_paths_count": 1,
        "time": "2026-02-01T00:00:00+00:00",
        "fingerprint": "bbbb",
        "source_path": "/staging/acme",
        "named_paths_home": GROUP_HOME,
    },
]


class TestFieldAccessorFunctions:
    # generalized field-accessor wiring (see manifest_field_functions_
    # proposal.md, Part A/B): each of these rides in name_one's own
    # combined chain exactly where :manifest() already rides, either
    # alone (every version, unreduced) or beside a version pointer (one
    # reduced version) -- but extracts one key from the matched entry
    # instead of the whole thing.
    def test_bare_uuid_with_no_pointer_gives_every_versions_uuid(self):
        results = _finder("$acme.csvpaths.:uuid()", RICH_MANIFEST).resolve()
        assert [r.data for r in results.results] == ["v0-uuid", "v1-uuid"]

    def test_uuid_beside_a_pointer_gives_the_one_matched_value(self):
        results = _finder("$acme.csvpaths.:last():uuid()", RICH_MANIFEST).resolve()
        assert results.results[0].data == "v1-uuid"

    def test_time(self):
        results = _finder("$acme.csvpaths.:first():time()", RICH_MANIFEST).resolve()
        assert results.results[0].data == "2026-01-01T00:00:00+00:00"

    def test_fingerprint(self):
        results = _finder(
            "$acme.csvpaths.:first():fingerprint()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == "aaaa"

    def test_home(self):
        results = _finder("$acme.csvpaths.:first():home()", RICH_MANIFEST).resolve()
        assert results.results[0].data == GROUP_HOME

    def test_origin_reads_the_source_path_key(self):
        results = _finder("$acme.csvpaths.:first():origin()", RICH_MANIFEST).resolve()
        assert results.results[0].data == "/staging/acme"

    def test_named_paths_identities(self):
        results = _finder(
            "$acme.csvpaths.:first():named_paths_identities()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == ["company_names", "1"]

    def test_named_paths_count(self):
        results = _finder(
            "$acme.csvpaths.:last():named_paths_count()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == 1

    def test_field_function_combined_with_all_gives_every_version(self):
        results = _finder(
            "$acme.csvpaths.:all():named_paths_count()", RICH_MANIFEST
        ).resolve()
        assert [r.data for r in results.results] == [2, 1]

    def test_group_file(self):
        results = _finder(
            "$acme.csvpaths.:first():group_file()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == GROUP_FILE_PATH

    def test_named_paths(self):
        results = _finder(
            "$acme.csvpaths.:first():named_paths()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == ["stmt text A", "stmt text B"]

    def test_archive(self):
        manifest = [
            {**RICH_MANIFEST[0], "archive_name": "archive-2026"},
        ]
        results = _finder("$acme.csvpaths.:first():archive()", manifest).resolve()
        assert results.results[0].data == "archive-2026"

    def test_group_manifest_falls_back_to_the_global_ledger(self):
        # group_manifest_3.py's KEY is empty -- the named-paths group's
        # own manifest never has this field, only the global ledger does
        # (see the shared LEDGER_KEY fallback mechanism this proves).
        ledger = [{"uuid": "v1-uuid", "paths_manifest": "named_paths/acme/manifest.json"}]
        results = _finder(
            "$acme.csvpaths.:last():group_manifest()", RICH_MANIFEST, ledger=ledger
        ).resolve()
        assert results.results[0].data == "named_paths/acme/manifest.json"

    def test_function_not_legal_here_is_rejected_not_silently_degraded(self):
        # :mark()'s own DATATYPES is FILES-only, and it has no POSITIONS
        # entry for csvpaths at all -- added 2026-08-14: this now raises
        # via ReferenceFinder3._check_position(), called from
        # _resolve_versions(), instead of silently reaching
        # _extract_data() and degrading to None on a KEY lookup with no
        # CSVPATHS entry (the old, undetected gap this test used to
        # lock in).
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:first():mark()", RICH_MANIFEST).query()

    def test_username_hostname_host_fall_back_to_the_global_ledger(self):
        # widened 2026-08-26 -- RICH_MANIFEST's own entries never have
        # username/hostname/ip_address (the Named-Paths Manifest
        # genuinely has no such fields), only the global loads ledger
        # does.
        ledger = [
            {
                "uuid": "v1-uuid",
                "username": "bot",
                "hostname": "worker-1",
                "ip_address": "10.0.0.5",
            }
        ]
        assert (
            _finder(
                "$acme.csvpaths.:last():username()", RICH_MANIFEST, ledger=ledger
            )
            .resolve()
            .results[0]
            .data
            == "bot"
        )
        assert (
            _finder(
                "$acme.csvpaths.:last():hostname()", RICH_MANIFEST, ledger=ledger
            )
            .resolve()
            .results[0]
            .data
            == "worker-1"
        )
        assert (
            _finder("$acme.csvpaths.:last():host()", RICH_MANIFEST, ledger=ledger)
            .resolve()
            .results[0]
            .data
            == "10.0.0.5"
        )

    def test_username_no_matching_ledger_entry_gives_none(self):
        ledger = [{"uuid": "some-other-uuid", "username": "bot"}]
        results = _finder(
            "$acme.csvpaths.:last():username()", RICH_MANIFEST, ledger=ledger
        ).resolve()
        assert results.results[0].data is None


class TestDefinitionFieldAccessorFunctions:
    # :scripts()/:webhooks()/:transfers()/:destinations() are
    # SOURCE="definition" -- resolved against the named-paths group's
    # definition.json config, not a manifest entry, and not affected by
    # which version a pointer happens to select.
    DEFINITION = {
        "scripts": {"on_complete_all": "notify.sh"},
        "webhooks": {"on_complete_valid": {"url": "https://example.com/hook"}},
        "transfers": {
            "path_transfers": {
                "company_names": {
                    "on_complete_all": [{"file": "data", "transfer_to": "@out"}]
                }
            }
        },
        "destinations": {"main": {"address": "example.com", "port": 22}},
    }

    def test_scripts(self):
        results = _finder(
            "$acme.csvpaths.:first():scripts()", RICH_MANIFEST, self.DEFINITION
        ).resolve()
        assert results.results[0].data == {"on_complete_all": "notify.sh"}

    def test_webhooks(self):
        # headers defaults to [], not None, so exclude_none leaves it in
        # -- an empty list is not the same as an unset field.
        results = _finder(
            "$acme.csvpaths.:first():webhooks()", RICH_MANIFEST, self.DEFINITION
        ).resolve()
        assert results.results[0].data == {
            "on_complete_valid": {"url": "https://example.com/hook", "headers": []}
        }

    def test_transfers_reads_the_nested_path_transfers_key(self):
        results = _finder(
            "$acme.csvpaths.:first():transfers()", RICH_MANIFEST, self.DEFINITION
        ).resolve()
        assert results.results[0].data == {
            "company_names": {
                "on_complete_all": [{"file": "data", "transfer_to": "@out"}]
            }
        }

    def test_destinations(self):
        results = _finder(
            "$acme.csvpaths.:last():destinations()", RICH_MANIFEST, self.DEFINITION
        ).resolve()
        assert results.results[0].data == {"main": {"address": "example.com", "port": 22}}

    def test_never_configured_gives_none_not_an_error(self):
        results = _finder(
            "$acme.csvpaths.:first():scripts()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data is None

    def test_same_value_regardless_of_which_version_is_selected(self):
        first = _finder(
            "$acme.csvpaths.:first():scripts()", RICH_MANIFEST, self.DEFINITION
        ).resolve()
        last = _finder(
            "$acme.csvpaths.:last():scripts()", RICH_MANIFEST, self.DEFINITION
        ).resolve()
        assert first.results[0].data == last.results[0].data


class TestDefinitionSubFieldAccessorFunctions:
    # the arg-keyed (destinations.<name>.*, transfers.<name>.
    # on_complete_*) and fixed-state (scripts.on_complete_*, webhooks.
    # on_complete_*) sub-field accessors built 2026-08-26 -- see
    # ReferenceFinder3._apply_key_arg()'s own docstring for the shared
    # "{}"-placeholder mechanism the arg-keyed ones need.
    DEFINITION = {
        "scripts": {
            "on_complete_all": "notify.sh",
            "on_complete_error": "alert.sh",
        },
        "webhooks": {
            "on_complete_valid": {"url": "https://example.com/hook"},
        },
        "transfers": {
            "path_transfers": {
                "company_names": {
                    "on_complete_all": [{"file": "data", "transfer_to": "@out"}]
                }
            }
        },
        "destinations": {
            "main": {
                "address": "example.com",
                "port": 22,
                "username": "bot",
                "password": "secret",
            }
        },
    }

    def test_script_on_complete_all(self):
        results = _finder(
            "$acme.csvpaths.:first():script_on_complete_all()",
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert results.results[0].data == "notify.sh"

    def test_script_on_complete_error(self):
        results = _finder(
            "$acme.csvpaths.:first():script_on_complete_error()",
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert results.results[0].data == "alert.sh"

    def test_script_on_complete_valid_not_configured_gives_none(self):
        results = _finder(
            "$acme.csvpaths.:first():script_on_complete_valid()",
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert results.results[0].data is None

    def test_webhooks_on_complete_valid(self):
        results = _finder(
            "$acme.csvpaths.:first():webhooks_on_complete_valid()",
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert results.results[0].data == {
            "url": "https://example.com/hook",
            "headers": [],
        }

    def test_destination_address_by_name(self):
        results = _finder(
            '$acme.csvpaths.:first():destination_address("main")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert results.results[0].data == "example.com"

    def test_destination_port_by_name(self):
        results = _finder(
            '$acme.csvpaths.:first():destination_port("main")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert results.results[0].data == 22

    def test_destination_username_by_name(self):
        results = _finder(
            '$acme.csvpaths.:first():destination_username("main")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert results.results[0].data == "bot"

    def test_destination_password_by_name(self):
        results = _finder(
            '$acme.csvpaths.:first():destination_password("main")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert results.results[0].data == "secret"

    def test_destination_unknown_name_gives_none_not_an_error(self):
        results = _finder(
            '$acme.csvpaths.:first():destination_address("nope")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert results.results[0].data is None

    def test_transfer_on_complete_all_by_identity(self):
        results = _finder(
            '$acme.csvpaths.:first():transfer_on_complete_all("company_names")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert results.results[0].data == [
            {"file": "data", "transfer_to": "@out"}
        ]

    def test_transfer_on_complete_unknown_identity_gives_none(self):
        results = _finder(
            '$acme.csvpaths.:first():transfer_on_complete_all("nope")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert results.results[0].data is None


class TestTemplateBareVsPointerDualSource:
    # :template() (built 2026-08-26) is the first field accessor using
    # Function3.BARE_SOURCE -- bare (no pointer at all) reads
    # definition.json's current default; alongside a real pointer, it
    # reads that specific matched version's own manifest snapshot
    # instead. See ReferenceFinder3._pointer_present()/Template3's own
    # docstring for the full design.
    MANIFEST = [
        {**RICH_MANIFEST[0], "template": "snapshot-v0"},
        {**RICH_MANIFEST[1], "template": "snapshot-v1"},
    ]
    DEFINITION = {"template": "current-default"}

    def test_bare_reads_the_current_definition_default(self):
        results = _finder(
            "$acme.csvpaths.:template()", self.MANIFEST, self.DEFINITION
        ).resolve()
        # no pointer -- pools every version, each reading the SAME
        # current default (definition.json is not versioned).
        assert [r.data for r in results.results] == [
            "current-default",
            "current-default",
        ]

    def test_first_reads_that_versions_own_manifest_snapshot(self):
        results = _finder(
            "$acme.csvpaths.:first():template()", self.MANIFEST, self.DEFINITION
        ).resolve()
        assert results.results[0].data == "snapshot-v0"

    def test_last_reads_that_versions_own_manifest_snapshot(self):
        results = _finder(
            "$acme.csvpaths.:last():template()", self.MANIFEST, self.DEFINITION
        ).resolve()
        assert results.results[0].data == "snapshot-v1"

    def test_bare_never_configured_gives_none_not_an_error(self):
        results = _finder(
            "$acme.csvpaths.:template()", self.MANIFEST
        ).resolve()
        assert [r.data for r in results.results] == [None, None]


class TestScopeLimits:
    def test_star_root_major_not_yet_supported(self):
        finder = _finder("$*.csvpaths.:last().x")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_name_two_worksheet_marker_not_yet_supported(self):
        finder = _finder("$acme.csvpaths.:last()#sheet1.x")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_literal_path_in_name_one_not_supported(self):
        finder = _finder("$acme.csvpaths.somefile.x")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_star_in_name_one_not_supported(self):
        finder = _finder("$acme.csvpaths.*.x")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_two_pointers_in_name_one_raises(self):
        finder = _finder("$acme.csvpaths.:first():last()")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_function_chain_on_name_three_not_yet_supported(self):
        finder = _finder("$acme.csvpaths.:last().company_names:data()")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_star_body_on_name_three_not_supported(self):
        finder = _finder("$acme.csvpaths.:last().*")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_metadata_kind_not_yet_supported(self):
        # :meta() matches resolve_kind's METADATA_FILE placeholder list
        # (Reference3._METADATA_FILE_FUNCTIONS) even though it is not
        # an actual registered function -- query() would already reject
        # this reference for a different reason first (functions on
        # name_three are rejected outright), so _extract_data() is
        # called directly to test its own resolve_kind branching in
        # isolation, ahead of any real metadata-access function
        # existing for csvpaths.
        finder = _finder("$acme.csvpaths.:first().:meta()")
        with pytest.raises(ReferenceException3):
            finder._extract_data(ReferenceResult3(path="p", uuid="v0-uuid"))


class TestPositionEnforcement:
    # ReferenceFinder3._check_position() -- added 2026-08-14, the
    # enforced replacement for the scattered "is this recognized"
    # guards each Finder used to hand-write on its own. CSVPATHS is the
    # first Finder retrofitted to call it.
    def test_name_is_registered_for_csvpaths_but_has_nowhere_legal_to_go(self):
        # the actual bug this mechanism was built to close: :name()'s
        # own DATATYPES includes csvpaths (it type-checks fine as an
        # argument-typed function), but it has no path-building
        # dimension there -- POSITIONS[csvpaths] is an explicit empty
        # tuple, not an absent key, so this now raises instead of
        # silently no-opping the way it used to.
        with pytest.raises(ReferenceException3):
            _finder('$acme.csvpaths.:name("x")').query()

    def test_a_function_not_declared_for_csvpaths_at_all_is_rejected(self):
        # :mark() is FILES-only in its own DATATYPES and has no
        # POSITIONS entry for csvpaths at all -- same rejection path,
        # different starting point (never declared vs. declared-empty).
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:first():mark()", RICH_MANIFEST).query()

    def test_a_legal_function_is_unaffected(self):
        # sanity check that the new check does not over-reject --
        # :having() legitimately declares name_one for csvpaths.
        results = _finder(
            '$acme.csvpaths.:having("company_names"):last()', RICH_MANIFEST
        ).query()
        assert results.uuids == ["v0-uuid"]

    def test_having_is_not_legal_at_name_three(self):
        # :having() only declares name_one -- riding on name_three
        # (where it has never been meaningful) is rejected the same way.
        with pytest.raises(ReferenceException3):
            _finder('$acme.csvpaths.:last().:having("x")', RICH_MANIFEST).query()


class TestLog:
    # compendium 5.16(b) -- an outlier: a single, global, datatype-
    # independent resource (config.ini's own log_file), not tied to any
    # named-paths group at all. Built and shared identically across all
    # three finders (ReferenceFinder3._bare_log_call()/_query_log_call()/
    # _read_log_file()) -- this class exercises the full scenario set
    # once here (csvpaths needs no real fixture beyond a log file path,
    # simplest of the three datatypes to set up); see
    # test_files_reference_finder_3.py/test_results_reference_finder_3.py
    # for one confirming end-to-end test each, proving the shared
    # mechanism composes correctly with each datatype's own query()
    # dispatch too, not just in isolation.
    def test_bare_log_resolves_the_whole_file(self, tmp_path):
        log_path = tmp_path / "csvpath.log"
        log_path.write_text("line1\nline2\nline3\n")
        results = _finder("$*.csvpaths.:log()", log_file=str(log_path)).resolve()
        assert results.results[0].data == "line1\nline2\nline3\n"

    def test_log_with_int_arg_gives_last_n_lines(self, tmp_path):
        log_path = tmp_path / "csvpath.log"
        log_path.write_text("\n".join(f"line{i}" for i in range(1, 21)) + "\n")
        results = _finder("$*.csvpaths.:log(3)", log_file=str(log_path)).resolve()
        assert results.results[0].data == "line18\nline19\nline20"

    def test_log_resolves_none_when_file_does_not_exist_yet(self, tmp_path):
        log_path = tmp_path / "does-not-exist.log"
        results = _finder("$*.csvpaths.:log()", log_file=str(log_path)).resolve()
        assert results.results[0].data is None

    def test_log_combined_with_a_pointer_is_rejected(self):
        # "standalone, not-combinable" -- riding alongside anything else
        # in name_one is illegal, even a plain pointer.
        with pytest.raises(ReferenceException3):
            _finder("$*.csvpaths.:log():last()", log_file="x.log").query()

    def test_log_with_literal_root_major_is_rejected(self):
        # root_major must be '*' -- a literal named-paths group name is
        # misleading here (there is no acme-specific log content).
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:log()", log_file="x.log").query()
