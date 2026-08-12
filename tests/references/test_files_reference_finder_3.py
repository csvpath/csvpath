import pytest

from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.reference_results_3 import ReferenceResult3


#
# fixture modeled directly on the spec's own EXAMPLE SCENARIO in
# "creating references v3.txt": named-file alpha has two distinct files
# (zero.csv, one.csv), one.csv has two versions, listed in arrival
# order. real file_home values always include the source filename's
# extension (confirmed against a real manifest.json), which is exactly
# why literal PATH_SEGMENT can't reach them and :name("...") exists.
#
ALPHA_HOME = "inputs/named_files/alpha"
ALPHA_MANIFEST = [
    {
        "file": "inputs/named_files/alpha/zero.csv/0000000000000000.csv",
        "file_home": "inputs/named_files/alpha/zero.csv",
        "uuid": "u-zero-1",
    },
    {
        "file": "inputs/named_files/alpha/one.csv/1111111111abcdef.csv",
        "file_home": "inputs/named_files/alpha/one.csv",
        "uuid": "u-one-1",
    },
    {
        "file": "inputs/named_files/alpha/one.csv/0000000000abcdef.csv",
        "file_home": "inputs/named_files/alpha/one.csv",
        "uuid": "u-one-2",
    },
]

TEMPLATED_HOME = "inputs/named_files/acme"
TEMPLATED_MANIFEST = [
    {
        "file": "inputs/named_files/acme/Q2/test-data/aaaa.csv",
        "file_home": "inputs/named_files/acme/Q2/test-data",
        "uuid": "u-q2-1",
    },
]

# for TestAllForOneNamedFile -- one named-file (mixed) with two distinct
# file_homes at DIFFERENT depths (one segment, two segments) under the
# same home, each with more than one version. A literal/'*' pattern
# always requires an exact segment count, so nothing before this could
# reach both at once -- exactly the gap bare ':all()' fills for a single
# named-file (settled 2026-08-12).
MIXED_HOME = "inputs/named_files/mixed"
MIXED_MANIFEST = [
    {
        "file": "inputs/named_files/mixed/zero.csv/aaa.csv",
        "file_home": "inputs/named_files/mixed/zero.csv",
        "uuid": "u-zero-1",
    },
    {
        "file": "inputs/named_files/mixed/zero.csv/bbb.csv",
        "file_home": "inputs/named_files/mixed/zero.csv",
        "uuid": "u-zero-2",
    },
    {
        "file": "inputs/named_files/mixed/nested/deep.csv/ccc.csv",
        "file_home": "inputs/named_files/mixed/nested/deep.csv",
        "uuid": "u-deep-1",
    },
    {
        "file": "inputs/named_files/mixed/nested/deep.csv/ddd.csv",
        "file_home": "inputs/named_files/mixed/nested/deep.csv",
        "uuid": "u-deep-2",
    },
]


class _FakeFileDescriber:
    def __init__(self, definition: dict):
        self._definition = definition

    def get_config(self, name):
        from csvpath.managers.files.file_descriptor import Config

        return Config(**self._definition)


class _FakeFileManager:
    def __init__(
        self,
        home,
        manifest,
        definition: dict | None = None,
        ledger=None,
        by_name: dict | None = None,
    ):
        self._home = home
        self._manifest = manifest
        self._definition = definition or {}
        self._ledger = manifest if ledger is None else ledger
        # by_name: {name: (home, manifest)} -- only used by '*' traversal
        # tests, which need more than one distinct named-file. Every
        # other test uses the single (home, manifest) pair above.
        self._by_name = by_name

    def named_file_home(self, name):
        if self._by_name is not None:
            return self._by_name[name][0]
        return self._home

    def get_manifest(self, name):
        if self._by_name is not None:
            return self._by_name[name][1]
        return self._manifest

    @property
    def named_file_names(self):
        if self._by_name is not None:
            return list(self._by_name.keys())
        return []

    @property
    def files_root_manifest(self):
        return self._ledger

    @property
    def describer(self):
        return _FakeFileDescriber(self._definition)


class _FakeConfig:
    def __init__(self, inputs_files_path: str | None = None):
        self.inputs_files_path = inputs_files_path


class _FakeCsvPaths:
    def __init__(self, file_manager, inputs_files_path: str | None = None):
        self.file_manager = file_manager
        self.config = _FakeConfig(inputs_files_path)


def _finder(
    reference: str,
    home: str,
    manifest: list,
    definition: dict | None = None,
    inputs_files_path: str | None = None,
    ledger: list | None = None,
    by_name: dict | None = None,
) -> FilesReferenceFinder3:
    csvpaths = _FakeCsvPaths(
        _FakeFileManager(home, manifest, definition, ledger=ledger, by_name=by_name),
        inputs_files_path=inputs_files_path,
    )
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return FilesReferenceFinder3(csvpaths=csvpaths, ref=ref)


class TestStarFlattensAcrossAllFiles:
    # matches "creating references v3.txt"'s EXAMPLE SCENARIO exactly.
    def test_last_across_everything_under_alpha(self):
        finder = _finder("$alpha.files.*.:last()", ALPHA_HOME, ALPHA_MANIFEST)
        results = finder.query()
        assert results.files == [
            "inputs/named_files/alpha/one.csv/0000000000abcdef.csv"
        ]

    def test_all_functions_flatten_to_last_manifest_entry(self):
        # :all() isn't built yet, but bare "*" already exercises the
        # same flattening behavior the spec describes for it.
        finder = _finder("$alpha.files.*.:first()", ALPHA_HOME, ALPHA_MANIFEST)
        results = finder.query()
        assert results.files == [
            "inputs/named_files/alpha/zero.csv/0000000000000000.csv"
        ]


class TestNameFunctionAsPathSegment:
    def test_name_selects_one_logical_file(self):
        finder = _finder(
            '$alpha.files.:name("zero.csv").:first()', ALPHA_HOME, ALPHA_MANIFEST
        )
        assert finder.query().files == [
            "inputs/named_files/alpha/zero.csv/0000000000000000.csv"
        ]

    def test_name_with_index(self):
        finder = _finder(
            '$alpha.files.:name("one.csv").:index(0)', ALPHA_HOME, ALPHA_MANIFEST
        )
        assert finder.query().files == [
            "inputs/named_files/alpha/one.csv/1111111111abcdef.csv"
        ]

    def test_name_with_negative_index(self):
        finder = _finder(
            '$alpha.files.:name("one.csv").:index(-1)', ALPHA_HOME, ALPHA_MANIFEST
        )
        assert finder.query().files == [
            "inputs/named_files/alpha/one.csv/0000000000abcdef.csv"
        ]

    def test_name_matching_nothing_returns_empty(self):
        finder = _finder(
            '$alpha.files.:name("nope.csv").:first()', ALPHA_HOME, ALPHA_MANIFEST
        )
        assert finder.query().files == []


class TestLiteralMultiSegmentPath:
    def test_extensionless_template_path_matches(self):
        finder = _finder(
            "$acme.files.Q2/test-data.:first()", TEMPLATED_HOME, TEMPLATED_MANIFEST
        )
        assert finder.query().files == [
            "inputs/named_files/acme/Q2/test-data/aaaa.csv"
        ]

    def test_wrong_segment_count_does_not_match(self):
        finder = _finder(
            "$acme.files.Q2.:first()", TEMPLATED_HOME, TEMPLATED_MANIFEST
        )
        assert finder.query().files == []

    def test_star_in_a_multi_segment_path(self):
        finder = _finder(
            "$acme.files.*/test-data.:first()", TEMPLATED_HOME, TEMPLATED_MANIFEST
        )
        assert finder.query().files == [
            "inputs/named_files/acme/Q2/test-data/aaaa.csv"
        ]


class TestIndexOutOfRange:
    def test_out_of_range_index_returns_empty_not_an_error(self):
        finder = _finder("$alpha.files.*.:index(99)", ALPHA_HOME, ALPHA_MANIFEST)
        assert finder.query().files == []


class TestNameThreeAbsent:
    # name_three is optional now: name_one alone is a prefix search that
    # returns zero or more paths to file-home directories -- one per
    # distinct file matched, deduplicated across versions, each with
    # uuid=None (a directory isn't a specific registered version, so it
    # has no uuid of its own). A bare, unqualified "*" with nothing else
    # is NOT one of these cases -- see
    # test_star_alone_is_rejected_before_the_finder_even_runs below --
    # Reference3.check_valid() rejects it at construction, before the
    # finder ever gets a chance to query().
    def test_star_alone_is_rejected_before_the_finder_even_runs(self):
        with pytest.raises(ReferenceException3):
            _finder("$alpha.files.*", ALPHA_HOME, ALPHA_MANIFEST)

    def test_name_one_alone_narrowed_by_name_function(self):
        finder = _finder('$alpha.files.:name("one.csv")', ALPHA_HOME, ALPHA_MANIFEST)
        results = finder.query()
        assert results.files == ["inputs/named_files/alpha/one.csv"]
        assert results.results[0].uuid is None

    def test_resolving_a_name_one_terminal_result_gives_none(self):
        # "no default" per "creating references v3.txt"'s "Resolve
        # terminating at name_one, with no pointer" rule -- a directory
        # has no single unambiguous first-party payload.
        finder = _finder('$alpha.files.:name("one.csv")', ALPHA_HOME, ALPHA_MANIFEST)
        results = finder.resolve()
        assert results.results[0].data is None


class TestScopeLimits:
    def test_star_root_major_with_no_named_files_gives_empty_results(self):
        # '*' traversal is supported now (see TestStarTraversal below) --
        # with zero named-files to enumerate (no by_name given here), it
        # correctly finds nothing rather than raising.
        finder = _finder("$*.files.*.:last()", ALPHA_HOME, ALPHA_MANIFEST)
        assert finder.query().results == []

    def test_name_two_worksheet_marker_not_yet_supported(self):
        finder = _finder(
            '$alpha.files.*#sheet1.:last()', ALPHA_HOME, ALPHA_MANIFEST
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_functions_directly_on_name_one_not_yet_supported(self):
        finder = _finder("$alpha.files.*:last().v1", ALPHA_HOME, ALPHA_MANIFEST)
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_unsupported_function_valued_path_segment(self):
        finder = _finder(
            "$acme.files.:quarter()/x.:first()", TEMPLATED_HOME, TEMPLATED_MANIFEST
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_literal_name_three_body_not_yet_supported(self):
        finder = _finder("$alpha.files.*.v1", ALPHA_HOME, ALPHA_MANIFEST)
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_two_pointers_in_name_three_raises(self):
        finder = _finder(
            "$alpha.files.*.:first():last()", ALPHA_HOME, ALPHA_MANIFEST
        )
        with pytest.raises(ReferenceException3):
            finder.query()


class TestManifestFunction:
    # ":manifest()" is a name_one-terminal, bare/sole-content shape --
    # it bypasses the "which file" pattern-matching pipeline entirely
    # and points at the named-file's own manifest.json instead (one
    # fixed resource per named-file, not scoped to any particular file/
    # version).
    def test_query_returns_the_manifest_path_with_no_uuid(self):
        finder = _finder("$alpha.files.:manifest()", ALPHA_HOME, ALPHA_MANIFEST)
        results = finder.query()
        assert results.files == [f"{ALPHA_HOME}/manifest.json"]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_manifest_files_raw_bytes(self, tmp_path):
        content = b'[{"file_home": "zero.csv"}]'
        home = tmp_path / "alpha"
        home.mkdir()
        (home / "manifest.json").write_bytes(content)
        finder = _finder("$alpha.files.:manifest()", str(home), ALPHA_MANIFEST)
        results = finder.resolve()
        assert results.results[0].data == content

    def test_manifest_with_extra_path_narrowing_is_not_yet_supported(self):
        # :manifest() must be name_one's entire content -- combining it
        # with real path narrowing falls through to the ordinary
        # "which file" pipeline, which does not recognize it as a
        # function-valued path segment.
        finder = _finder("$alpha.files.a/:manifest()", ALPHA_HOME, ALPHA_MANIFEST)
        with pytest.raises(ReferenceException3):
            finder.query()


class TestGlobalArrivalsLedger:
    # Rule 1a: "*" at root_major combined with a bare :manifest() is the
    # one exception to root_major=="*" being unsupported -- it resolves
    # to the Named-File Arrivals Manifest, a single global ledger at the
    # named-files root tracking every arrival across every named-file.
    def test_query_returns_the_global_ledger_path_with_no_uuid(self):
        finder = _finder(
            "$*.files.:manifest()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
        )
        results = finder.query()
        assert results.files == ["inputs/named_files/manifest.json"]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_global_ledgers_raw_bytes(self, tmp_path):
        content = b'[{"named_file_name": "alpha"}, {"named_file_name": "beta"}]'
        root = tmp_path / "named_files"
        root.mkdir()
        (root / "manifest.json").write_bytes(content)
        finder = _finder(
            "$*.files.:manifest()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path=str(root),
        )
        results = finder.resolve()
        assert results.results[0].data == content

    def test_star_with_definition_is_still_not_supported(self):
        # :definition() has no equivalent global resource anywhere in
        # the codebase -- stays unsupported at "*" root_major.
        finder = _finder(
            "$*.files.:definition()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
        )
        with pytest.raises(ReferenceException3):
            finder.query()

LEDGER = [
    {"named_file_name": "alpha", "uuid": "u-ledger-1"},
    {"named_file_name": "beta", "uuid": "u-ledger-2"},
    {"named_file_name": "gamma", "uuid": "u-ledger-3"},
]


class TestGlobalArrivalsLedgerOrdinalIndexing:
    # Rule 1b: a pointer (:first()/:last()/:index(n)) riding before the
    # bare :manifest() selects one entry out of the ledger by ordinal
    # position, instead of dumping the whole thing.
    def test_last_gives_the_most_recent_arrival(self):
        finder = _finder(
            "$*.files.:last():manifest()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=LEDGER,
        )
        results = finder.resolve()
        assert results.results[0].data == LEDGER[-1]

    def test_first_gives_the_earliest_arrival(self):
        finder = _finder(
            "$*.files.:first():manifest()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=LEDGER,
        )
        results = finder.resolve()
        assert results.results[0].data == LEDGER[0]

    def test_index_gives_the_nth_arrival(self):
        finder = _finder(
            "$*.files.:index(1):manifest()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=LEDGER,
        )
        results = finder.resolve()
        assert results.results[0].data == LEDGER[1]

    def test_negative_index_counts_from_the_end(self):
        finder = _finder(
            "$*.files.:index(-1):manifest()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=LEDGER,
        )
        results = finder.resolve()
        assert results.results[0].data == LEDGER[-1]

    def test_out_of_range_index_gives_no_results(self):
        finder = _finder(
            "$*.files.:index(99):manifest()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=LEDGER,
        )
        results = finder.query()
        assert len(results.results) == 0

    def test_query_gives_the_ledger_path_with_the_entrys_own_uuid(self):
        finder = _finder(
            "$*.files.:last():manifest()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=LEDGER,
        )
        results = finder.query()
        assert results.files == ["inputs/named_files/manifest.json"]
        assert results.results[0].uuid == "u-ledger-3"

    def test_manifest_then_pointer_order_also_works(self):
        # ":manifest():last()" means the same as ":last():manifest()" --
        # order-insensitivity was missing on _pointer_before_manifest
        # and fixed 2026-08-10.
        finder = _finder(
            "$*.files.:manifest():last()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=LEDGER,
        )
        results = finder.query()
        assert results.results[0].uuid == "u-ledger-3"


#
# matches the spec compendium's own EXAMPLE SCENARIO exactly ("Why a
# trailing bare '*' is illegal but bare ':all()' is fine"): named-file
# alpha (zero.csv x1 version, one.csv x2 versions), named-file beta
# (two.csv x2 versions). beta is listed FIRST here on purpose -- naive
# concatenation with no time-sort would put alpha's own entries last in
# the pooled list, so a test asserting beta's true-latest entry wins
# would fail if the flatten case's time-sort were ever removed/broken.
#
STAR_ALPHA_HOME = "inputs/named_files/alpha"
STAR_ALPHA_MANIFEST = [
    {
        "file": "inputs/named_files/alpha/zero.csv/aaa.csv",
        "file_home": "inputs/named_files/alpha/zero.csv",
        "uuid": "u-zero-1",
        "time": "2026-01-01T00:00:00+00:00",
    },
    {
        "file": "inputs/named_files/alpha/one.csv/bbb.csv",
        "file_home": "inputs/named_files/alpha/one.csv",
        "uuid": "u-one-1",
        "time": "2026-01-02T00:00:00+00:00",
    },
    {
        "file": "inputs/named_files/alpha/one.csv/ccc.csv",
        "file_home": "inputs/named_files/alpha/one.csv",
        "uuid": "u-one-2",
        "time": "2026-01-03T00:00:00+00:00",
    },
]
STAR_BETA_HOME = "inputs/named_files/beta"
STAR_BETA_MANIFEST = [
    {
        "file": "inputs/named_files/beta/two.csv/ddd.csv",
        "file_home": "inputs/named_files/beta/two.csv",
        "uuid": "u-two-1",
        "time": "2026-01-04T00:00:00+00:00",
    },
    {
        "file": "inputs/named_files/beta/two.csv/eee.csv",
        "file_home": "inputs/named_files/beta/two.csv",
        "uuid": "u-two-2",
        "time": "2026-01-05T00:00:00+00:00",
    },
]
STAR_BY_NAME = {
    "beta": (STAR_BETA_HOME, STAR_BETA_MANIFEST),
    "alpha": (STAR_ALPHA_HOME, STAR_ALPHA_MANIFEST),
}


def _star_finder(reference: str) -> FilesReferenceFinder3:
    return _finder(reference, STAR_ALPHA_HOME, STAR_ALPHA_MANIFEST, by_name=STAR_BY_NAME)


class TestStarTraversalFlatten:
    # bare '*'/path narrowing pools every named-file's matches into one
    # combined list, sorted by true chronological order (each entry's
    # own "time"), reduced by one terminal pointer.
    def test_last_across_every_named_file_is_the_true_most_recent(self):
        # beta's two.csv v2 (2026-01-05) is the global most-recent, not
        # alpha's own last entry (2026-01-03) -- proves pooling crosses
        # named-files and is truly time-sorted, not just concatenated.
        results = _star_finder("$*.files.*.:last()").query()
        assert results.uuids == ["u-two-2"]

    def test_first_across_every_named_file_is_the_true_earliest(self):
        results = _star_finder("$*.files.*.:first()").query()
        assert results.uuids == ["u-zero-1"]

    def test_index_selects_by_chronological_position(self):
        # chronological order: zero-1, one-1, one-2, two-1, two-2
        results = _star_finder("$*.files.*.:index(2)").query()
        assert results.uuids == ["u-one-2"]

    # Note: a bare, trailing "*" with no name_three (e.g. "$*.files.*")
    # is illegal grammar -- same rule that already rejects "$alpha.
    # files.*" alone (Reference3.check_valid()). The "no name_three"
    # dedupe path is exercised via ':all()' instead, see
    # TestStarTraversalGroup below.

    def test_combining_with_manifest_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _star_finder("$*.files.*.:last():manifest()").query()

    def test_combining_with_a_field_accessor_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _star_finder("$*.files.*.:last():uuid()").query()

    def test_functions_directly_on_name_one_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _star_finder("$*.files.*:last().v1").query()


class TestStarTraversalGroup:
    # bare ':all()' as name_one's entire content partitions every
    # named-file's EXACTLY-one-level matches (corrected 2026-08-12 to
    # require the same [Star3()] pattern '*' does -- an earlier version
    # matched any depth, which diverged from ResultsReferenceFinder3's
    # own ':all()'/'*' depth-peer vocabulary) by file_home (already
    # unique per named-file+path), applying the terminal pointer
    # independently within each group -- one result per (named-file,
    # path) pair. STAR_ALPHA/STAR_BETA are already all one level deep,
    # so these assertions are unaffected by the correction -- see
    # TestStarTraversalFlattenAnyDepth below for the any-depth case.
    def test_all_with_last_gives_one_result_per_named_file_and_path(self):
        results = _star_finder("$*.files.:all().:last()").query()
        assert len(results.results) == 3
        assert set(results.uuids) == {"u-zero-1", "u-one-2", "u-two-2"}

    def test_all_with_first_gives_each_groups_earliest_version(self):
        results = _star_finder("$*.files.:all().:first()").query()
        assert len(results.results) == 3
        assert set(results.uuids) == {"u-zero-1", "u-one-1", "u-two-1"}

    def test_all_with_no_name_three_dedupes_to_file_home_directories(self):
        results = _star_finder("$*.files.:all()").query()
        assert set(results.files) == {
            "inputs/named_files/alpha/zero.csv",
            "inputs/named_files/alpha/one.csv",
            "inputs/named_files/beta/two.csv",
        }

    def test_all_combined_with_manifest_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _star_finder("$*.files.:all().:last():manifest()").query()


#
# adds one named-file ("gamma") with a TWO-level entry, chronologically
# latest of everything, to STAR_ALPHA/STAR_BETA's existing one-level
# fixtures -- '*'/':all()' (both restricted to exactly one level) never
# see it; ':flatten()' (any depth, pooled across every named-file) does.
#
FLATTEN_GAMMA_HOME = "inputs/named_files/gamma"
FLATTEN_GAMMA_MANIFEST = [
    {
        "file": "inputs/named_files/gamma/nested/deep.csv/fff.csv",
        "file_home": "inputs/named_files/gamma/nested/deep.csv",
        "uuid": "u-gamma-deep-1",
        "time": "2026-01-06T00:00:00+00:00",
    },
]
FLATTEN_BY_NAME = dict(STAR_BY_NAME, gamma=(FLATTEN_GAMMA_HOME, FLATTEN_GAMMA_MANIFEST))


def _flatten_star_finder(reference: str) -> FilesReferenceFinder3:
    csvpaths = _FakeCsvPaths(_FakeFileManager(None, None, by_name=FLATTEN_BY_NAME))
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return FilesReferenceFinder3(csvpaths=csvpaths, ref=ref)


class TestStarTraversalFlattenAnyDepth:
    # bare ':flatten()' as name_one's entire content -- added 2026-08-12,
    # the any-depth POOL peer of '*' (one-level POOL)/':all()' (one-level
    # GROUP) across every named-file, mirroring ResultsReferenceFinder3's
    # own ':flatten()'. Pools every named-file's candidates at any depth
    # into one combined list, time-sorted, same as '*' traversal's own
    # pool branch -- just without the exact-one-level restriction.
    def test_last_reaches_a_two_level_entry_star_cannot(self):
        star_results = _flatten_star_finder("$*.files.*.:last()").query()
        assert star_results.uuids == ["u-two-2"]
        flatten_results = _flatten_star_finder("$*.files.:flatten().:last()").query()
        assert flatten_results.uuids == ["u-gamma-deep-1"]

    def test_first_across_every_named_file_and_depth(self):
        results = _flatten_star_finder("$*.files.:flatten().:first()").query()
        assert results.uuids == ["u-zero-1"]

    def test_with_no_name_three_dedupes_to_file_home_directories_any_depth(self):
        results = _flatten_star_finder("$*.files.:flatten()").query()
        assert set(results.files) == {
            "inputs/named_files/alpha/zero.csv",
            "inputs/named_files/alpha/one.csv",
            "inputs/named_files/beta/two.csv",
            "inputs/named_files/gamma/nested/deep.csv",
        }

    def test_combining_with_manifest_is_not_yet_supported(self):
        # same structural reason '*' traversal has this restriction --
        # root_major is "*" here, so _extract_data() cannot know which
        # named-file's manifest to re-read.
        with pytest.raises(ReferenceException3):
            _flatten_star_finder("$*.files.:flatten().:last():manifest()").query()


class TestAllForOneNamedFile:
    # bare ':all()' as name_one's entire content, for a LITERAL (non-'*')
    # root_major -- settled 2026-08-12, CORRECTED same day: ':all()' is
    # a one-level GROUP, an exact peer of '*' (same [Star3()] pattern),
    # not an any-depth match -- kept in lockstep with
    # ResultsReferenceFinder3's own ':all()'/'*' depth-peer vocabulary.
    # ALPHA_MANIFEST has two distinct one-level paths (zero.csv x1
    # version, one.csv x2) -- exactly what ':all()' groups by.
    def test_all_with_last_gives_each_paths_own_latest(self):
        results = _finder("$alpha.files.:all().:last()", ALPHA_HOME, ALPHA_MANIFEST)
        r = results.query()
        assert set(r.uuids) == {"u-zero-1", "u-one-2"}

    def test_all_with_first_gives_each_paths_own_earliest(self):
        results = _finder("$alpha.files.:all().:first()", ALPHA_HOME, ALPHA_MANIFEST)
        r = results.query()
        assert set(r.uuids) == {"u-zero-1", "u-one-1"}

    def test_all_with_no_name_three_dedupes_to_file_home_directories(self):
        results = _finder("$alpha.files.:all()", ALPHA_HOME, ALPHA_MANIFEST)
        r = results.query()
        assert set(r.files) == {
            "inputs/named_files/alpha/zero.csv",
            "inputs/named_files/alpha/one.csv",
        }

    def test_all_does_not_reach_a_two_level_entry(self):
        # ':all()' is now restricted to exactly one level, same as '*'
        # -- a two-level path is invisible to it, same as to '*'. Use
        # ':flatten()' (TestFlattenForOneNamedFile below) to reach it.
        results = _finder("$mixed.files.:all().:last()", MIXED_HOME, MIXED_MANIFEST)
        r = results.query()
        assert set(r.uuids) == {"u-zero-2"}

    def test_all_combined_with_manifest_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.files.:all().:last():manifest()", ALPHA_HOME, ALPHA_MANIFEST
            ).query()

    def test_all_combined_with_a_field_accessor_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.files.:all().:last():uuid()", ALPHA_HOME, ALPHA_MANIFEST
            ).query()


class TestFlattenForOneNamedFile:
    # bare ':flatten()' as name_one's entire content, for a LITERAL
    # (non-'*') root_major -- added 2026-08-12, the any-depth POOL peer
    # of ':all()' (one-level GROUP)/'*' (one-level POOL). MIXED_MANIFEST
    # has two distinct file_homes at DIFFERENT depths (zero.csv one
    # level, nested/deep.csv two levels) -- exactly what '*' cannot
    # reach (an exact segment count) and ':flatten()' pools into one
    # answer, in manifest-array order (arrival order for FILES, not a
    # "time" field -- this is one already-known manifest, same as any
    # other single-name pooled reduction).
    def test_flatten_last_pools_across_every_depth(self):
        results = _finder("$mixed.files.:flatten().:last()", MIXED_HOME, MIXED_MANIFEST)
        r = results.query()
        assert r.uuids == ["u-deep-2"]

    def test_flatten_first_pools_across_every_depth(self):
        results = _finder(
            "$mixed.files.:flatten().:first()", MIXED_HOME, MIXED_MANIFEST
        )
        r = results.query()
        assert r.uuids == ["u-zero-1"]

    def test_flatten_with_no_name_three_dedupes_to_file_homes_any_depth(self):
        results = _finder("$mixed.files.:flatten()", MIXED_HOME, MIXED_MANIFEST)
        r = results.query()
        assert set(r.files) == {
            "inputs/named_files/mixed/zero.csv",
            "inputs/named_files/mixed/nested/deep.csv",
        }

    def test_a_literal_star_misses_the_two_level_entry_flatten_does_not(self):
        star_results = _finder(
            "$mixed.files.*.:last()", MIXED_HOME, MIXED_MANIFEST
        ).query()
        assert star_results.uuids == ["u-zero-2"]
        flatten_results = _finder(
            "$mixed.files.:flatten().:last()", MIXED_HOME, MIXED_MANIFEST
        ).query()
        assert flatten_results.uuids == ["u-deep-2"]

    def test_flatten_combined_with_manifest_is_supported(self):
        # unlike ':all()' grouping, ':flatten()' pooling has no
        # under-specified-interaction restriction -- root_major is
        # always known here (unlike '*' traversal), so it reduces to
        # one entity same as an ordinary pointer would.
        results = _finder(
            "$mixed.files.:flatten().:last():manifest()", MIXED_HOME, MIXED_MANIFEST
        )
        r = results.resolve()
        assert r.results[0].data == MIXED_MANIFEST[3]


class TestManifestCombinedWithNameThree:
    # :manifest() never narrows/selects anything itself -- combined with
    # real name_one path narrowing plus name_three, it either rides
    # alongside a real version pointer (giving that one matched entry)
    # or appears alone with no pointer at all (giving every matching
    # entry, unreduced). Neither shape routes through
    # _is_bare_pointer_reference -- that is only for the sole-content
    # "$acme.files.:manifest()" case.
    def test_manifest_alone_with_more_than_one_matching_version_raises(self):
        # "one.csv" has two versions in ALPHA_MANIFEST -- resolving full
        # manifest content always touches exactly one entity (settled
        # 2026-08-07), so no pointer to pick between them is illegal now,
        # not "every entry, unreduced" as it used to be.
        finder = _finder(
            '$alpha.files.:name("one.csv").:manifest()', ALPHA_HOME, ALPHA_MANIFEST
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_manifest_alone_with_exactly_one_matching_version_still_works(self):
        # "zero.csv" has only one version -- no pointer needed, since
        # there is nothing to pick between.
        finder = _finder(
            '$alpha.files.:name("zero.csv").:manifest()', ALPHA_HOME, ALPHA_MANIFEST
        )
        results = finder.resolve()
        assert results.uuids == ["u-zero-1"]
        assert results.results[0].data == ALPHA_MANIFEST[0]

    def test_manifest_beside_a_pointer_gives_the_one_matched_entry(self):
        finder = _finder(
            '$alpha.files.:name("one.csv").:last():manifest()',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        )
        results = finder.resolve()
        assert results.uuids == ["u-one-2"]
        assert results.results[0].data == ALPHA_MANIFEST[2]

    def test_name_three_with_neither_pointer_nor_manifest_still_raises(self):
        # a context setter alone (:name(...) is not meaningful in
        # name_three for files, but exercises the same "requires a
        # pointer or :manifest()" gate either function would hit).
        finder = _finder(
            '$alpha.files.*.:name("x")', ALPHA_HOME, ALPHA_MANIFEST
        )
        with pytest.raises(ReferenceException3):
            finder.query()


class TestDefinitionFunction:
    # ":definition()" mirrors ":manifest()" exactly -- same bare, sole-
    # content shape, same query()/_extract_data() routing -- except
    # definition.json is genuinely optional, so resolving one that was
    # never written gives None rather than raising.
    def test_query_returns_the_definition_path_with_no_uuid(self):
        finder = _finder("$alpha.files.:definition()", ALPHA_HOME, ALPHA_MANIFEST)
        results = finder.query()
        assert results.files == [f"{ALPHA_HOME}/definition.json"]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_definition_files_raw_bytes(self, tmp_path):
        content = b'{"sources": {}}'
        home = tmp_path / "alpha"
        home.mkdir()
        (home / "definition.json").write_bytes(content)
        finder = _finder("$alpha.files.:definition()", str(home), ALPHA_MANIFEST)
        results = finder.resolve()
        assert results.results[0].data == content

    def test_resolve_gives_none_when_never_configured(self, tmp_path):
        # a named-file that was never explicitly configured has no
        # definition.json on disk at all -- this is a normal, expected
        # absence (matching NamedFileDescriber.get_json()'s own
        # "return {} if missing" treatment), not an error.
        home = tmp_path / "alpha"
        home.mkdir()
        finder = _finder("$alpha.files.:definition()", str(home), ALPHA_MANIFEST)
        results = finder.resolve()
        assert results.results[0].data is None


RICH_HOME = "inputs/named_files/rich"
RICH_MANIFEST = [
    {
        "file": "inputs/named_files/rich/orders.csv/aaaa.csv",
        "file_home": "inputs/named_files/rich/orders.csv",
        "uuid": "u-rich-1",
        "time": "2026-01-01T00:00:00+00:00",
        "fingerprint": "aaaa",
        "from": "/staging/orders.csv",
        "mark": "Sheet1",
    },
    {
        "file": "inputs/named_files/rich/orders.csv/bbbb.csv",
        "file_home": "inputs/named_files/rich/orders.csv",
        "uuid": "u-rich-2",
        "time": "2026-02-01T00:00:00+00:00",
        "fingerprint": "bbbb",
        "from": "/staging/orders.csv",
    },
]


class TestFieldAccessorFunctions:
    # generalized field-accessor wiring (see manifest_field_functions_
    # proposal.md, Part A/B): each of these rides in name_three exactly
    # where :manifest() already rides, either alone (every matching
    # entry, unreduced) or beside a pointer (one reduced entry) -- but
    # extracts one key from the matched entry instead of the whole thing.
    def test_bare_uuid_with_no_pointer_gives_every_matching_entrys_uuid(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:uuid()', RICH_HOME, RICH_MANIFEST
        )
        results = finder.resolve()
        assert [r.data for r in results.results] == ["u-rich-1", "u-rich-2"]

    def test_uuid_beside_a_pointer_gives_the_one_matched_value(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:last():uuid()',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data == "u-rich-2"

    def test_time(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():time()',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data == "2026-01-01T00:00:00+00:00"

    def test_fingerprint(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():fingerprint()',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data == "aaaa"

    def test_home(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():home()',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data == "inputs/named_files/rich/orders.csv"

    def test_origin_reads_the_from_key(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():origin()',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data == "/staging/orders.csv"

    def test_mark_present(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():mark()',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data == "Sheet1"

    def test_mark_absent_gives_none_not_an_error(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:last():mark()',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data is None

    def test_named_file_name_is_computed_not_read(self):
        # never stored in the Named-File Manifest -- reference.root_major
        # is already the answer, so both matched entries give the same
        # value with no pointer needed (see manifest_field_functions_
        # proposal.md, settled 2026-08-09).
        finder = _finder(
            '$rich.files.:name("orders.csv").:named_file_name()',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert [r.data for r in results.results] == ["rich", "rich"]

    def test_named_file_home_is_computed_not_read(self):
        # SOURCE == "computed" -- file_manager.named_file_home(), not any
        # manifest key, same reasoning as named_file_name above.
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():named_file_home()',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data == RICH_HOME

    def test_query_does_not_require_a_pointer_when_a_field_function_is_present(self):
        # this is the same "self-completing, no pointer needed" gate
        # :manifest() already gets -- a bare field function satisfies it
        # too.
        finder = _finder(
            '$rich.files.:name("orders.csv").:uuid()', RICH_HOME, RICH_MANIFEST
        )
        results = finder.query()
        assert len(results.results) == 2


class TestDefinitionFieldAccessorFunctions:
    # :on_arrival()/:sources() are SOURCE="definition" -- resolved
    # against the named-file's definition.json config, not a manifest
    # entry, and not affected by which version a pointer happens to
    # select (definition.json is not versioned).
    DEFINITION = {
        "on_arrival": {
            "named_paths_group": "order validations",
            "run_method": "collect_paths",
        },
        "sources": {"a": {"address": "localhost", "port": 22}},
    }

    def test_on_arrival_whole_object(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():on_arrival()',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        )
        results = finder.resolve()
        assert results.results[0].data == {
            "named_paths_group": "order validations",
            "run_method": "collect_paths",
        }

    def test_sources_whole_object(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():sources()',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        )
        results = finder.resolve()
        assert results.results[0].data == {"a": {"address": "localhost", "port": 22}}

    def test_never_configured_gives_none_not_an_error(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():on_arrival()',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data is None

    def test_same_value_regardless_of_which_version_is_selected(self):
        # definition.json is not versioned -- :last() picks a different
        # manifest entry than :first(), but :on_arrival() gives the same
        # answer either way.
        first = _finder(
            '$rich.files.:name("orders.csv").:first():on_arrival()',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        last = _finder(
            '$rich.files.:name("orders.csv").:last():on_arrival()',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert first.results[0].data == last.results[0].data


class TestPathFunction:
    # :path(inner) returns the filesystem path to whatever well-known
    # resource `inner` points at, instead of its content -- and, unlike
    # :manifest()/:definition() themselves, is meant to be poolable
    # across "*"/unresolved versions (not exercised here, since "*" as
    # root_major is not yet supported -- see manifest_field_functions_
    # proposal.md's Rule 2).
    def test_path_wrapping_manifest(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():path(:manifest())',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data == f"{RICH_HOME}/manifest.json"

    def test_path_wrapping_definition(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():path(:definition())',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data == f"{RICH_HOME}/definition.json"

    def test_path_alone_satisfies_the_no_pointer_gate(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:path(:manifest())',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.query()
        assert len(results.results) == 2

    def test_path_wrapping_a_field_accessor_is_not_yet_supported(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():path(:uuid())',
            RICH_HOME,
            RICH_MANIFEST,
        )
        with pytest.raises(ReferenceException3):
            finder.resolve()


class TestExtractData:
    def test_first_party_returns_raw_file_bytes(self, tmp_path):
        # resolve_kind is FIRST_PARTY by default (no metadata-file/
        # field function present) -- resolving a plain files reference
        # should give the version file's actual raw bytes.
        content = b"a,b\n1,2\n"
        file_path = tmp_path / "0000000000000000.csv"
        file_path.write_bytes(content)
        manifest = [
            {
                "file": str(file_path),
                "file_home": f"{ALPHA_HOME}/zero.csv",
                "uuid": "u-zero-1",
            }
        ]
        finder = _finder("$alpha.files.*.:first()", ALPHA_HOME, manifest)
        results = finder.resolve()
        assert results.results[0].data == content

    def test_metadata_file_kind_not_yet_supported(self):
        # :meta() is not a registered function yet, so a real
        # query()/resolve() would already reject this reference earlier
        # (unknown function, in build_chain()). calling _extract_data()
        # directly tests its own resolve_kind branching in isolation,
        # ahead of any metadata-file function actually existing.
        finder = _finder("$alpha.files.*.:meta()", ALPHA_HOME, ALPHA_MANIFEST)
        with pytest.raises(ReferenceException3):
            finder._extract_data(ReferenceResult3(path="p", uuid="u"))

    def test_metadata_field_kind_not_yet_supported(self):
        finder = _finder(
            '$alpha.files.*.:meta(:idchain("a[0]"))', ALPHA_HOME, ALPHA_MANIFEST
        )
        with pytest.raises(ReferenceException3):
            finder._extract_data(ReferenceResult3(path="p", uuid="u"))
