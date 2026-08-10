import pytest

from csvpath.references.csvpaths_reference_finder_3 import CsvpathsReferenceFinder3
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
    def __init__(self, definition: dict):
        self._definition = definition

    def get_config(self, name):
        from csvpath.managers.paths.paths_descriptor import GroupConfig

        return GroupConfig(**self._definition)


class _FakePathsManager:
    def __init__(
        self,
        manifest,
        home=GROUP_HOME,
        definition: dict | None = None,
        ledger=None,
        by_name: dict | None = None,
    ):
        self._manifest = manifest
        self._home = home
        self._definition = definition or {}
        self._ledger = manifest if ledger is None else ledger
        # by_name: {name: manifest} -- only used by '*' traversal tests,
        # which need more than one distinct named-paths group. Every
        # other test uses the single manifest above.
        self._by_name = by_name

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
        return _FakePathsDescriber(self._definition)


class _FakeConfig:
    def __init__(self, inputs_csvpaths_path: str | None = None):
        self.inputs_csvpaths_path = inputs_csvpaths_path


class _FakeCsvPaths:
    def __init__(self, paths_manager, inputs_csvpaths_path: str | None = None):
        self.paths_manager = paths_manager
        self.config = _FakeConfig(inputs_csvpaths_path)


def _finder(
    reference: str,
    manifest: list = ACME_MANIFEST,
    definition: dict | None = None,
    inputs_csvpaths_path: str | None = None,
    ledger: list | None = None,
    by_name: dict | None = None,
) -> CsvpathsReferenceFinder3:
    csvpaths = _FakeCsvPaths(
        _FakePathsManager(manifest, definition=definition, ledger=ledger, by_name=by_name),
        inputs_csvpaths_path=inputs_csvpaths_path,
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
        # version, regardless of which statement within it).
        with_three = _finder("$acme.csvpaths.:first().company_names").query()
        without_three = _finder("$acme.csvpaths.:first()").query()
        assert with_three.results == without_three.results


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
        # 2026-08-07), so this is illegal now, not "every version,
        # unreduced" as it used to be -- a pointer is required to pick
        # one version.
        finder = _finder("$acme.csvpaths.:all():manifest()")
        with pytest.raises(ReferenceException3):
            finder.query()

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
    return _finder(reference, by_name=STAR_BY_NAME)


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

    def test_combining_with_manifest_is_not_yet_supported(self):
        # note: a plain pointer + :manifest() (e.g. ":last():manifest()")
        # is intercepted earlier by Rule 1b (the global-ledger ordinal
        # case, same structural shape) before ever reaching traversal --
        # :all():manifest() is not a pointer-first shape, so it reaches
        # _query_star_traversal's own combining-guard instead.
        with pytest.raises(ReferenceException3):
            _star_finder("$*.csvpaths.:all():manifest()").query()

    def test_name_three_combined_with_traversal_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _star_finder("$*.csvpaths.:last().0").query()


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

    def test_function_with_no_key_for_this_datatype_gives_none_not_a_crash(self):
        # :mark()'s own DATATYPES is FILES-only, but nothing currently
        # enforces DATATYPES against the reference it is actually used
        # in (a pre-existing gap, not introduced here) -- so this reaches
        # _extract_data() and must degrade to None rather than crashing
        # on a KEY lookup that has no CSVPATHS entry.
        results = _finder("$acme.csvpaths.:first():mark()", RICH_MANIFEST).resolve()
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


class TestPathFunction:
    # :path(inner) returns the filesystem path to whatever well-known
    # resource `inner` points at, instead of its content.
    def test_path_wrapping_manifest(self):
        results = _finder("$acme.csvpaths.:first():path(:manifest())").resolve()
        assert results.results[0].data == f"{GROUP_HOME}/manifest.json"

    def test_path_wrapping_definition(self):
        results = _finder("$acme.csvpaths.:first():path(:definition())").resolve()
        assert results.results[0].data == f"{GROUP_HOME}/definition.json"

    def test_path_alone_with_no_pointer_gives_every_version(self):
        results = _finder("$acme.csvpaths.:path(:manifest())").resolve()
        assert [r.data for r in results.results] == [
            f"{GROUP_HOME}/manifest.json",
            f"{GROUP_HOME}/manifest.json",
        ]

    def test_path_wrapping_a_field_accessor_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:first():path(:uuid())").resolve()


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
