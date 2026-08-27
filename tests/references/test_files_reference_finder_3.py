import pytest

from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.reference_results_3 import ReferenceResult3
from csvpath.util.date_util import DateUtility as daut


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
    def __init__(self, inputs_files_path: str | None = None, log_file: str | None = None):
        self.inputs_files_path = inputs_files_path
        self.log_file = log_file


class _FakeCsvPaths:
    def __init__(
        self,
        file_manager,
        inputs_files_path: str | None = None,
        log_file: str | None = None,
    ):
        self.file_manager = file_manager
        self.config = _FakeConfig(inputs_files_path, log_file=log_file)


def _finder(
    reference: str,
    home: str,
    manifest: list,
    definition: dict | None = None,
    inputs_files_path: str | None = None,
    ledger: list | None = None,
    by_name: dict | None = None,
    log_file: str | None = None,
    variables: dict | None = None,
) -> FilesReferenceFinder3:
    csvpaths = _FakeCsvPaths(
        _FakeFileManager(home, manifest, definition, ledger=ledger, by_name=by_name),
        inputs_files_path=inputs_files_path,
        log_file=log_file,
    )
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return FilesReferenceFinder3(csvpaths=csvpaths, ref=ref, variables=variables)


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


class TestClockFunctionInPathSegments:
    # a bare SOURCE == "clock" function (e.g. :year()) is now a legal
    # name_one path segment in its own right (added 2026-08-26, see
    # ReferenceFinder3._compile_path_pattern()'s own docstring), and
    # :name("...")'s own string argument now evaluates any "{...}"
    # interpolation spans it contains (ReferenceFinder3._resolve_value())
    # -- both proven here against the real current year rather than a
    # mocked clock, so a fixture built from daut.now() itself always
    # matches regardless of when the suite actually runs.
    def test_bare_clock_function_as_a_path_segment(self):
        year = str(daut.now().year)
        home = f"inputs/named_files/acme/{year}/test-data"
        manifest = [{"file": f"{home}/aaaa.csv", "file_home": home, "uuid": "u-1"}]
        finder = _finder(
            "$acme.files.:year()/test-data.:first()", TEMPLATED_HOME, manifest
        )
        assert finder.query().files == [f"{home}/aaaa.csv"]

    def test_interpolated_name_containing_a_clock_function(self):
        year = str(daut.now().year)
        home = f"inputs/named_files/acme/orders-{year}.csv"
        manifest = [{"file": f"{home}/aaaa.csv", "file_home": home, "uuid": "u-1"}]
        finder = _finder(
            '$acme.files.:name("orders-{:year()}.csv").:first()',
            TEMPLATED_HOME,
            manifest,
        )
        assert finder.query().files == [f"{home}/aaaa.csv"]

    def test_non_clock_function_still_rejected_as_a_path_segment(self):
        # regression guard: the widening is specifically for SOURCE ==
        # "clock" functions, not "any function at all" -- a field
        # accessor like :uuid() still raises, same as before.
        with pytest.raises(ReferenceException3):
            _finder(
                "$acme.files.:uuid()/test-data.:first()",
                TEMPLATED_HOME,
                TEMPLATED_MANIFEST,
            ).query()

    def test_interpolated_name_combining_a_variable_and_a_clock_function(self):
        # matches the compendium's own worked example (5.37):
        # :name("partner-{:year()}-{@company}"). @variable resolution
        # (compendium 3.12, built 2026-08-26) is the other half of
        # interpolation, registered on the finder itself before
        # resolving -- see ReferenceFinder3.set_variable()'s own
        # docstring.
        year = str(daut.now().year)
        home = f"inputs/named_files/acme/partner-{year}-acme-corp"
        manifest = [{"file": f"{home}/aaaa.csv", "file_home": home, "uuid": "u-1"}]
        finder = _finder(
            '$acme.files.:name("partner-{:year()}-{@company}").:first()',
            TEMPLATED_HOME,
            manifest,
            variables={"company": "acme-corp"},
        )
        assert finder.query().files == [f"{home}/aaaa.csv"]


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


class TestStarTraversalGroupsAnyDepth:
    # bare ':groups()' as name_one's entire content -- added 2026-08-12,
    # the any-depth GROUP peer of ':all()' (one-level GROUP)/':flatten()'
    # (any-depth POOL) across every named-file. Same any-depth candidate
    # gathering as ':flatten()' (reaches gamma's two-level entry, which
    # ':all()' cannot), partitioned by file_home like ':all()' instead of
    # pooled into one answer.
    def test_last_gives_one_result_per_named_file_and_path_any_depth(self):
        all_results = _flatten_star_finder("$*.files.:all().:last()").query()
        assert set(all_results.uuids) == {"u-zero-1", "u-one-2", "u-two-2"}
        groups_results = _flatten_star_finder("$*.files.:groups().:last()").query()
        assert set(groups_results.uuids) == {
            "u-zero-1",
            "u-one-2",
            "u-two-2",
            "u-gamma-deep-1",
        }

    def test_combining_with_manifest_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _flatten_star_finder("$*.files.:groups().:last():manifest()").query()


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


ANCHOR_HOME = "inputs/named_files/anchor"
ANCHOR_MANIFEST = [
    {
        "file": "inputs/named_files/anchor/2025/orders.csv/aaa.csv",
        "file_home": "inputs/named_files/anchor/2025/orders.csv",
        "uuid": "u-one-pre-1",
    },
    {
        "file": "inputs/named_files/anchor/orders.csv/bbb.csv",
        "file_home": "inputs/named_files/anchor/orders.csv",
        "uuid": "u-zero-pre-1",
    },
    {
        "file": "inputs/named_files/anchor/returns.csv/ccc.csv",
        "file_home": "inputs/named_files/anchor/returns.csv",
        "uuid": "u-returns",
    },
    {
        "file": "inputs/named_files/anchor/2025/returns.csv/ddd.csv",
        "file_home": "inputs/named_files/anchor/2025/returns.csv",
        "uuid": "u-nested-returns",
    },
]


class TestFlattenPrefixedWithSuffix:
    # ':flatten()' as name_one's FIRST segment, followed by more path --
    # added 2026-08-12, David: "the last version of all orders.csv no
    # matter how many template levels from 0 to n"
    # ($alpha.files.:flatten()/:name("orders.csv").:last()). ANCHOR_
    # MANIFEST has "orders.csv" at both zero segments preceding
    # (directly under anchor's home) and one segment preceding
    # ("2025/orders.csv"), plus "returns.csv" at both depths too (to
    # prove the suffix anchor actually filters by name, not just by
    # depth).
    def test_last_pools_across_every_depth_including_zero(self):
        # array order: one-pre, zero-pre, returns, nested-returns --
        # zero-pre is LAST among the orders.csv-suffix matches, so it
        # wins -- proves a zero-segment-preceding match is genuinely
        # included, not just tolerated.
        results = _finder(
            '$anchor.files.:flatten()/:name("orders.csv").:last()',
            ANCHOR_HOME,
            ANCHOR_MANIFEST,
        ).query()
        assert results.uuids == ["u-zero-pre-1"]

    def test_first_pools_across_every_depth_including_zero(self):
        results = _finder(
            '$anchor.files.:flatten()/:name("orders.csv").:first()',
            ANCHOR_HOME,
            ANCHOR_MANIFEST,
        ).query()
        assert results.uuids == ["u-one-pre-1"]

    def test_only_matches_the_named_suffix_not_every_path(self):
        # "returns.csv" entries at both depths must NOT appear.
        results = _finder(
            '$anchor.files.:flatten()/:name("orders.csv")',
            ANCHOR_HOME,
            ANCHOR_MANIFEST,
        ).query()
        assert set(results.files) == {
            "inputs/named_files/anchor/orders.csv",
            "inputs/named_files/anchor/2025/orders.csv",
        }

    def test_a_literal_name_alone_misses_the_deeper_entry(self):
        # contrast: bare ':name("orders.csv")' alone is position-
        # anchored (exactly one level), so it only sees the zero-
        # preceding-segment match, never the "2025/orders.csv" one.
        results = _finder(
            '$anchor.files.:name("orders.csv")', ANCHOR_HOME, ANCHOR_MANIFEST
        ).query()
        assert results.files == ["inputs/named_files/anchor/orders.csv"]

    def test_flatten_prefixed_rejects_an_argument(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$anchor.files.:flatten("x")/:name("orders.csv").:last()',
                ANCHOR_HOME,
                ANCHOR_MANIFEST,
            ).query()

    def test_a_literal_prefix_before_flatten_is_not_yet_supported(self):
        # a THIRD shape -- literal prefix, THEN ':flatten()', THEN a
        # literal/:name(...) suffix (e.g. "2025/:flatten()/:name(...)"
        # -- "any orders.csv below 2025, at any depth") -- is a real,
        # separate extension David flagged wanting eventually, deferred
        # 2026-08-12 rather than built now. ':flatten()' is only
        # recognized as name_one's FIRST segment today
        # (_is_flatten_prefixed_reference); anywhere else it falls
        # through to the ordinary _compile_path_pattern path, which
        # raises cleanly rather than silently matching wrong -- adding
        # this later is expected to be additive (a new elif branch
        # keyed on ':flatten()' appearing at some OTHER position in
        # name_one.path) and should not touch any non-prefixed shape's
        # behavior, including the bare/no-prefix ':flatten()/...' shape
        # this class already covers.
        with pytest.raises(ReferenceException3):
            _finder(
                '$anchor.files.2025/:flatten()/:name("orders.csv").:last()',
                ANCHOR_HOME,
                ANCHOR_MANIFEST,
            ).query()


HOME_TEST_HOME = "inputs/named_files/homer"
HOME_TEST_MANIFEST = [
    {
        "file": "inputs/named_files/homer/aaa.csv",
        "file_home": "inputs/named_files/homer",
        "uuid": "u-zero-1",
    },
    {
        "file": "inputs/named_files/homer/bbb.csv",
        "file_home": "inputs/named_files/homer",
        "uuid": "u-zero-2",
    },
    {
        "file": "inputs/named_files/homer/orders.csv/ccc.csv",
        "file_home": "inputs/named_files/homer/orders.csv",
        "uuid": "u-one-level",
    },
]


class TestHomeAsAZeroLevelSelector:
    # bare ':home()' as name_one's entire content -- added 2026-08-12,
    # a zero-level selector mirroring ResultsReferenceFinder3's own
    # ':home()' (David: keep functions meaning the same thing across
    # datatypes). Unlike RESULTS, this needed real new code -- FILES'
    # name_one can never be empty, so there is no pre-existing "no
    # pattern" path for a bare pointer to fall into the way RESULTS'
    # did. HOME_TEST_MANIFEST has both zero-level entries (directly at
    # homer's own home) and a one-level "orders.csv" entry that must be
    # excluded.
    def test_home_then_pointer_gives_the_latest_zero_level_entry(self):
        results = _finder(
            "$homer.files.:home().:last()", HOME_TEST_HOME, HOME_TEST_MANIFEST
        ).query()
        assert results.uuids == ["u-zero-2"]

    def test_bare_home_dedupes_to_the_named_files_own_home_directory(self):
        results = _finder(
            "$homer.files.:home()", HOME_TEST_HOME, HOME_TEST_MANIFEST
        ).query()
        assert results.files == [HOME_TEST_HOME]
        assert results.results[0].uuid is None

    def test_home_excludes_the_one_level_entry(self):
        results = _finder(
            "$homer.files.:home()", HOME_TEST_HOME, HOME_TEST_MANIFEST
        ).query()
        assert "u-one-level" not in results.uuids

    def test_home_rejects_an_argument(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$homer.files.:home("x").:last()', HOME_TEST_HOME, HOME_TEST_MANIFEST
            ).query()

    def test_home_in_name_three_position_is_unaffected(self):
        # ':home()' keeps its ordinary field-accessor job (SOURCE ==
        # "manifest", reading "file_home") when it appears in name_three
        # instead of bare in name_one -- different position, no collision.
        results = _finder(
            '$homer.files.:name("orders.csv").:first():home()',
            HOME_TEST_HOME,
            HOME_TEST_MANIFEST,
        ).resolve()
        assert results.results[0].data == "inputs/named_files/homer/orders.csv"


class TestAllOnNameThree:
    # ':all()' as (part of) name_three's function chain -- added
    # 2026-08-12, mirroring CsvpathsReferenceFinder3's own ':all()'
    # precedent exactly: it is not a POINTER, so its whole effect is
    # simply NOT reducing -- every matched candidate comes back with its
    # own real path/uuid, unlike name_three being absent entirely (which
    # dedupes to directory-level results with uuid=None instead).
    def test_all_gives_every_matched_version_with_real_uuids(self):
        results = _finder(
            '$alpha.files.:name("one.csv").:all()', ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert set(results.uuids) == {"u-one-1", "u-one-2"}
        assert None not in results.uuids

    def test_all_differs_from_no_name_three_at_all(self):
        # no name_three: deduped to ONE directory-level result, uuid=None.
        no_name_three = _finder(
            '$alpha.files.:name("one.csv")', ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert len(no_name_three.results) == 1
        assert no_name_three.results[0].uuid is None
        # :all(): every version, unreduced, real uuids.
        with_all = _finder(
            '$alpha.files.:name("one.csv").:all()', ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert len(with_all.results) == 2
        assert all(u is not None for u in with_all.uuids)

    def test_all_combined_with_a_pointer_is_redundant_pointer_wins(self):
        # mirrors CSVPATHS' own "the same outcome as writing no pointer
        # at all" framing -- :all() alongside a real pointer does not
        # error, the pointer just reduces as normal.
        results = _finder(
            '$alpha.files.:name("one.csv").:all():last()',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        ).query()
        assert results.uuids == ["u-one-2"]


FINGERPRINT_HOME = "inputs/named_files/finn"
FINGERPRINT_MANIFEST = [
    {
        "file": "inputs/named_files/finn/orders.csv/aaaa.csv",
        "file_home": "inputs/named_files/finn/orders.csv",
        "uuid": "u-orders-1",
        "fingerprint": "aaaa",
    },
    {
        "file": "inputs/named_files/finn/2025/returns.csv/cccc.csv",
        "file_home": "inputs/named_files/finn/2025/returns.csv",
        "uuid": "u-returns-1",
        "fingerprint": "cccc",
    },
]


class TestBareFingerprintLookup:
    # bare ':fingerprint("hash...")' -- added 2026-08-13, a content-hash
    # lookup across the WHOLE named-file's manifest, every file_home/
    # path -- unlike ':name()' (a path identity), content identity does
    # not care which slot a version is registered under.
    # FINGERPRINT_MANIFEST deliberately has its match at TWO levels deep
    # (2025/returns.csv), proving this is not just pattern-matching one
    # level like ':name()' would be.
    def test_finds_the_matching_version_with_real_path_and_uuid(self):
        results = _finder(
            '$finn.files.:fingerprint("cccc")', FINGERPRINT_HOME, FINGERPRINT_MANIFEST
        ).query()
        assert results.files == ["inputs/named_files/finn/2025/returns.csv/cccc.csv"]
        assert results.uuids == ["u-returns-1"]

    def test_no_match_gives_empty(self):
        results = _finder(
            '$finn.files.:fingerprint("nope")', FINGERPRINT_HOME, FINGERPRINT_MANIFEST
        ).query()
        assert results.results == []

    def test_bare_no_arg_is_not_recognized_here(self):
        # no arg means there is no candidate to read the field off of at
        # this position -- falls through to the ordinary "not yet
        # supported" rejection, not a silent no-op.
        with pytest.raises(ReferenceException3):
            _finder(
                "$finn.files.:fingerprint()", FINGERPRINT_HOME, FINGERPRINT_MANIFEST
            ).query()

    def test_combined_with_name_three_is_not_yet_supported(self):
        # a fingerprint already identifies one specific version -- no
        # further narrowing is meaningful.
        with pytest.raises(ReferenceException3):
            _finder(
                '$finn.files.:fingerprint("cccc").:last()',
                FINGERPRINT_HOME,
                FINGERPRINT_MANIFEST,
            ).query()

    def test_ordinary_field_accessor_usage_is_unaffected(self):
        # riding alongside a matched version in name_three (its original,
        # pre-existing job) still works exactly as before.
        results = _finder(
            '$finn.files.:name("orders.csv").:first():fingerprint()',
            FINGERPRINT_HOME,
            FINGERPRINT_MANIFEST,
        ).resolve()
        assert results.results[0].data == "aaaa"

    def test_an_argument_in_the_field_accessor_position_is_rejected(self):
        # ARG_TYPES now allows a str arg (for the bare lookup form) --
        # confirm it does NOT get silently ignored when :fingerprint()
        # rides in its ordinary field-accessor position instead.
        with pytest.raises(ReferenceException3):
            _finder(
                '$finn.files.:name("orders.csv").:first():fingerprint("x")',
                FINGERPRINT_HOME,
                FINGERPRINT_MANIFEST,
            ).query()

    def test_two_different_logical_files_sharing_one_fingerprint_both_come_back(self):
        # confirms the "at most one match is expected in practice... not
        # specially guarded against" comment in query() -- two DIFFERENT
        # logical files (different file_home) with byte-identical content
        # share one fingerprint here; the lookup is not artificially
        # restricted to one result, it returns every real match.
        shared_manifest = FINGERPRINT_MANIFEST + [
            {
                "file": "inputs/named_files/finn/backups/orders.csv/aaaa.csv",
                "file_home": "inputs/named_files/finn/backups/orders.csv",
                "uuid": "u-orders-backup-1",
                "fingerprint": "aaaa",
            }
        ]
        results = _finder(
            '$finn.files.:fingerprint("aaaa")', FINGERPRINT_HOME, shared_manifest
        ).query()
        assert results.files == [
            "inputs/named_files/finn/orders.csv/aaaa.csv",
            "inputs/named_files/finn/backups/orders.csv/aaaa.csv",
        ]
        assert results.uuids == ["u-orders-1", "u-orders-backup-1"]


RANGE_HOME = "inputs/named_files/ranger"
RANGE_MANIFEST = [
    {
        "file": f"inputs/named_files/ranger/orders.csv/v{i}.csv",
        "file_home": "inputs/named_files/ranger/orders.csv",
        "uuid": f"v{i}",
        "time": f"2026-01-0{i + 1}T00:00:00+00:00",
    }
    for i in range(5)
]


class TestNameThreeRange:
    # ':from()'/':to()' as a name_three version range -- added
    # 2026-08-13, David: rewind/replay and comparing versions need "the
    # last N versions of a named-file" the same way RESULTS' own
    # run-level range does. Windows the ordered version list of the
    # already name_one-matched file, same position :first()/:last()/
    # :index(n) already occupy.
    def test_from_index_negative_gives_the_last_n(self):
        results = _finder(
            '$ranger.files.:name("orders.csv").:from(-3)', RANGE_HOME, RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v2", "v3", "v4"]

    def test_from_and_to_together_is_an_inclusive_range(self):
        results = _finder(
            '$ranger.files.:name("orders.csv").:from(1):to(3)',
            RANGE_HOME,
            RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v1", "v2", "v3"]

    def test_a_pointer_reduces_the_range_not_the_full_candidate_set(self):
        results = _finder(
            '$ranger.files.:name("orders.csv").:from(-3):last()',
            RANGE_HOME,
            RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v4"]

    def test_date_mode_from_filters_by_the_versions_own_arrival_time(self):
        # broadened from RESULTS-only 2026-08-13 -- David: a named-file
        # version's own registration/load "time" is a real arrival-date
        # concept, same as RESULTS' run start time.
        results = _finder(
            '$ranger.files.:name("orders.csv").:from(:date("2026-01-03"))',
            RANGE_HOME,
            RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v2", "v3", "v4"]

    def test_date_mode_from_and_to_together_is_an_inclusive_range(self):
        # the bare-string shape (no ':date()' wrapper) is also valid,
        # same as RESULTS' own date-mode.
        results = _finder(
            '$ranger.files.:name("orders.csv").:from("2026-01-02"):to("2026-01-04")',
            RANGE_HOME,
            RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v1", "v2", "v3"]

    def test_mixing_index_mode_and_date_mode_bounds_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$ranger.files.:name("orders.csv").:from(1):to(:date("2026-01-01"))',
                RANGE_HOME,
                RANGE_MANIFEST,
            ).query()

    def test_a_malformed_date_bound_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$ranger.files.:name("orders.csv").:from("not-a-date")',
                RANGE_HOME,
                RANGE_MANIFEST,
            ).query()

    def test_range_combined_with_grouping_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$ranger.files.:all().:from(-1)", RANGE_HOME, RANGE_MANIFEST
            ).query()


class TestGroupsForOneNamedFile:
    # bare ':groups()' as name_one's entire content, for a LITERAL
    # (non-'*') root_major -- added 2026-08-12, the any-depth GROUP peer
    # of ':all()' (one-level GROUP)/':flatten()' (any-depth POOL). Same
    # any-depth candidate gathering as ':flatten()' (MIXED_MANIFEST's two
    # different-depth file_homes), but partitioned like ':all()' instead
    # of pooled -- reaches BOTH distinct paths, each own reduction,
    # exactly the case a literal/'*' pattern and ':all()' (both one
    # level) cannot reach on their own.
    def test_groups_last_gives_each_paths_own_latest_at_any_depth(self):
        results = _finder("$mixed.files.:groups().:last()", MIXED_HOME, MIXED_MANIFEST)
        r = results.query()
        assert set(r.uuids) == {"u-zero-2", "u-deep-2"}

    def test_groups_first_gives_each_paths_own_earliest_at_any_depth(self):
        results = _finder("$mixed.files.:groups().:first()", MIXED_HOME, MIXED_MANIFEST)
        r = results.query()
        assert set(r.uuids) == {"u-zero-1", "u-deep-1"}

    def test_groups_with_no_name_three_is_the_same_as_flatten(self):
        # with no pointer, "partitioned" and "pooled" candidate sets are
        # identical -- both just dedupe by file_home over the same
        # any-depth gathering, same as ':all()'/'*' already coincide
        # with no pointer.
        groups_results = _finder("$mixed.files.:groups()", MIXED_HOME, MIXED_MANIFEST).query()
        flatten_results = _finder(
            "$mixed.files.:flatten()", MIXED_HOME, MIXED_MANIFEST
        ).query()
        assert set(groups_results.files) == set(flatten_results.files)

    def test_a_literal_all_misses_the_two_level_entry_groups_does_not(self):
        all_results = _finder(
            "$mixed.files.:all().:last()", MIXED_HOME, MIXED_MANIFEST
        ).query()
        assert set(all_results.uuids) == {"u-zero-2"}
        groups_results = _finder(
            "$mixed.files.:groups().:last()", MIXED_HOME, MIXED_MANIFEST
        ).query()
        assert set(groups_results.uuids) == {"u-zero-2", "u-deep-2"}

    def test_groups_combined_with_manifest_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$mixed.files.:groups().:last():manifest()", MIXED_HOME, MIXED_MANIFEST
            ).query()

    def test_groups_combined_with_a_field_accessor_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$mixed.files.:groups().:last():uuid()", MIXED_HOME, MIXED_MANIFEST
            ).query()


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
        # 2026-08-07), so no pointer to pick between them is illegal.
        # query() itself succeeds (moved 2026-08-26, see the ":path()"
        # retirement/Rule 1 bucket-list entry) -- only resolve() raises,
        # once something actually tries to read the content.
        finder = _finder(
            '$alpha.files.:name("one.csv").:manifest()', ALPHA_HOME, ALPHA_MANIFEST
        )
        assert len(finder.query()) > 1
        with pytest.raises(ReferenceException3):
            finder.resolve()

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

    def test_type_and_reference_and_file_path(self):
        manifest = [
            {**RICH_MANIFEST[0], "type": "csv", "reference": "ref-aaaa"},
        ]
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():type()', RICH_HOME, manifest
        )
        assert finder.resolve().results[0].data == "csv"

        finder = _finder(
            '$rich.files.:name("orders.csv").:first():reference()', RICH_HOME, manifest
        )
        assert finder.resolve().results[0].data == "ref-aaaa"

        finder = _finder(
            '$rich.files.:name("orders.csv").:first():file_path()', RICH_HOME, manifest
        )
        assert finder.resolve().results[0].data == manifest[0]["file"]


class TestLedgerFallbackFieldAccessor:
    # :file_manifest() has KEY = {} (RICH_MANIFEST's own entries never
    # have this field -- confirmed, the named-file's own manifest has no
    # self-reference to itself, see issue #261) and LEDGER_KEY pointing
    # at the global ledger instead -- proves Function3.LEDGER_KEY's
    # fallback mechanism actually reaches the ledger, not just that it
    # is declared.
    LEDGER = [
        {
            "uuid": "u-rich-2",
            "file_manifest": "inputs/named_files/rich/manifest.json",
        },
    ]

    def test_field_missing_from_own_manifest_falls_back_to_ledger_entry(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:last():file_manifest()',
            RICH_HOME,
            RICH_MANIFEST,
            ledger=self.LEDGER,
        )
        results = finder.resolve()
        assert results.results[0].data == "inputs/named_files/rich/manifest.json"

    def test_no_matching_ledger_entry_gives_none(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():file_manifest()',
            RICH_HOME,
            RICH_MANIFEST,
            ledger=self.LEDGER,
        )
        # RICH_MANIFEST's first entry is u-rich-1, which has no matching
        # LEDGER entry (only u-rich-2 does) -- falls through to None
        # rather than raising, same "absence is normal" treatment as
        # every other field lookup.
        results = finder.resolve()
        assert results.results[0].data is None


class TestUsernameHostnameHostLedgerFallback:
    # username/hostname/host widened 2026-08-26 to also cover FILES --
    # RICH_MANIFEST's own entries never have these fields (confirmed,
    # the Named-File Manifest genuinely has no such fields), only the
    # global arrivals ledger does.
    LEDGER = [
        {
            "uuid": "u-rich-2",
            "username": "bot",
            "hostname": "worker-1",
            "ip_address": "10.0.0.5",
        },
    ]

    def test_username_falls_back_to_the_ledger_entry(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:last():username()',
            RICH_HOME,
            RICH_MANIFEST,
            ledger=self.LEDGER,
        )
        assert finder.resolve().results[0].data == "bot"

    def test_hostname_falls_back_to_the_ledger_entry(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:last():hostname()',
            RICH_HOME,
            RICH_MANIFEST,
            ledger=self.LEDGER,
        )
        assert finder.resolve().results[0].data == "worker-1"

    def test_host_falls_back_to_the_ledger_entry(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:last():host()',
            RICH_HOME,
            RICH_MANIFEST,
            ledger=self.LEDGER,
        )
        assert finder.resolve().results[0].data == "10.0.0.5"

    def test_no_matching_ledger_entry_gives_none(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():username()',
            RICH_HOME,
            RICH_MANIFEST,
            ledger=self.LEDGER,
        )
        # RICH_MANIFEST's first entry is u-rich-1, which has no
        # matching LEDGER entry (only u-rich-2 does).
        assert finder.resolve().results[0].data is None


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

    def test_named_paths_group_and_run_method(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():named_paths_group()',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        )
        assert finder.resolve().results[0].data == "order validations"

        finder = _finder(
            '$rich.files.:name("orders.csv").:first():run_method()',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        )
        assert finder.resolve().results[0].data == "collect_paths"

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

    def test_bare_on_arrival_needs_no_name_or_version(self):
        # settled 2026-08-12: on_arrival lives in the named-file's own
        # definition.json (root_major-scoped), not any particular file/
        # version, so it needs no :name(...)/pointer at all to resolve
        # -- matches ":definition()" itself, which already gets this
        # same bare treatment.
        finder = _finder(
            "$rich.files.:on_arrival()", RICH_HOME, RICH_MANIFEST, self.DEFINITION
        )
        results = finder.resolve()
        assert results.results[0].data == self.DEFINITION["on_arrival"]
        assert results.results[0].uuid is None

    def test_bare_sources_needs_no_name_or_version(self):
        finder = _finder(
            "$rich.files.:sources()", RICH_HOME, RICH_MANIFEST, self.DEFINITION
        )
        results = finder.resolve()
        assert results.results[0].data == self.DEFINITION["sources"]

    def test_bare_on_arrival_never_configured_gives_none(self):
        finder = _finder("$rich.files.:on_arrival()", RICH_HOME, RICH_MANIFEST)
        results = finder.resolve()
        assert results.results[0].data is None

    def test_bare_on_arrival_query_gives_the_definition_path_no_uuid(self):
        finder = _finder(
            "$rich.files.:on_arrival()", RICH_HOME, RICH_MANIFEST, self.DEFINITION
        )
        results = finder.query()
        assert results.files == [f"{RICH_HOME}/definition.json"]
        assert results.results[0].uuid is None

    def test_bare_manifest_sourced_field_accessor_still_requires_a_match(self):
        # contrast case: SOURCE == "manifest" field accessors (e.g.
        # :uuid()) genuinely vary by which version matched, so they are
        # NOT given the same bare treatment -- still requires :name(...)
        # (or '*') to identify a real candidate.
        with pytest.raises(ReferenceException3):
            _finder("$rich.files.:uuid()", RICH_HOME, RICH_MANIFEST).query()


class TestSourceSubFieldAccessorFunctions:
    # sources.<name>.* -- arg-keyed (built 2026-08-26, see
    # ReferenceFinder3._apply_key_arg()'s own docstring for the shared
    # "{}"-placeholder mechanism). Same bare-name_one treatment as
    # :sources() itself (SOURCE="definition", no version needed), plus
    # the ordinary name_three position beside a matched pointer.
    DEFINITION = {
        "sources": {
            "email": {
                "address": "mail.example.com",
                "port": 993,
                "username": "bot",
                "password": "secret",
            }
        }
    }

    def test_source_address_bare(self):
        finder = _finder(
            '$rich.files.:source_address("email")',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        )
        assert finder.resolve().results[0].data == "mail.example.com"

    def test_source_port_bare(self):
        finder = _finder(
            '$rich.files.:source_port("email")',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        )
        assert finder.resolve().results[0].data == 993

    def test_source_username_bare(self):
        finder = _finder(
            '$rich.files.:source_username("email")',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        )
        assert finder.resolve().results[0].data == "bot"

    def test_source_password_bare(self):
        finder = _finder(
            '$rich.files.:source_password("email")',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        )
        assert finder.resolve().results[0].data == "secret"

    def test_source_address_at_name_three(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():source_address("email")',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        )
        assert finder.resolve().results[0].data == "mail.example.com"

    def test_unknown_source_name_gives_none_not_an_error(self):
        finder = _finder(
            '$rich.files.:source_address("nope")',
            RICH_HOME,
            RICH_MANIFEST,
            self.DEFINITION,
        )
        assert finder.resolve().results[0].data is None


class TestTemplateBareVsMatchedDualSource:
    # :template() (built 2026-08-26) is the first field accessor using
    # Function3.BARE_SOURCE -- bare, name_one-only (no :name(...)/match
    # at all) reads definition.json's current default; matched at
    # name_three beside a real version, it reads that version's own
    # manifest snapshot instead. See ReferenceFinder3._bare_definition_
    # field_call()/Template3's own docstring for the full design.
    DEFINITION = {"template": "current-default"}

    def test_bare_reads_the_current_definition_default(self):
        manifest = [
            {**RICH_MANIFEST[0], "template": "snapshot-v1"},
            {**RICH_MANIFEST[1], "template": "snapshot-v2"},
        ]
        finder = _finder(
            "$rich.files.:template()", RICH_HOME, manifest, self.DEFINITION
        )
        assert finder.resolve().results[0].data == "current-default"

    def test_matched_first_reads_that_versions_own_manifest_snapshot(self):
        manifest = [
            {**RICH_MANIFEST[0], "template": "snapshot-v1"},
            {**RICH_MANIFEST[1], "template": "snapshot-v2"},
        ]
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():template()',
            RICH_HOME,
            manifest,
            self.DEFINITION,
        )
        assert finder.resolve().results[0].data == "snapshot-v1"

    def test_matched_last_reads_that_versions_own_manifest_snapshot(self):
        manifest = [
            {**RICH_MANIFEST[0], "template": "snapshot-v1"},
            {**RICH_MANIFEST[1], "template": "snapshot-v2"},
        ]
        finder = _finder(
            '$rich.files.:name("orders.csv").:last():template()',
            RICH_HOME,
            manifest,
            self.DEFINITION,
        )
        assert finder.resolve().results[0].data == "snapshot-v2"

    def test_bare_never_configured_gives_none_not_an_error(self):
        finder = _finder("$rich.files.:template()", RICH_HOME, RICH_MANIFEST)
        assert finder.resolve().results[0].data is None


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


class TestPositionEnforcement:
    # ReferenceFinder3._check_position() -- added 2026-08-14, the
    # enforced replacement for the scattered "is this recognized"
    # guards each Finder used to hand-write on its own. FILES is the
    # second Finder retrofitted to call it, after CSVPATHS.
    def test_an_extra_unrecognized_function_on_name_three_is_rejected(self):
        # the actual bug this closes for FILES: the old "at least one
        # recognized category present" gate never rejected an
        # individual EXTRA unrecognized function riding alongside a
        # legitimate one -- confirmed via direct testing before this
        # fix that ":last():name('y')" silently swallowed the stray
        # :name() instead of raising, the same bug class already fixed
        # for CSVPATHS' :name() on name_one.
        with pytest.raises(ReferenceException3):
            _finder(
                '$alpha.files.:name("one.csv").:last():name("y")',
                ALPHA_HOME,
                ALPHA_MANIFEST,
            ).query()

    def test_a_legal_function_is_unaffected(self):
        # sanity check that the new check does not over-reject.
        results = _finder(
            '$alpha.files.:name("one.csv").:last()', ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert len(results.results) == 1
        assert results.uuids[0] in ("u-one-1", "u-one-2")

    def test_name_is_not_legal_at_name_three(self):
        # :name() is FILES' own name_one path-building function -- it
        # has never been meaningful riding beside a matched version at
        # name_three.
        with pytest.raises(ReferenceException3):
            _finder(
                '$alpha.files.:name("one.csv").:name("y")',
                ALPHA_HOME,
                ALPHA_MANIFEST,
            ).query()


class TestLog:
    # compendium 5.16(b) -- see test_csvpaths_reference_finder_3.py's
    # own TestLog for the full scenario set (shared ABC mechanism,
    # ReferenceFinder3._bare_log_call()/_query_log_call()/
    # _read_log_file()); this just confirms it composes correctly with
    # FilesReferenceFinder3's own query()/_extract_data() dispatch too.
    def test_bare_log_resolves_the_whole_file(self, tmp_path):
        log_path = tmp_path / "csvpath.log"
        log_path.write_text("line1\nline2\n")
        results = _finder(
            "$*.files.:log()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            log_file=str(log_path),
        ).resolve()
        assert results.results[0].data == "line1\nline2\n"
