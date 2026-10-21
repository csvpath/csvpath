import os

import pytest

from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.reference_results_3 import ReferenceResult3
from csvpath.util.date_util import DateUtility as daut
from csvpath.util.path_util import PathUtility as pathu


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


class _PerNameFakeFileDescriber:
    # added 2026-10-17 for the predicate-argument filtering tests
    # (':home():definition(:on_arrival(:not_none()))') -- those need a
    # DIFFERENT on_arrival config per named-file to prove filtering
    # actually filters, which the single-global-dict _FakeFileDescriber
    # above cannot express. Falls back to {} (an empty/unconfigured
    # Config, same as the bare-dict describer's own default) for any
    # name not given its own entry.
    def __init__(self, definitions: dict):
        self._definitions = definitions

    def get_config(self, name):
        from csvpath.managers.files.file_descriptor import Config

        return Config(**self._definitions.get(name, {}))


class _FakeFileManager:
    def __init__(
        self,
        home,
        manifest,
        definition: dict | None = None,
        ledger=None,
        by_name: dict | None = None,
        definitions: dict | None = None,
    ):
        self._home = home
        self._manifest = manifest
        self._definition = definition or {}
        self._ledger = manifest if ledger is None else ledger
        # by_name: {name: (home, manifest)} -- only used by '*' traversal
        # tests, which need more than one distinct named-file. Every
        # other test uses the single (home, manifest) pair above.
        self._by_name = by_name
        # definitions: {name: definition_dict} -- per-named-file
        # describer configs, added 2026-10-17 alongside by_name, for
        # tests that need DIFFERENT definition.json content per name
        # (see _PerNameFakeFileDescriber above). None (the default)
        # preserves the single-global-definition describer exactly as
        # it always worked.
        self._definitions = definitions

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
        if self._definitions is not None:
            return _PerNameFakeFileDescriber(self._definitions)
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
    definitions: dict | None = None,
) -> FilesReferenceFinder3:
    csvpaths = _FakeCsvPaths(
        _FakeFileManager(
            home,
            manifest,
            definition,
            ledger=ledger,
            by_name=by_name,
            definitions=definitions,
        ),
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

    def test_name_with_a_regex_arg_searches_not_exact_matches(self):
        # added 2026-08-27, see the "name_one path segment cannot be a
        # regex" bucket-list entry -- ALPHA_MANIFEST has "zero.csv" and
        # "one.csv" (two versions); /one/ must match only "one.csv".
        finder = _finder(
            "$alpha.files.:name(/one/).:index(0)", ALPHA_HOME, ALPHA_MANIFEST
        )
        assert finder.query().files == [
            "inputs/named_files/alpha/one.csv/1111111111abcdef.csv"
        ]

    def test_name_with_a_regex_arg_matching_nothing_returns_empty(self):
        finder = _finder(
            "$alpha.files.:name(/nope/).:first()", ALPHA_HOME, ALPHA_MANIFEST
        )
        assert finder.query().files == []

    def test_name_with_an_invalid_regex_arg_raises(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.files.:name(/(unclosed/).:first()", ALPHA_HOME, ALPHA_MANIFEST
            ).query()


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

    def test_name_two_worksheet_marker_beside_a_pointer_now_works(self):
        # '#worksheet' settled 2026-08-26 -- legal against a literal
        # path (a wildcard path segment counts, same as :name("...")),
        # combined with a real version-selecting pointer. See
        # TestNameTwoWorksheetMarker below for actually resolving one.
        finder = _finder(
            '$alpha.files.*#sheet1.:last()', ALPHA_HOME, ALPHA_MANIFEST
        )
        results = finder.query()
        assert results.results[0].identity == "sheet1"

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

    def test_literal_name_three_body_now_matches_by_fingerprint(self):
        # REVISED 2026-09-22 -- superseded by the literal-name_three-body
        # fix (see TestLiteralNameThreeBody): a literal body is no
        # longer an unconditional rejection, it is a fingerprint match
        # against the name_one-matched candidates. ALPHA_MANIFEST's own
        # entries have no "fingerprint" field at all, so "v1" (not a
        # real fingerprint value here) correctly gives empty results,
        # not an error -- the same "no match" convention every other
        # literal-identity lookup in this codebase already uses.
        finder = _finder("$alpha.files.*.v1", ALPHA_HOME, ALPHA_MANIFEST)
        results = finder.query()
        assert results.results == []

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
        assert results.files == [pathu.resep(f"{ALPHA_HOME}/manifest.json")]
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
        assert results.files == [pathu.resep("inputs/named_files/manifest.json")]
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

    # :manifest() alone stays the one function with a real GLOBAL
    # resource to fall back to at "*" root_major (Rule 1a, above) --
    # :definition() has no such global resource, so a bare ':definition()'
    # at "*" root_major means something different: every named-file's own
    # definition.json, one per name. See TestStarTraversalDefinition
    # below (added 2026-08-27, FILES '*' traversal generalization
    # bucket-list entry) -- this used to be unsupported outright, since
    # nothing routed :definition() through _query_star_traversal() at
    # all; a fixture with only one named-file (ALPHA_HOME/ALPHA_MANIFEST,
    # by_name=None means named_file_names is []) could not have exercised
    # the real "*" case anyway.

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
        assert results.files == [pathu.resep("inputs/named_files/manifest.json")]
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
        "fingerprint": "aaa",
    },
    {
        "file": "inputs/named_files/alpha/one.csv/bbb.csv",
        "file_home": "inputs/named_files/alpha/one.csv",
        "uuid": "u-one-1",
        "time": "2026-01-02T00:00:00+00:00",
        "fingerprint": "bbb",
    },
    {
        "file": "inputs/named_files/alpha/one.csv/ccc.csv",
        "file_home": "inputs/named_files/alpha/one.csv",
        "uuid": "u-one-2",
        "time": "2026-01-03T00:00:00+00:00",
        "fingerprint": "ccc",
    },
]
STAR_BETA_HOME = "inputs/named_files/beta"
STAR_BETA_MANIFEST = [
    {
        "file": "inputs/named_files/beta/two.csv/ddd.csv",
        "file_home": "inputs/named_files/beta/two.csv",
        "uuid": "u-two-1",
        "time": "2026-01-04T00:00:00+00:00",
        "fingerprint": "ddd",
    },
    {
        "file": "inputs/named_files/beta/two.csv/eee.csv",
        "file_home": "inputs/named_files/beta/two.csv",
        "uuid": "u-two-2",
        "time": "2026-01-05T00:00:00+00:00",
        "fingerprint": "eee",
    },
]
STAR_BY_NAME = {
    "beta": (STAR_BETA_HOME, STAR_BETA_MANIFEST),
    "alpha": (STAR_ALPHA_HOME, STAR_ALPHA_MANIFEST),
}

# a field accessor riding alongside a pointer during '*' traversal --
# narrowed 2026-08-29 -- resolves via _extract_data()'s Star3-aware
# branch, which reads the global arrivals ledger (result.uuid alone does
# not say which named-file a candidate came from) -- these tests need a
# ledger entry for every uuid any of them might resolve, unlike every
# OTHER star-traversal test in this file, which never reads the ledger
# at all.
STAR_LEDGER = [
    {"uuid": "u-zero-1", "fingerprint": "aaa"},
    {"uuid": "u-one-1", "fingerprint": "bbb"},
    {"uuid": "u-one-2", "fingerprint": "ccc"},
    {"uuid": "u-two-1", "fingerprint": "ddd"},
    {"uuid": "u-two-2", "fingerprint": "eee"},
]


def _star_finder(reference: str) -> FilesReferenceFinder3:
    return _finder(
        reference,
        STAR_ALPHA_HOME,
        STAR_ALPHA_MANIFEST,
        by_name=STAR_BY_NAME,
        ledger=STAR_LEDGER,
    )


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

    def test_combining_with_manifest_now_works(self):
        # REVISED 2026-09-28 (was: "...is_not_yet_supported") -- POOL
        # mode always reduces to exactly one overall candidate, so
        # ':manifest()' riding alongside the pointer is never ambiguous
        # here at all (unlike GROUP mode, see TestStarTraversalGroup's
        # own equivalent test) -- converted from an unconditional raise
        # to the deferred Rule 1 pattern, same as every other content-
        # accessor guard this session; this specific shape happens to
        # never actually trip it.
        results = _star_finder("$*.files.*.:last():manifest()").resolve()
        assert results.results[0].uuid == "u-two-2"

    def test_combining_with_a_field_accessor_now_works(self):
        # narrowed 2026-08-29 -- POOL mode always reduces to exactly one
        # overall candidate, so a field accessor riding alongside the
        # pointer is unambiguous the same way it already was for every
        # other pointer+field-accessor position in this file.
        results = _star_finder("$*.files.*.:last():uuid()").resolve()
        assert results.results[0].data == "u-two-2"

    def test_functions_directly_on_name_one_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _star_finder("$*.files.*:last().v1").query()


class TestStarTraversalLiteralNameThreeBody:
    # a literal fingerprint body in name_three during '*' traversal --
    # added 2026-10-20 (not-yet-supported sweep #4), closing a real
    # parity gap: the identical literal-root shape (TestLiteralName
    # ThreeBody above) already supported this, but '*' traversal
    # rejected ANY name_three body unconditionally. Matches across
    # every named-file's own pooled candidates, same as the bare '*'
    # pointer case does for ordinal position.
    def test_matches_across_every_named_file(self):
        results = _star_finder("$*.files.*.bbb").query()
        assert results.uuids == ["u-one-1"]

    def test_no_match_gives_empty(self):
        results = _star_finder("$*.files.*.zzz").query()
        assert results.results == []

    def test_combined_with_a_manifest_call(self):
        results = _star_finder("$*.files.*.bbb:manifest()").resolve()
        assert results.results[0].uuid == "u-one-1"
        assert results.results[0].data["fingerprint"] == "bbb"

    def test_combined_with_a_field_accessor(self):
        results = _star_finder("$*.files.*.bbb:fingerprint()").resolve()
        assert results.results[0].data == "bbb"


MANIFEST_FIELD_LEDGER = [
    {
        "named_file_name": "alpha",
        "uuid": "u-ledger-1",
        "file_path": "inputs/named_files/alpha/one.csv/bbb.csv",
    },
    {
        "named_file_name": "beta",
        "uuid": "u-ledger-2",
        "file_path": "inputs/named_files/beta/two.csv/ddd.csv",
    },
]


class TestStarBareManifestFieldAccessor:
    # ':manifest():uuid()' during '*' traversal -- added 2026-08-28,
    # David's own worked example ("get uuids from all registrations").
    # Reads the global arrivals ledger (Rule 1a's own resource for bare
    # ':manifest()' at '*' root), same as the literal-root shape reads
    # its one named-file's own manifest.json.
    def test_query_gives_one_result_per_ledger_entry(self):
        results = _finder(
            "$*.files.:manifest():uuid()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=MANIFEST_FIELD_LEDGER,
        ).query()
        assert set(results.uuids) == {"u-ledger-1", "u-ledger-2"}

    def test_resolve_reads_the_field_off_each_ledger_entry(self):
        results = _finder(
            "$*.files.:manifest():uuid()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=MANIFEST_FIELD_LEDGER,
        ).resolve()
        assert {r.data for r in results.results} == {"u-ledger-1", "u-ledger-2"}

    def test_composes_with_a_regex_name_filter_at_root_major(self):
        results = _finder(
            "$:regex(/^al.*/).files.:manifest():uuid()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=MANIFEST_FIELD_LEDGER,
        ).query()
        assert results.uuids == ["u-ledger-1"]

    def test_combined_with_name_three_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.files.:manifest():uuid().:last()",
                ALPHA_HOME,
                ALPHA_MANIFEST,
                inputs_files_path="inputs/named_files",
                ledger=MANIFEST_FIELD_LEDGER,
            ).query()


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

    def test_all_combined_with_manifest_now_resolves_each_groups_own_entry(self):
        # REVISED 2026-10-16 (was: "...query_succeeds_resolve_raises") --
        # see the "'*'-traversal content-accessor guards" bucket-list
        # entry. GROUP mode reduces each of the three distinct (named-
        # file, path) groups to its own single pointer-selected winner
        # BEFORE :manifest() ever reads it -- "three groups, each already
        # reduced to exactly one" is not the same Rule 1 violation as
        # pooling several raw, unreduced candidates sharing one
        # :manifest() read (the identical shape CSVPATHS already ships
        # for its own ':all():last():manifest()'). No longer flagged as
        # an ambiguous content read, and resolve() now succeeds, giving
        # each group's own manifest entry.
        results = _star_finder("$*.files.:all().:last():manifest()").resolve()
        assert len(results.results) == 3
        assert results.ambiguous_content_read is False
        assert {r.data["uuid"] for r in results.results} == {
            "u-zero-1",
            "u-one-2",
            "u-two-2",
        }

    def test_all_combined_with_a_field_accessor_now_works(self):
        # narrowed 2026-08-29 -- one value per (named-file, path) group,
        # same as the literal-root ':all()' GROUP-mode fix the same day.
        results = _star_finder("$*.files.:all().:last():uuid()").resolve()
        assert {r.data for r in results.results} == {
            "u-zero-1",
            "u-one-2",
            "u-two-2",
        }

    def test_field_accessor_with_no_pointer_now_works(self):
        # added 2026-09-25 -- a field accessor alone (no pointer) used to
        # raise unconditionally here, even though the identical literal-
        # root ':all()' shape already allowed it (field accessors are
        # exempt from Rule 1's "reduce to one entity first" requirement).
        # GROUP mode is not specially reduced without a pointer -- every
        # candidate's own value comes back, same as POOL mode's own
        # no-pointer case just below.
        results = _star_finder("$*.files.:all().:uuid()").resolve()
        assert {r.data for r in results.results} == {
            "u-zero-1",
            "u-one-1",
            "u-one-2",
            "u-two-1",
            "u-two-2",
        }


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
FLATTEN_LEDGER = STAR_LEDGER + [{"uuid": "u-gamma-deep-1"}]


def _flatten_star_finder(reference: str) -> FilesReferenceFinder3:
    csvpaths = _FakeCsvPaths(
        _FakeFileManager(None, None, by_name=FLATTEN_BY_NAME, ledger=FLATTEN_LEDGER)
    )
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

    def test_combining_with_manifest_now_works(self):
        # REVISED 2026-09-28 (was: "...is_not_yet_supported") -- POOL
        # mode (':flatten()' included -- any-depth, but still exactly
        # one overall candidate) is never ambiguous, so this now
        # resolves cleanly, converted from an unconditional raise to the
        # deferred Rule 1 pattern (which, for this POOL shape, never
        # actually trips) -- see TestStarTraversalFlatten's own
        # equivalent one-level test.
        results = _flatten_star_finder(
            "$*.files.:flatten().:last():manifest()"
        ).resolve()
        assert results.results[0].uuid == "u-gamma-deep-1"

    def test_combining_with_a_field_accessor_now_works(self):
        # narrowed 2026-08-29 -- POOL mode always reduces to exactly one
        # overall candidate, so a field accessor riding alongside the
        # pointer is unambiguous, the any-depth peer of '*' traversal's
        # own POOL-mode fix (TestStarTraversalFlatten above).
        results = _flatten_star_finder("$*.files.:flatten().:last():uuid()").resolve()
        assert results.results[0].data == "u-gamma-deep-1"

    def test_field_accessor_with_no_pointer_now_works(self):
        # added 2026-09-25 -- surfaced investigating why FILES'
        # implied-'*' work stalled (see the bucket list): the literal-
        # root shape ("$acme.files.:flatten().:uuid()") already allowed
        # a field accessor with no pointer (field accessors are exempt
        # from Rule 1), but this '*'-traversal twin unconditionally
        # required a pointer -- a real, narrower gap, not a design
        # difference. Every candidate's own value now comes back,
        # unreduced, across every named-file and depth.
        results = _flatten_star_finder("$*.files.:flatten().:uuid()").resolve()
        assert {r.data for r in results.results} == {
            "u-zero-1",
            "u-one-1",
            "u-one-2",
            "u-two-1",
            "u-two-2",
            "u-gamma-deep-1",
        }


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

    def test_combining_with_manifest_now_resolves_each_groups_own_entry(self):
        # REVISED 2026-10-16 (was: "...query_succeeds_resolve_raises") --
        # same partition-aware fix as ':all()''s own equivalent test,
        # applied to ':groups()' (GROUP, any depth): each of the four
        # distinct (named-file, path) groups is already reduced to its
        # own single pointer-selected winner before :manifest() reads
        # it, so pooling the four winners' own entries is not a Rule 1
        # violation -- no longer flagged, resolve() now succeeds.
        results = _flatten_star_finder(
            "$*.files.:groups().:last():manifest()"
        ).resolve()
        assert len(results.results) == 4
        assert results.ambiguous_content_read is False
        assert {r.data["uuid"] for r in results.results} == {
            "u-zero-1",
            "u-one-2",
            "u-two-2",
            "u-gamma-deep-1",
        }

    def test_combining_with_a_field_accessor_now_works(self):
        # narrowed 2026-08-29 -- one value per (named-file, path) group,
        # any depth, including gamma's two-level entry ':all()' cannot
        # reach.
        results = _flatten_star_finder(
            "$*.files.:groups().:last():uuid()"
        ).resolve()
        assert {r.data for r in results.results} == {
            "u-zero-1",
            "u-one-2",
            "u-two-2",
            "u-gamma-deep-1",
        }


#
# alpha has TWO zero-level ("no template") entries directly at its own
# home; beta has only a ONE-level "orders.csv" entry -- proves ':home()'
# traversal pools zero-level candidates ACROSS named-files (not just
# within one, which TestHomeAsAZeroLevelSelector already covers), and
# that a named-file with no zero-level registration at all is correctly
# excluded/contributes nothing -- both to the plain pooled-candidate
# shape and to the ':home():definition()' filtered-lookup shape below.
#
HOME_STAR_ALPHA_HOME = "inputs/named_files/alpha"
HOME_STAR_ALPHA_MANIFEST = [
    {
        "file": "inputs/named_files/alpha/aaa.csv",
        "file_home": "inputs/named_files/alpha",
        "uuid": "u-alpha-zero-1",
        "time": "2026-01-01T00:00:00+00:00",
    },
    {
        "file": "inputs/named_files/alpha/bbb.csv",
        "file_home": "inputs/named_files/alpha",
        "uuid": "u-alpha-zero-2",
        "time": "2026-01-03T00:00:00+00:00",
    },
]
HOME_STAR_BETA_HOME = "inputs/named_files/beta"
HOME_STAR_BETA_MANIFEST = [
    {
        "file": "inputs/named_files/beta/orders.csv/ccc.csv",
        "file_home": "inputs/named_files/beta/orders.csv",
        "uuid": "u-beta-one-level",
        "time": "2026-01-02T00:00:00+00:00",
    },
]
HOME_STAR_BY_NAME = {
    "alpha": (HOME_STAR_ALPHA_HOME, HOME_STAR_ALPHA_MANIFEST),
    "beta": (HOME_STAR_BETA_HOME, HOME_STAR_BETA_MANIFEST),
}


def _home_star_finder(reference: str) -> FilesReferenceFinder3:
    return _finder(
        reference, HOME_STAR_ALPHA_HOME, HOME_STAR_ALPHA_MANIFEST, by_name=HOME_STAR_BY_NAME
    )


class TestStarTraversalHome:
    # bare ':home()' as name_one's entire content during '*' traversal --
    # added 2026-08-27 (FILES '*' traversal generalization bucket-list
    # entry, gap #1: ":home()" + "'*'" traversal did not exist at all,
    # raising "Does not yet support :home() as a name_one path segment").
    # Not partitioned (mirrors the plain-path POOL branch immediately
    # above, just with an empty pattern instead of a compiled one) -- a
    # terminal pointer picks ONE overall winner by time across every
    # named-file's own zero-level candidates, it does not pick one winner
    # per named-file (':all()' already does that).
    def test_last_pools_zero_level_candidates_across_named_files(self):
        results = _home_star_finder("$*.files.:home().:last()").query()
        assert results.uuids == ["u-alpha-zero-2"]

    def test_a_named_file_with_no_zero_level_entry_contributes_nothing(self):
        # beta's only entry is one level deep -- must never appear,
        # regardless of pointer.
        results = _home_star_finder("$*.files.:home().:first()").query()
        assert "u-beta-one-level" not in results.uuids
        assert results.uuids == ["u-alpha-zero-1"]

    def test_with_no_name_three_dedupes_to_zero_level_file_homes_only(self):
        results = _home_star_finder("$*.files.:home()").query()
        assert results.files == [HOME_STAR_ALPHA_HOME]

    def test_chaining_anything_other_than_definition_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _home_star_finder("$*.files.:home():uuid().:last()").query()

    def test_worksheet_marker_is_rejected(self):
        # not-yet-supported sweep #6, 2026-10-20: '#worksheet' means
        # content from exactly one specific XLSX file -- '*' traversal
        # matches across every named-file by definition, so this is a
        # settled rejection, not a pending gap.
        with pytest.raises(ReferenceException3):
            _home_star_finder("$*.files.*#Summary.:last()").query()


class TestStarTraversalDefinition:
    # bare ':definition()' during '*' traversal (gap #2) and ':home()'
    # with ':definition()' chained onto it (gap #3, "does not yet support
    # functions attached directly to name_one for '*' traversal" even
    # once #1/#2 individually work) -- both added 2026-08-27, same
    # bucket-list entry as TestStarTraversalHome above. Neither takes
    # name_three -- definition.json is never versioned, so there is
    # nothing left to narrow once a named-file is matched.
    def test_bare_definition_gives_one_result_per_named_file(self):
        results = _home_star_finder("$*.files.:definition()").query()
        assert set(results.files) == {
            pathu.resep(f"{HOME_STAR_ALPHA_HOME}/definition.json"),
            pathu.resep(f"{HOME_STAR_BETA_HOME}/definition.json"),
        }
        assert all(r.uuid is None for r in results.results)

    def test_bare_definition_flags_ambiguous_content_read_when_plural(self):
        # Rule 1 (manifest_field_functions_proposal.md): resolving full
        # METADATA_FILE content for more than one entity at once is
        # illegal -- more than one named-file's own definition.json is
        # exactly that case, same as :manifest() already flags.
        results = _home_star_finder("$*.files.:definition()").query()
        assert results.ambiguous_content_read is True

    def test_home_prefixed_definition_filters_to_zero_level_named_files_only(self):
        # beta has no zero-level registration -- must be excluded, even
        # though it has its own definition.json like any named-file would.
        results = _home_star_finder("$*.files.:home():definition()").query()
        assert results.files == [pathu.resep(f"{HOME_STAR_ALPHA_HOME}/definition.json")]
        assert results.ambiguous_content_read is False

    def test_bare_definition_combined_with_name_three_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _home_star_finder("$*.files.:definition().:last()").query()

    def test_home_prefixed_definition_combined_with_name_three_is_rejected(
        self,
    ):
        with pytest.raises(ReferenceException3):
            _home_star_finder("$*.files.:home():definition().:last()").query()

    def test_resolve_reads_each_named_files_own_definition_bytes(self, tmp_path):
        # manifest file_home values must actually match the tmp_path
        # homes below (unlike HOME_STAR_ALPHA_MANIFEST's hardcoded
        # "inputs/named_files/..." strings) -- ':home()' filters by real
        # file_home-vs-home matching, not by name alone.
        alpha_home = tmp_path / "alpha"
        alpha_home.mkdir()
        (alpha_home / "definition.json").write_bytes(b'{"on_arrival": "go"}')
        alpha_manifest = [
            {
                "file": str(alpha_home / "aaa.csv"),
                "file_home": str(alpha_home),
                "uuid": "u-alpha-zero-1",
            }
        ]
        beta_home = tmp_path / "beta"
        beta_home.mkdir()
        (beta_home / "definition.json").write_bytes(b'{"on_arrival": null}')
        beta_manifest = [
            {
                "file": str(beta_home / "orders.csv" / "ccc.csv"),
                "file_home": str(beta_home / "orders.csv"),
                "uuid": "u-beta-one-level",
            }
        ]
        by_name = {
            "alpha": (str(alpha_home), alpha_manifest),
            "beta": (str(beta_home), beta_manifest),
        }
        finder = _finder(
            "$*.files.:home():definition()", str(alpha_home), [], by_name=by_name
        )
        results = finder.resolve()
        assert len(results.results) == 1
        assert results.results[0].data == b'{"on_arrival": "go"}'

    def test_on_arrival_predicate_filters_to_named_files_that_have_it_set(self):
        # the generic predicate-argument filtering mechanism (added
        # 2026-10-17, closing the deferred-work bucket list's own
        # "Predicate-argument field accessors" entry) -- its own
        # motivating worked example:
        # "$*.files.:home():definition(:on_arrival(:not_none()))" --
        # "which named-files have on_arrival set." Both alpha and beta
        # are zero-level-eligible (isolating the predicate's own effect
        # from the pre-existing ':home()' filter, already covered by
        # test_home_prefixed_definition_filters_to_zero_level_named_
        # files_only above) -- only alpha has on_arrival configured.
        results = _finder(
            "$*.files.:home():definition(:on_arrival(:not_none()))",
            HOME_STAR_ALPHA_HOME,
            HOME_STAR_ALPHA_MANIFEST,
            by_name=HOME_STAR_BY_NAME,
            definitions={
                "alpha": {
                    "on_arrival": {
                        "named_paths_name": "validations",
                        "run_method": "fast_forward",
                    }
                },
                "beta": {"on_arrival": None},
            },
        ).query()
        # content resolution itself (reading the real definition.json
        # bytes for a survivor) is already proven by the pre-existing
        # test_resolve_reads_each_named_files_own_definition_bytes above
        # -- this test is only about WHICH named-files survive the new
        # predicate filter.
        assert results.files == [pathu.resep(f"{HOME_STAR_ALPHA_HOME}/definition.json")]
        assert results.ambiguous_content_read is False

    def test_on_arrival_predicate_with_no_survivors_gives_empty_results(self):
        results = _finder(
            "$*.files.:home():definition(:on_arrival(:not_none()))",
            HOME_STAR_ALPHA_HOME,
            HOME_STAR_ALPHA_MANIFEST,
            by_name=HOME_STAR_BY_NAME,
            definitions={"alpha": {"on_arrival": None}, "beta": {"on_arrival": None}},
        ).query()
        assert results.results == []

    def test_on_arrival_predicate_combined_with_name_three_is_not_yet_supported(
        self,
    ):
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.files.:home():definition(:on_arrival(:not_none())).:last()",
                HOME_STAR_ALPHA_HOME,
                HOME_STAR_ALPHA_MANIFEST,
                by_name=HOME_STAR_BY_NAME,
                definitions={"alpha": {"on_arrival": {"a": 1}}},
            ).query()

    def test_on_arrival_predicate_survivor_resolves_its_real_definition_bytes(
        self, tmp_path
    ):
        # end-to-end: the fake describer drives the FILTER decision
        # (which named-files survive), a real on-disk definition.json
        # drives the actual RESOLVED content for the survivor -- two
        # independent fakes, same as production (describer.get_config()
        # for the check, a real file read for the content).
        alpha_home = tmp_path / "alpha"
        alpha_home.mkdir()
        (alpha_home / "definition.json").write_bytes(
            b'{"on_arrival": {"named_paths_name": "validations", '
            b'"run_method": "fast_forward"}}'
        )
        alpha_manifest = [
            {
                "file": str(alpha_home / "aaa.csv"),
                "file_home": str(alpha_home),
                "uuid": "u-alpha-zero-1",
            }
        ]
        beta_home = tmp_path / "beta"
        beta_home.mkdir()
        (beta_home / "definition.json").write_bytes(b'{"on_arrival": null}')
        beta_manifest = [
            {
                "file": str(beta_home / "bbb.csv"),
                "file_home": str(beta_home),
                "uuid": "u-beta-zero-1",
            }
        ]
        by_name = {
            "alpha": (str(alpha_home), alpha_manifest),
            "beta": (str(beta_home), beta_manifest),
        }
        results = _finder(
            "$*.files.:home():definition(:on_arrival(:not_none()))",
            str(alpha_home),
            [],
            by_name=by_name,
            definitions={
                "alpha": {
                    "on_arrival": {
                        "named_paths_name": "validations",
                        "run_method": "fast_forward",
                    }
                },
                "beta": {"on_arrival": None},
            },
        ).resolve()
        assert len(results.results) == 1
        assert results.results[0].data == (
            b'{"on_arrival": {"named_paths_name": "validations", '
            b'"run_method": "fast_forward"}}'
        )


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

    def test_all_combined_with_manifest_now_resolves_each_groups_own_entry(self):
        # used to raise ("does not yet support combining ':all()'/
        # ':groups()' grouping with :manifest()") -- fixed 2026-10-16,
        # see the "'*'-traversal content-accessor guards" bucket-list
        # entry. Each file_home group is already independently reduced
        # to exactly one candidate by its own ':last()' before
        # :manifest() ever reads it, the same "several groups, each
        # already pointer-reduced" shape CSVPATHS already supports --
        # not a Rule 1 violation, so this is no longer flagged as an
        # ambiguous content read either.
        results = _finder(
            "$alpha.files.:all().:last():manifest()", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert {r.data["uuid"] for r in results.results} == {"u-zero-1", "u-one-2"}

    def test_all_combined_with_a_range_is_rejected(self):
        # split into its own check 2026-09-25 -- used to raise the SAME
        # error as the :manifest() case above (a confusing "combining
        # with :manifest()" message even though no :manifest() is
        # present here at all, confirmed live before this fix -- see the
        # bucket list). Still rejected, not built: the range would apply
        # to the POOLED candidate list before partitioning, an
        # ambiguous reading (last N overall vs. last N per group) with
        # no driving use case to settle it, matching RESULTS' own
        # identical rejection.
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.files.:all().:from(-1)", ALPHA_HOME, ALPHA_MANIFEST
            ).query()

    def test_all_combined_with_a_field_accessor_gives_one_value_per_group(self):
        # narrowed 2026-08-29 -- unlike ':manifest()' (a whole-resource
        # read, still Rule 1 territory), a field accessor is poolable:
        # each file_home group's own pointer-reduced candidate
        # contributes its own field value. Matches
        # ResultsReferenceFinder3's own already-settled precedent for
        # the identical shape (a field accessor riding alongside a
        # pointer during GROUP-mode partitioning is not rejected there).
        results = _finder(
            "$alpha.files.:all().:last():uuid()", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert {r.data for r in results.results} == {"u-zero-1", "u-one-2"}


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

    # a literal prefix BEFORE ':flatten()' -- a THIRD shape, e.g.
    # "2025/:flatten()/:name('orders.csv')" ("any orders.csv below 2025,
    # at any depth in between") -- used to raise unconditionally here
    # (deferred 2026-08-12); BUILT 2026-08-27, see TestPrefixedFlatten
    # below for its own dedicated fixture/coverage.


PREFIXED_FLATTEN_HOME = "inputs/named_files/vault"
PREFIXED_FLATTEN_MANIFEST = [
    {
        "file": "inputs/named_files/vault/2025/orders.csv/aaa.csv",
        "file_home": "inputs/named_files/vault/2025/orders.csv",
        "uuid": "u-2025-direct",
    },
    {
        "file": "inputs/named_files/vault/2025/q1/orders.csv/bbb.csv",
        "file_home": "inputs/named_files/vault/2025/q1/orders.csv",
        "uuid": "u-2025-q1",
    },
    {
        "file": "inputs/named_files/vault/2026/orders.csv/ccc.csv",
        "file_home": "inputs/named_files/vault/2026/orders.csv",
        "uuid": "u-2026-direct",
    },
    {
        "file": "inputs/named_files/vault/2025/returns.csv/ddd.csv",
        "file_home": "inputs/named_files/vault/2025/returns.csv",
        "uuid": "u-2025-returns",
    },
    {
        "file": "inputs/named_files/vault/orders.csv/eee.csv",
        "file_home": "inputs/named_files/vault/orders.csv",
        "uuid": "u-no-prefix",
    },
]


class TestPrefixedFlatten:
    # a literal/'*'/:name(...) PREFIX, THEN ':flatten()', THEN an
    # OPTIONAL literal/'*'/:name(...) SUFFIX -- built 2026-08-27, closing
    # the gap deferred 2026-08-12 (David: "any orders.csv below 2025, at
    # any depth in between"). PREFIXED_FLATTEN_MANIFEST has "orders.csv"
    # directly under "2025" (zero-segment gap), under "2025/q1" (one-
    # segment gap, proving "any depth in between"), under "2026" (wrong
    # prefix -- must be excluded), "returns.csv" under "2025" (right
    # prefix, wrong suffix -- must be excluded), and "orders.csv" with
    # no prefix at all (must be excluded).
    def test_matches_zero_and_nonzero_gap_but_not_wrong_prefix_or_suffix(self):
        results = _finder(
            '$vault.files.2025/:flatten()/:name("orders.csv")',
            PREFIXED_FLATTEN_HOME,
            PREFIXED_FLATTEN_MANIFEST,
        ).query()
        assert set(results.files) == {
            "inputs/named_files/vault/2025/orders.csv",
            "inputs/named_files/vault/2025/q1/orders.csv",
        }

    def test_last_picks_the_last_matching_entry_in_array_order(self):
        results = _finder(
            '$vault.files.2025/:flatten()/:name("orders.csv").:last()',
            PREFIXED_FLATTEN_HOME,
            PREFIXED_FLATTEN_MANIFEST,
        ).query()
        assert results.uuids == ["u-2025-q1"]

    def test_first_picks_the_first_matching_entry_in_array_order(self):
        results = _finder(
            '$vault.files.2025/:flatten()/:name("orders.csv").:first()',
            PREFIXED_FLATTEN_HOME,
            PREFIXED_FLATTEN_MANIFEST,
        ).query()
        assert results.uuids == ["u-2025-direct"]

    def test_missing_suffix_means_prefix_then_any_depth_no_further_constraint(
        self,
    ):
        # "2025/:flatten()" alone -- prefix-only, no suffix anchor --
        # matches every distinct file_home under "2025" at any depth,
        # both orders.csv and returns.csv, but nothing under "2026" or
        # with no prefix at all.
        results = _finder(
            "$vault.files.2025/:flatten()", PREFIXED_FLATTEN_HOME, PREFIXED_FLATTEN_MANIFEST
        ).query()
        assert set(results.files) == {
            "inputs/named_files/vault/2025/orders.csv",
            "inputs/named_files/vault/2025/q1/orders.csv",
            "inputs/named_files/vault/2025/returns.csv",
        }

    def test_prefixed_flatten_rejects_an_argument(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$vault.files.2025/:flatten("x")/:name("orders.csv")',
                PREFIXED_FLATTEN_HOME,
                PREFIXED_FLATTEN_MANIFEST,
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

    def test_home_in_name_three_position_now_raises(self):
        # ':home()' no longer has an ordinary field-accessor job at all
        # (split 2026-08-26 -- see :file_home() for FILES' own share of
        # that retired job) -- it keeps only the bare, name_one, zero-
        # level placeholder role, so using it in name_three now raises
        # via POSITIONS/_check_position, rather than silently reading
        # "file_home" the way it used to.
        with pytest.raises(ReferenceException3):
            _finder(
                '$homer.files.:name("orders.csv").:first():home()',
                HOME_TEST_HOME,
                HOME_TEST_MANIFEST,
            ).query()

    def test_file_home_in_name_three_position_works(self):
        # :file_home() is the retired job's new home.
        results = _finder(
            '$homer.files.:name("orders.csv").:first():file_home()',
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


REGEX_HOME = "inputs/named_files/alpha"
REGEX_MANIFEST = [
    {
        "file": "inputs/named_files/alpha/orders/2027/EMEA/aaa.csv",
        "file_home": "inputs/named_files/alpha/orders/2027/EMEA",
        "uuid": "match-1",
    },
    {
        "file": "inputs/named_files/alpha/orders/2028/EMEA/bbb.csv",
        "file_home": "inputs/named_files/alpha/orders/2028/EMEA",
        "uuid": "match-2",
    },
    {
        "file": "inputs/named_files/alpha/orders/1999/EMEA/ccc.csv",
        "file_home": "inputs/named_files/alpha/orders/1999/EMEA",
        "uuid": "no-match-1",
    },
]


class TestRegexPathSegment:
    # ':regex(...)' as a name_one path segment -- added 2026-09-23,
    # closing the deferred-work bucket list gap of the same name,
    # confirmed 2026-09-23 to apply to FILES too (David). Mechanically
    # the same capability ':name(/pattern/)' already has (matches a
    # TEMPLATE segment by pattern), just spelled without the ':name()'
    # wrapper -- shares _compile_path_pattern() with RESULTS (see
    # test_results_reference_finder_3.py's own TestRegexPathSegment for
    # the RESULTS-side tests and the fuller design writeup).
    def test_prefixed_regex_matches_the_template_segment(self):
        results = _finder(
            '$alpha.files.orders/:regex("202[6789]")/EMEA.:last()',
            REGEX_HOME,
            REGEX_MANIFEST,
        ).query()
        # both "2027" and "2028" match the pattern -- every matching
        # version pools together (no ':all()'/':groups()' grouping here)
        # and ':last()' reduces to the single overall latest.
        assert results.uuids == ["match-2"]

    def test_prefixed_regex_with_no_name_three_gives_matching_file_homes(self):
        # no name_three -- dedupes to directory-level results (uuid=None),
        # same convention every other name_three-less FILES query uses.
        results = _finder(
            '$alpha.files.orders/:regex("202[6789]")/EMEA', REGEX_HOME, REGEX_MANIFEST
        ).query()
        assert set(results.files) == {
            "inputs/named_files/alpha/orders/2027/EMEA",
            "inputs/named_files/alpha/orders/2028/EMEA",
        }

    def test_invalid_pattern_is_rejected_eagerly(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$alpha.files.orders/:regex("[unclosed")/EMEA.:last()',
                REGEX_HOME,
                REGEX_MANIFEST,
            ).query()


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


class TestBareUuidLookup:
    # bare ':uuid("u-returns-1")' -- added 2026-10-18, the compendium's
    # own worked example ("select a registered version of an acme file
    # by its UUID"). Same SELECTOR_WHEN_ARGUED mechanism :fingerprint()
    # already has (see test_an_argument_in_the_field_accessor_position_
    # is_rejected above for that one's own version of this guard) --
    # the registry-driven dispatch/guard are both shared code, this is
    # the second function to exercise them, not a parallel copy.
    def test_finds_the_matching_version_with_real_path_and_uuid(self):
        results = _finder(
            '$finn.files.:uuid("u-returns-1")', FINGERPRINT_HOME, FINGERPRINT_MANIFEST
        ).query()
        assert results.files == ["inputs/named_files/finn/2025/returns.csv/cccc.csv"]
        assert results.uuids == ["u-returns-1"]

    def test_no_match_gives_empty(self):
        results = _finder(
            '$finn.files.:uuid("nope")', FINGERPRINT_HOME, FINGERPRINT_MANIFEST
        ).query()
        assert results.results == []

    def test_combined_with_name_three_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$finn.files.:uuid("u-returns-1").:last()',
                FINGERPRINT_HOME,
                FINGERPRINT_MANIFEST,
            ).query()

    def test_ordinary_field_accessor_usage_is_unaffected(self):
        # riding alongside a matched version in name_three (its
        # original, pre-existing job, unchanged by this build) still
        # works exactly as before.
        results = _finder(
            '$finn.files.:name("orders.csv").:first():uuid()',
            FINGERPRINT_HOME,
            FINGERPRINT_MANIFEST,
        ).resolve()
        assert results.results[0].data == "u-orders-1"

    def test_an_argument_in_the_field_accessor_position_is_rejected(self):
        # ARG_TYPES now allows a str arg (for the bare lookup form) --
        # confirm it does NOT get silently ignored when :uuid() rides
        # in its ordinary field-accessor position instead (the exact
        # footgun confirmed live before this guard existed).
        with pytest.raises(ReferenceException3):
            _finder(
                '$finn.files.:name("orders.csv").:first():uuid("x")',
                FINGERPRINT_HOME,
                FINGERPRINT_MANIFEST,
            ).query()


TYPE_HOME = "inputs/named_files/finn"
TYPE_MANIFEST = [
    {
        "file": "inputs/named_files/finn/orders.csv/aaaa.csv",
        "file_home": "inputs/named_files/finn/orders.csv",
        "uuid": "u-csv",
        "type": "csv",
    },
    {
        "file": "inputs/named_files/finn/data.xlsx/bbbb.xlsx",
        "file_home": "inputs/named_files/finn/data.xlsx",
        "uuid": "u-xlsx",
        "type": "xlsx",
    },
]

TYPE_PREFIXED_MANIFEST = [
    {
        "file": "inputs/named_files/finn/orders/2026/aaaa.csv",
        "file_home": "inputs/named_files/finn/orders/2026",
        "uuid": "u-2026-csv",
        "type": "csv",
    },
    {
        "file": "inputs/named_files/finn/orders/2027/bbbb.xlsx",
        "file_home": "inputs/named_files/finn/orders/2027",
        "uuid": "u-2027-xlsx",
        "type": "xlsx",
    },
    {
        "file": "inputs/named_files/finn/other/cccc.csv",
        "file_home": "inputs/named_files/finn/other",
        "uuid": "u-other-csv",
        "type": "csv",
    },
]


class TestTypeGate:
    # ':type()' widened 2026-10-18 to accept a string argument, GATE-
    # ing a candidate list in name_one -- compendium 3.9d's own claimed
    # equivalence between the bare and explicit-'*' forms
    # (":type(\"csv\")" == "*:type(\"csv\")"), plus its own worked
    # example (normative_reference_examples.txt line 271, ":flatten():
    # type(\"xlsx\")"). FilesReferenceFinder3.query()'s own literal-
    # root branch previously rejected ANY function chained in name_one
    # unconditionally, at two different checkpoints (confirmed live
    # before this fix) -- see _extract_gate_field_call()'s own
    # docstring for why both exist.
    def test_bare_implied_star_gate(self):
        results = _finder(
            '$finn.files.:type("csv")', TYPE_HOME, TYPE_MANIFEST
        ).query()
        assert results.files == ["inputs/named_files/finn/orders.csv"]

    def test_explicit_star_gate_is_the_same_mechanism(self):
        # compendium 3.9d's own claimed equivalence, confirmed live --
        # both forms must give the identical answer.
        bare = _finder(
            '$finn.files.:type("csv")', TYPE_HOME, TYPE_MANIFEST
        ).query()
        explicit = _finder(
            '$finn.files.*:type("csv")', TYPE_HOME, TYPE_MANIFEST
        ).query()
        assert bare.files == explicit.files

    def test_flatten_gate(self):
        results = _finder(
            '$finn.files.:flatten():type("xlsx")', TYPE_HOME, TYPE_MANIFEST
        ).query()
        assert results.files == ["inputs/named_files/finn/data.xlsx"]

    def test_prefixed_bare_gate(self):
        results = _finder(
            '$finn.files.orders/:type("csv")', TYPE_HOME, TYPE_PREFIXED_MANIFEST
        ).query()
        assert results.files == ["inputs/named_files/finn/orders/2026"]

    def test_prefixed_explicit_star_gate_is_the_same_mechanism(self):
        bare = _finder(
            '$finn.files.orders/:type("csv")', TYPE_HOME, TYPE_PREFIXED_MANIFEST
        ).query()
        explicit = _finder(
            '$finn.files.orders/*:type("csv")', TYPE_HOME, TYPE_PREFIXED_MANIFEST
        ).query()
        assert bare.files == explicit.files

    def test_no_match_gives_empty(self):
        results = _finder(
            '$finn.files.:type("nope")', TYPE_HOME, TYPE_MANIFEST
        ).query()
        assert results.results == []

    def test_composes_with_name_three_pointer(self):
        results = _finder(
            '$finn.files.:type("csv").:last()', TYPE_HOME, TYPE_MANIFEST
        ).query()
        assert results.uuids == ["u-csv"]

    def test_a_field_accessor_with_no_name_one_position_still_raises(self):
        # :named_file_name() accepts a string argument (widened for
        # RESULTS' own GATE need, a separate PR) but its own FILES
        # POSITIONS entry is still NAME_THREE-only -- confirms the new
        # extraction is scoped to functions that actually declare
        # NAME_ONE legal for FILES, not just any argument-accepting
        # field accessor.
        with pytest.raises(ReferenceException3):
            _finder(
                '$finn.files.:named_file_name("orders")', TYPE_HOME, TYPE_MANIFEST
            ).query()


STATUS_LEDGER = [
    {
        "named_file_name": "orders",
        "status": "Registration failed",
        "uuid": "fail-1",
        "file_path": None,
        "origin_path": "/tmp/orders1.csv",
    },
    {
        "named_file_name": "orders",
        "status": None,
        "uuid": "ok-1",
        "file_path": "inputs/named_files/orders/orders.csv/aaaa.csv",
    },
    {
        "named_file_name": "invoices",
        "status": "Registration failed",
        "uuid": "fail-2",
        "file_path": None,
        "origin_path": "/tmp/invoices1.csv",
    },
]


class TestStatusGate:
    # ':status()' widened 2026-10-18 to also cover FILES -- the global
    # arrivals ledger's own "status" field (a failure message),
    # confirmed live by tracing the real registration code
    # (file_manager.py's own "mdata.status = 'Registration failed'",
    # written only to files_root_manifest, never a per-name manifest).
    # normative_reference_examples.txt's own worked example: "select
    # named-files registrations for orders that failed" --
    # "$*.files.:status(\"Registration failed\"):named_file_name(
    # \"orders\")". Both the '*' form AND the literal-root form are
    # built -- David confirmed the literal form is at least as common
    # an operational need ("if you were inspecting a run that should
    # have happened overnight you would know what status you were
    # looking for... we know those high risk files by name").
    def test_star_root_matches_the_normative_example(self):
        results = _finder(
            '$*.files.:status("Registration failed"):named_file_name("orders")',
            TYPE_HOME,
            [],
            ledger=STATUS_LEDGER,
        ).query()
        assert results.uuids == ["fail-1"]
        # a failed registration never got a real file_path -- falls
        # back to origin_path, the one real path it does carry.
        assert results.files == ["/tmp/orders1.csv"]

    def test_star_root_bare_status_alone(self):
        results = _finder(
            '$*.files.:status("Registration failed")', TYPE_HOME, [], ledger=STATUS_LEDGER
        ).query()
        assert sorted(results.uuids) == ["fail-1", "fail-2"]

    def test_literal_root_is_just_as_real_a_need(self):
        results = _finder(
            '$orders.files.:status("Registration failed")',
            TYPE_HOME,
            [],
            ledger=STATUS_LEDGER,
        ).query()
        assert results.uuids == ["fail-1"]

    def test_literal_root_combined_with_named_file_name_chain(self):
        results = _finder(
            '$orders.files.:status("Registration failed"):named_file_name("orders")',
            TYPE_HOME,
            [],
            ledger=STATUS_LEDGER,
        ).query()
        assert results.uuids == ["fail-1"]

    def test_literal_root_excludes_other_names(self):
        # "invoices" also has a failed registration, but this query is
        # scoped to "orders" -- confirms the literal root genuinely
        # narrows, not just filters client-side afterward.
        results = _finder(
            '$invoices.files.:status("Registration failed"):named_file_name("orders")',
            TYPE_HOME,
            [],
            ledger=STATUS_LEDGER,
        ).query()
        assert results.results == []

    def test_no_match_gives_empty(self):
        results = _finder(
            '$*.files.:status("nope")', TYPE_HOME, [], ledger=STATUS_LEDGER
        ).query()
        assert results.results == []

    def test_name_three_is_rejected_star_root(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$*.files.:status("Registration failed").:last()',
                TYPE_HOME,
                [],
                ledger=STATUS_LEDGER,
            ).query()

    def test_name_three_is_rejected_literal_root(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$orders.files.:status("Registration failed").:last()',
                TYPE_HOME,
                [],
                ledger=STATUS_LEDGER,
            ).query()

    def test_an_uncited_combination_still_raises_clearly(self):
        # ':status()' is genuinely ledger-only -- chaining it onto
        # ':flatten()' (reading the PER-NAME manifest instead) is not
        # a shape any worked example asks for. Confirms the new KEY-
        # presence guard in _extract_gate_field_call() -- without it,
        # this would have silently matched nothing instead of raising
        # (confirmed live before adding that guard).
        with pytest.raises(ReferenceException3):
            _finder(
                '$finn.files.:flatten():status("x")',
                TYPE_HOME,
                TYPE_MANIFEST,
                ledger=STATUS_LEDGER,
            ).query()

    def test_type_gate_is_unaffected(self):
        # regression check -- the new KEY-presence guard added for
        # ':status()' must not affect ':type()'s own, already-working
        # GATE.
        results = _finder(
            '$finn.files.:type("csv")', TYPE_HOME, TYPE_MANIFEST
        ).query()
        assert results.files == ["inputs/named_files/finn/orders.csv"]


class TestLiteralNameThreeBody:
    # a literal name_three body -- e.g. "orders.aaaa" -- names the
    # FINGERPRINT of the version, per compendium 3.19b/3.20. Added
    # 2026-09-22, closing the deferred-work bucket list gap of the same
    # name. Distinct from the bare ':fingerprint("...")' lookup above:
    # this searches only within the already-name_one-matched candidates
    # (here, just "orders.csv"'s own versions), not the whole named-
    # file's manifest.
    def test_matches_the_named_versions_own_fingerprint(self):
        # ':name("orders.csv")' rather than a bare "orders" path segment
        # -- the file_home's own last segment is "orders.csv", and a
        # literal dot cannot appear in a bare PATH_SEGMENT (it is the
        # name_one/name_three separator), same reason :name(...) exists
        # at all -- see _compile_path_pattern()'s own docstring.
        results = _finder(
            '$finn.files.:name("orders.csv").aaaa', FINGERPRINT_HOME, FINGERPRINT_MANIFEST
        ).query()
        assert results.files == ["inputs/named_files/finn/orders.csv/aaaa.csv"]
        assert results.uuids == ["u-orders-1"]

    def test_no_match_gives_empty(self):
        results = _finder(
            '$finn.files.:name("orders.csv").zzzz', FINGERPRINT_HOME, FINGERPRINT_MANIFEST
        ).query()
        assert results.results == []

    def test_scoped_to_the_matched_name_one_not_the_whole_named_file(self):
        # "cccc" is a real fingerprint in FINGERPRINT_MANIFEST, but it
        # belongs to "2025/returns.csv", not "orders.csv" -- unlike the
        # bare ':fingerprint("cccc")' lookup (which searches every
        # file_home), a literal name_three body only searches within
        # name_one's own already-matched candidates.
        results = _finder(
            '$finn.files.:name("orders.csv").cccc', FINGERPRINT_HOME, FINGERPRINT_MANIFEST
        ).query()
        assert results.results == []

    def test_combined_with_a_manifest_call(self):
        # not-yet-supported sweep #4, 2026-10-20: the literal body
        # already reduces to one candidate before any function runs --
        # falls through into the ordinary single-candidate ':manifest()'
        # machinery, same as a real pointer's own one-candidate
        # reduction already does.
        results = _finder(
            '$finn.files.:name("orders.csv").aaaa:manifest()',
            FINGERPRINT_HOME,
            FINGERPRINT_MANIFEST,
        ).resolve()
        assert results.results[0].uuid == "u-orders-1"
        assert results.results[0].data["fingerprint"] == "aaaa"

    def test_combined_with_a_field_accessor(self):
        results = _finder(
            '$finn.files.:name("orders.csv").aaaa:fingerprint()',
            FINGERPRINT_HOME,
            FINGERPRINT_MANIFEST,
        ).resolve()
        assert results.results[0].data == "aaaa"

    def test_combined_with_trailing_functions_no_match_gives_empty(self):
        results = _finder(
            '$finn.files.:name("orders.csv").zzzz:manifest()',
            FINGERPRINT_HOME,
            FINGERPRINT_MANIFEST,
        ).query()
        assert results.results == []


class TestBareManifestFieldAccessor:
    # ':manifest():uuid()'/':manifest():time()' -- added 2026-08-28,
    # David's own worked examples ("get uuids from all registrations,"
    # "get all acme registration uuids"). Unlike the ordinary field-
    # accessor position (riding beside a real pointer in name_three,
    # exactly one already-selected entity), this maps the chained field
    # over EVERY entry in the matched named-file's own manifest.json --
    # a genuinely different shape, not a syntax variant of the same
    # thing.
    def test_query_gives_one_result_per_manifest_entry(self):
        results = _finder(
            "$alpha.files.:manifest():uuid()", ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert set(results.uuids) == {"u-zero-1", "u-one-1", "u-one-2"}

    def test_resolve_gives_the_field_value_per_entry_not_the_whole_entry(self):
        results = _finder(
            "$alpha.files.:manifest():uuid()", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert {r.data for r in results.results} == {
            "u-zero-1",
            "u-one-1",
            "u-one-2",
        }
        # every value is the plain uuid string, not the whole entry dict
        assert all(isinstance(r.data, str) for r in results.results)

    def test_single_entry_manifest_matches_davids_own_worked_example(self):
        # the exact syntax from David's own worked examples
        # ("$acme.files.:manifest():uuid()" -- get all acme registration
        # uuids).
        results = _finder(
            "$acme.files.:manifest():uuid()", TEMPLATED_HOME, TEMPLATED_MANIFEST
        ).resolve()
        assert [r.data for r in results.results] == ["u-q2-1"]

    def test_a_different_manifest_field_works_the_same_way(self):
        # confirms this is a general mechanism, not hardcoded to :uuid()
        # specifically -- STAR_ALPHA_MANIFEST's entries have a "time"
        # field too.
        results = _finder(
            "$alpha.files.:manifest():time()", STAR_ALPHA_HOME, STAR_ALPHA_MANIFEST
        ).resolve()
        assert {r.data for r in results.results} == {
            "2026-01-01T00:00:00+00:00",
            "2026-01-02T00:00:00+00:00",
            "2026-01-03T00:00:00+00:00",
        }

    def test_combined_with_name_three_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.files.:manifest():uuid().:last()", ALPHA_HOME, ALPHA_MANIFEST
            ).query()

    def test_more_than_one_chained_function_is_not_recognized_here(self):
        # falls through to the ordinary "functions attached directly to
        # name_one" rejection -- picking one field per entry from more
        # than one chained accessor at once is not a shape any worked
        # example has asked for.
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.files.:manifest():uuid():time()", ALPHA_HOME, ALPHA_MANIFEST
            ).query()

    def test_chaining_a_pointer_is_not_recognized_here(self):
        # ':last()' is a POINTER, not a registered field accessor
        # (SOURCE is None), so this bare-manifest-FIELD mechanism does
        # not match it -- it falls through to the dedicated pointer-
        # before-manifest branch instead (TestManifestPointerSymmetry,
        # below), which resolves it correctly rather than raising.
        # Previously (before the 2026-10-16 symmetry fix) that branch
        # did not exist, so this same reference used to raise here.
        results = _finder(
            "$alpha.files.:manifest():last()", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert results.results[0].data == ALPHA_MANIFEST[-1]

    def test_the_ordinary_name_three_field_accessor_position_still_works(self):
        # David: narrowing to one version via :name(...)+pointer, then
        # reading :uuid() in name_three, is a different, equally valid
        # way to reach a uuid -- this new shape does not replace or
        # touch it.
        results = _finder(
            '$alpha.files.:name("one.csv").:first():uuid()', ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert results.results[0].data == "u-one-1"


class TestNameOneNarrowedManifestCall:
    # issue #410 -- David's own exact repro ($food.files.:name(
    # "food.csv"):manifest()) raised "does not yet support functions
    # attached directly to name_one." Unlike TestBareManifestField
    # Accessor above (a fully-bare ':manifest()', no narrowing prefix
    # at all) or TestManifestPointerSymmetry below (a pointer
    # alongside ':manifest()', reducing to exactly ONE entry), this is
    # a REAL narrowing prefix (':name(...)'/'*'/etc.) with no pointer
    # -- maps the manifest ENTRY (not a field) over every candidate
    # the prefix matches, analogous to _bare_manifest_field_call()'s
    # own "map a field over every entry" shape but with no field.
    def test_name_then_manifest_maps_the_entry_over_matching_candidates(self):
        # "one.csv" has two of alpha's three entries.
        results = _finder(
            '$alpha.files.:name("one.csv"):manifest()', ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert {r.uuid for r in results.results} == {"u-one-1", "u-one-2"}
        assert {
            r.data["uuid"] if isinstance(r.data, dict) else None
            for r in results.results
        } == {"u-one-1", "u-one-2"}

    def test_query_gives_one_result_per_matching_candidate(self):
        results = _finder(
            '$alpha.files.:name("one.csv"):manifest()', ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert {r.uuid for r in results.results} == {"u-one-1", "u-one-2"}

    def test_resolve_gives_the_whole_entry_not_just_a_field(self):
        results = _finder(
            '$alpha.files.:name("one.csv"):manifest()', ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        matched = next(
            e for e in ALPHA_MANIFEST if e["uuid"] == results.results[0].uuid
        )
        assert results.results[0].data == matched

    def test_explicit_star_before_manifest_is_the_same_shape(self):
        # no ':name(...)' narrowing at all -- every file in the group
        # is a candidate.
        results = _finder(
            "$alpha.files.*:manifest()", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert {r.uuid for r in results.results} == {
            "u-zero-1",
            "u-one-1",
            "u-one-2",
        }

    def test_combined_with_a_pointer_is_still_rejected(self):
        # untested/undecided combination -- no worked example asks
        # for ':manifest()' alongside a pointer AND a narrowing
        # prefix all at once in name_one.
        with pytest.raises(ReferenceException3):
            _finder(
                '$alpha.files.:name("one.csv"):last():manifest()',
                ALPHA_HOME,
                ALPHA_MANIFEST,
            ).query()

    def test_combined_with_worksheet_marker_is_rejected(self):
        # a worksheet read means content (the sheet's own rows), not
        # manifest entries -- not yet supported.
        with pytest.raises(ReferenceException3):
            _finder(
                '$alpha.files.:name("one.csv")#sheet1:manifest()',
                ALPHA_HOME,
                ALPHA_MANIFEST,
            ).query()

    def test_combined_with_name_three_is_still_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$alpha.files.:name("one.csv"):manifest().:last()',
                ALPHA_HOME,
                ALPHA_MANIFEST,
            ).query()


class TestManifestPointerSymmetry:
    # the literal-root_major counterpart to TestGlobalArrivalsLedger
    # OrdinalIndexing's Rule 1b -- a pointer (:first()/:last()/:index(n))
    # riding alongside a bare ':manifest()' in name_one (either order)
    # ordinal-selects one entry out of THIS named-file's own manifest.json,
    # instead of either dumping the whole thing (TestBareManifestField
    # Accessor's own ":manifest():<field>()" shape maps over every entry,
    # a genuinely different mechanism) or raising. Added 2026-10-16,
    # closing a consistency gap with CSVPATHS/RESULTS, which already
    # support this exact bare-chain shape natively.
    def test_last_gives_the_most_recently_registered_version(self):
        results = _finder(
            "$alpha.files.:manifest():last()", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert results.results[0].data == ALPHA_MANIFEST[-1]

    def test_first_gives_the_earliest_registered_version(self):
        results = _finder(
            "$alpha.files.:manifest():first()", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert results.results[0].data == ALPHA_MANIFEST[0]

    def test_index_gives_the_nth_version(self):
        results = _finder(
            "$alpha.files.:manifest():index(1)", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert results.results[0].data == ALPHA_MANIFEST[1]

    def test_negative_index_counts_from_the_end(self):
        results = _finder(
            "$alpha.files.:manifest():index(-1)", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert results.results[0].data == ALPHA_MANIFEST[-1]

    def test_out_of_range_index_gives_no_results(self):
        results = _finder(
            "$alpha.files.:manifest():index(99)", ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert len(results.results) == 0

    def test_pointer_then_manifest_order_also_works(self):
        # ":manifest():last()" means the same as ":last():manifest()" --
        # same order-insensitivity _pointer_before_manifest() already
        # guarantees for the global ledger case.
        results = _finder(
            "$alpha.files.:last():manifest()", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert results.results[0].data == ALPHA_MANIFEST[-1]

    def test_query_gives_the_selected_versions_own_path_and_uuid(self):
        # unlike the global ledger case (Rule 1b, which points at
        # manifest.json itself since the ledger has no other home), this
        # points at the selected VERSION's own file, since that is what
        # this named-file's own manifest entries describe.
        results = _finder(
            "$alpha.files.:manifest():last()", ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert results.results[0].uuid == "u-one-2"
        assert results.results[0].path == ALPHA_MANIFEST[-1]["file"]

    def test_templated_single_entry_manifest_works_the_same_way(self):
        results = _finder(
            "$acme.files.:manifest():last()", TEMPLATED_HOME, TEMPLATED_MANIFEST
        ).resolve()
        assert results.results[0].data == TEMPLATED_MANIFEST[-1]


class TestNameOneBarePointer:
    # compendium 5.21's resolve matrix documents "name_one, file
    # pointer" as legal for FILES ("contents of manifest.json") -- the
    # code never caught up to it (this code predates the spec's own
    # third revision, per David 2026-10-20: "take the spec over the
    # code"). A lone pointer (:first()/:last()/:index(n)) directly in
    # name_one, with NO separating '.' before it and no explicit
    # ':manifest()', is now equivalent to TestManifestPointerSymmetry's
    # own explicit ':manifest()'+pointer shape above. (The normative
    # examples doc's own ':name(...).{dot}:last()' pairs, e.g. lines
    # 866/956-957, have a '.' before the pointer -- confirmed live
    # that parses as a real name_three, a different, already-working
    # shape, NOT what this class covers; see _name_one_pointer's own
    # docstring.)
    def test_bare_last_pools_the_whole_group_same_as_manifest_last(self):
        bare = _finder("$alpha.files.:last()", ALPHA_HOME, ALPHA_MANIFEST).resolve()
        explicit = _finder(
            "$alpha.files.:manifest():last()", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert bare.results[0].data == ALPHA_MANIFEST[-1]
        assert bare.results[0].data == explicit.results[0].data

    def test_explicit_star_before_last_is_the_same_shape_as_bare(self):
        starred = _finder(
            "$alpha.files.*:last()", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert starred.results[0].data == ALPHA_MANIFEST[-1]

    def test_bare_first(self):
        results = _finder("$alpha.files.:first()", ALPHA_HOME, ALPHA_MANIFEST).resolve()
        assert results.results[0].data == ALPHA_MANIFEST[0]

    def test_bare_index(self):
        results = _finder(
            "$alpha.files.:index(1)", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert results.results[0].data == ALPHA_MANIFEST[1]

    def test_name_then_pointer_narrows_to_just_that_file(self):
        # "one.csv" has two of alpha's three entries (u-one-1, u-one-2)
        # -- :last() among just those, not the whole group's own last
        # entry (which here happens to be the same one, so this also
        # exercises :first() to be sure the narrowing is real). No '.'
        # before the pointer -- see this class's own comment on why
        # that matters.
        last = _finder(
            '$alpha.files.:name("one.csv"):last()', ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        first = _finder(
            '$alpha.files.:name("one.csv"):first()', ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert last.results[0].data == ALPHA_MANIFEST[2]
        assert first.results[0].data == ALPHA_MANIFEST[1]

    def test_query_gives_the_selected_entrys_own_path_and_uuid(self):
        results = _finder("$alpha.files.:last()", ALPHA_HOME, ALPHA_MANIFEST).query()
        assert len(results.results) == 1
        assert results.results[0].path == ALPHA_MANIFEST[-1]["file"]
        assert results.results[0].uuid == ALPHA_MANIFEST[-1]["uuid"]

    def test_out_of_range_index_gives_no_results(self):
        results = _finder(
            "$alpha.files.:index(99)", ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert len(results.results) == 0

    def test_two_pointers_together_is_still_rejected(self):
        # two pointers in name_one is nonsensical (normative_reference_
        # examples.txt line 284: "cannot specify the 4th item and the
        # last item at the same time") -- _apply_implied_star() only
        # relocates the LAST path segment (":last()"), leaving
        # ":index(3)" sitting in name_one.path; _name_one_pointer()'s
        # own guard against another pointer-role function still being
        # in .path is what catches this (caught live by this exact
        # test before that guard existed -- it silently returned
        # u-one-2, the group's overall last entry, treating ":index(3)"
        # as a harmless no-op path segment instead of raising).
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.files.:index(3):last()", ALPHA_HOME, ALPHA_MANIFEST
            ).query()

    def test_combined_with_worksheet_marker_is_rejected(self):
        # a worksheet read means content (the sheet's own rows), not a
        # manifest entry -- not yet supported, see this fix's own
        # comment in query() for why it is rejected rather than
        # silently giving the (probably unwanted) manifest entry.
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.files.*#sheet1:last()", ALPHA_HOME, ALPHA_MANIFEST
            ).query()

    def test_combined_with_name_three_is_still_rejected(self):
        # unchanged, pre-existing behavior -- this fix only recognizes
        # the shape when name_three is absent (see _name_one_pointer's
        # own callers); combining both is a separate, untested
        # question no worked example asks for.
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.files.:last().:last()", ALPHA_HOME, ALPHA_MANIFEST
            ).query()


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

    def test_range_combined_with_grouping_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$ranger.files.:all().:from(-1)", RANGE_HOME, RANGE_MANIFEST
            ).query()

    def test_bare_time_window_function_is_gap_1s_flagship_files_example(
        self,
    ):
        # Gap 1 of compendium 6.27/TimeWindowFunction3, added 2026-10-17
        # -- a BARE time-component function riding in the chain, no
        # explicit :from()/:to(). The compendium's own FLAGSHIP worked
        # example for this entire mechanism is literally
        # "$acme.files.:yesterday()" (6.27d/6.27e/6.27f) -- confirmed
        # here with a real version pinned to "yesterday" via
        # DateUtility.OFFSET_DAYS.
        from datetime import date

        from csvpath.util.date_util import DateUtility as daut

        real_now = daut.now()
        daut.OFFSET_DAYS = (date(2026, 1, 4) - real_now.date()).days
        try:
            results = _finder(
                '$ranger.files.:name("orders.csv").:yesterday()',
                RANGE_HOME,
                RANGE_MANIFEST,
            ).query()
            # v2's own time is "2026-01-03T00:00:00+00:00" -- yesterday
            # relative to the pinned "now" of 2026-01-04.
            assert results.uuids == ["v2"]
        finally:
            daut.OFFSET_DAYS = 0

    def test_bare_time_window_combined_with_explicit_range_is_rejected(
        self,
    ):
        with pytest.raises(ReferenceException3):
            _finder(
                '$ranger.files.:name("orders.csv").:yesterday():from(1)',
                RANGE_HOME,
                RANGE_MANIFEST,
            ).query()

    def test_time_window_function_nested_anchor_also_works_for_files(self):
        # Gap 2 of compendium 6.27/TimeWindowFunction3 (added 2026-10-17)
        # -- confirmed live, not just assumed from the shared mechanism,
        # that it actually reaches FILES (the shared _apply_manifest_
        # date_range()/_range_bound() widening lives in the common
        # ReferenceFinder3 base, but FILES' own dispatch sites needed
        # their own from_is_date/to_is_date widening too). Pins "now" to
        # 2026-01-04 (v3's own arrival time) via DateUtility.OFFSET_DAYS.
        from datetime import date

        from csvpath.util.date_util import DateUtility as daut

        real_now = daut.now()
        daut.OFFSET_DAYS = (date(2026, 1, 4) - real_now.date()).days
        try:
            # :year() -> [2026-01-01, 2026-12-31] -- every version in
            # RANGE_MANIFEST is in January 2026, all kept.
            results = _finder(
                '$ranger.files.:name("orders.csv").:from(:year())',
                RANGE_HOME,
                RANGE_MANIFEST,
            ).query()
            assert results.uuids == ["v0", "v1", "v2", "v3", "v4"]
            # :before(:today()) -- excludes the WHOLE of "today"
            # (2026-01-04, v3's own day) and everything after it.
            results = _finder(
                '$ranger.files.:name("orders.csv").:before(:today())',
                RANGE_HOME,
                RANGE_MANIFEST,
            ).query()
            assert results.uuids == ["v0", "v1", "v2"]
        finally:
            daut.OFFSET_DAYS = 0


class TestDirectionFunctions:
    # ':before()'/':after()' -- compendium 6.28/6.28b/6.28c, built
    # 2026-10-16, the EXCLUSIVE siblings of ':to()'/':from()'. RANGE_
    # MANIFEST is v0..v4, positions 0-4, dates 2026-01-01..2026-01-05.
    def test_after_excludes_its_own_position(self):
        results = _finder(
            '$ranger.files.:name("orders.csv").:after(1)', RANGE_HOME, RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v2", "v3", "v4"]

    def test_before_excludes_its_own_position(self):
        results = _finder(
            '$ranger.files.:name("orders.csv").:before(3)', RANGE_HOME, RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v0", "v1", "v2"]

    def test_after_and_before_together_is_an_exclusive_range(self):
        results = _finder(
            '$ranger.files.:name("orders.csv").:after(1):before(4)',
            RANGE_HOME,
            RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v2", "v3"]

    def test_after_with_a_negative_index_counts_one_later(self):
        # position -3 is v2; "after" position -3 is v3 onward.
        results = _finder(
            '$ranger.files.:name("orders.csv").:after(-3)', RANGE_HOME, RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v3", "v4"]

    def test_before_with_a_negative_index_excludes_the_last_item(self):
        results = _finder(
            '$ranger.files.:name("orders.csv").:before(-1)', RANGE_HOME, RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v0", "v1", "v2", "v3"]

    def test_after_and_to_can_combine_dissimilar_directions(self):
        # 6.28's own point: dissimilar functions (one exclusive lower,
        # one inclusive upper) may pair freely.
        results = _finder(
            '$ranger.files.:name("orders.csv").:after(1):to(3)',
            RANGE_HOME,
            RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v2", "v3"]

    def test_date_mode_after_excludes_its_own_date(self):
        results = _finder(
            '$ranger.files.:name("orders.csv").:after("2026-01-02")',
            RANGE_HOME,
            RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v2", "v3", "v4"]

    def test_date_mode_before_excludes_its_own_date(self):
        results = _finder(
            '$ranger.files.:name("orders.csv").:before("2026-01-04")',
            RANGE_HOME,
            RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v0", "v1", "v2"]

    def test_combining_two_lower_bounds_is_illegal(self):
        # 6.28c: ':from()'/':after()' both indicate the same direction.
        with pytest.raises(ReferenceException3):
            _finder(
                '$ranger.files.:name("orders.csv").:from(1):after(2)',
                RANGE_HOME,
                RANGE_MANIFEST,
            ).query()

    def test_combining_two_upper_bounds_is_illegal(self):
        # 6.28c's own named example: ':to()' + ':before()'.
        with pytest.raises(ReferenceException3):
            _finder(
                '$ranger.files.:name("orders.csv").:to(3):before(1)',
                RANGE_HOME,
                RANGE_MANIFEST,
            ).query()

    def test_below_alias_behaves_exactly_like_before(self):
        results = _finder(
            '$ranger.files.:name("orders.csv").:below(3)', RANGE_HOME, RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v0", "v1", "v2"]

    def test_above_alias_behaves_exactly_like_after(self):
        results = _finder(
            '$ranger.files.:name("orders.csv").:above(1)', RANGE_HOME, RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v2", "v3", "v4"]


class TestImpliedStarForNameOneFunctions:
    # compendium 3.9c/3.9d: a function starting name_one, or following
    # directly after a path separator, implies a '*' wildcard unless it
    # is itself a wildcard, fully occupies a path segment, or does not
    # operate in a path segment at all. ':after()'/':before()'/':from()'/
    # ':to()' fit none of those three exemption categories, so by spec
    # they default into the implied-'*' rule -- added 2026-10-16, closing
    # the gap where the bare form used to raise a DIFFERENT, misleading
    # message ("not a legal name_one path segment") than the already-
    # normalized explicit-'*' form ("functions attached directly to
    # name_one"). The fix does NOT make ':after()' legal at name_one for
    # FILES -- it is still name_three-only there by design (From3's own
    # POSITIONS, "FILES' version selector never lives in name_one") --
    # it only makes both forms fail for the SAME, accurate reason.
    _MESSAGE = (
        "FilesReferenceFinder3 does not support functions attached "
        "directly to name_one -- put the version-selecting function in "
        "name_three instead."
    )

    def test_bare_and_explicit_star_raise_the_identical_message(self):
        with pytest.raises(ReferenceException3) as bare_exc:
            _finder(
                "$ranger.files.:after(:index(3))", RANGE_HOME, RANGE_MANIFEST
            ).query()
        with pytest.raises(ReferenceException3) as star_exc:
            _finder(
                "$ranger.files.*:after(:index(3))", RANGE_HOME, RANGE_MANIFEST
            ).query()
        assert str(bare_exc.value) == str(star_exc.value) == self._MESSAGE

    def test_following_a_path_separator_also_implies_star(self):
        # 3.9c's OTHER clause -- not just "starting name_one," also "a
        # function following directly after a path separator" (a
        # literal/'*'-prefixed path ending in a not-otherwise-recognized
        # function, not just a bare sole-content one).
        with pytest.raises(ReferenceException3) as exc:
            _finder(
                "$mixed.files.nested/:after(:index(0))",
                MIXED_HOME,
                MIXED_MANIFEST,
            ).query()
        assert str(exc.value) == self._MESSAGE

    def test_name_three_position_is_unaffected_and_still_works(self):
        # the one currently-legal form for FILES -- ':after()' riding in
        # name_three, after a real path separator -- must keep working
        # exactly as before; this fix only touches name_one.
        results = _finder(
            "$ranger.files.*.:after(:index(3))", RANGE_HOME, RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v4"]

    def test_name_regex_and_clock_functions_remain_exempt_and_unaffected(self):
        # ':name()' is in _apply_implied_star()'s own exemption list
        # ("fully occupies a path segment") -- confirms the fix did not
        # start wrongly normalizing it too (it would raise the "functions
        # attached directly to name_one" message instead of resolving,
        # if it had).
        results = _finder(
            '$ranger.files.:name("orders.csv").:last()', RANGE_HOME, RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v4"]


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

    def test_groups_combined_with_manifest_now_resolves_each_groups_own_entry(self):
        # same fix as ':all()''s own equivalent test above, 2026-10-16 --
        # ':groups()' shares the identical `partitioned` reduction path.
        results = _finder(
            "$mixed.files.:groups().:last():manifest()", MIXED_HOME, MIXED_MANIFEST
        ).resolve()
        assert {r.data["uuid"] for r in results.results} == {"u-zero-2", "u-deep-2"}

    def test_groups_combined_with_a_field_accessor_gives_one_value_per_group(self):
        # narrowed 2026-08-29, same fix as ':all()' above -- ':groups()'
        # (any-depth GROUP) shares the identical `partitioned` reduction
        # path.
        results = _finder(
            "$mixed.files.:groups().:last():uuid()", MIXED_HOME, MIXED_MANIFEST
        ).resolve()
        assert {r.data for r in results.results} == {"u-zero-2", "u-deep-2"}


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

    def test_manifest_with_a_chained_field_accessor_is_poolable_not_ambiguous(
        self,
    ):
        # added 2026-09-28 -- a real, confirmed bug caught while
        # re-auditing the '*'-traversal content-accessor guards (see the
        # bucket list): "one.csv" has two matching versions, no pointer,
        # so bare ':manifest()' alone would correctly be Rule 1
        # territory (see test_manifest_alone_with_more_than_one_
        # matching_version_raises above) -- but chaining a field
        # accessor (':uuid()') onto ':manifest()' means resolve_kind
        # resolves to METADATA_FIELD, not METADATA_FILE (see Reference3.
        # resolve_kind's own priority), so :manifest() itself is never
        # actually read as a whole resource here at all. This used to be
        # incorrectly rejected identically to the bare case -- confirmed
        # live before this fix. Field accessors are exempt from Rule 1
        # (Rule 3) -- poolable, one value per matched version.
        finder = _finder(
            '$alpha.files.:name("one.csv").:manifest():uuid()',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        )
        results = finder.query()
        assert results.ambiguous_content_read is False
        assert len(results) == 2
        resolved = finder.resolve()
        assert sorted(r.data for r in resolved.results) == ["u-one-1", "u-one-2"]

    def test_all_grouping_with_manifest_and_a_chained_field_accessor_is_poolable(
        self,
    ):
        # the GROUP-mode ('*'/':all()') twin of the fix just above -- the
        # same "reject :manifest() combined with grouping" guard used to
        # ALSO incorrectly catch ':manifest():uuid()' (field present),
        # even though only the bare, no-field shape is genuine Rule 1
        # territory. alpha's own two distinct one-level file_homes
        # ("zero.csv", "one.csv") each contribute their own ':all()'-
        # reduced winner's uuid -- same fixture shape as the already-
        # working ':all():last():uuid()' precedent (no :manifest()),
        # just proving :manifest() riding alongside it does not change
        # the outcome.
        finder = _finder(
            "$alpha.files.:all().:last():manifest():uuid()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
        )
        results = finder.resolve()
        assert {r.data for r in results.results} == {"u-zero-1", "u-one-2"}

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
        assert results.files == [pathu.resep(f"{ALPHA_HOME}/definition.json")]
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


class TestReadmeFunction:
    # ":readme()" -- added 2026-09-21, same bare/sole-content shape as
    # ":definition()" above, but README.md is generated by the system by
    # default (compendium 6.12), so absence is the unusual case, not the
    # normal one -- still resolves to None rather than raising, same
    # treatment as every other genuinely-missing well-known file.
    def test_query_returns_the_readme_path_with_no_uuid(self):
        finder = _finder("$alpha.files.:readme()", ALPHA_HOME, ALPHA_MANIFEST)
        results = finder.query()
        assert results.files == [pathu.resep(f"{ALPHA_HOME}/README.md")]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_readmes_raw_bytes(self, tmp_path):
        content = b"# alpha\n\nSome notes about this named-file.\n"
        home = tmp_path / "alpha"
        home.mkdir()
        (home / "README.md").write_bytes(content)
        finder = _finder("$alpha.files.:readme()", str(home), ALPHA_MANIFEST)
        results = finder.resolve()
        assert results.results[0].data == content

    def test_resolve_gives_none_when_never_generated(self, tmp_path):
        home = tmp_path / "alpha"
        home.mkdir()
        finder = _finder("$alpha.files.:readme()", str(home), ALPHA_MANIFEST)
        results = finder.resolve()
        assert results.results[0].data is None

    def test_readme_cannot_combine_with_a_path(self):
        # compendium 6.12: "you cannot combine a path with the
        # ':readme()' function in name_one" -- enforced the same way
        # :manifest()/:definition() enforce their own bare-only shape,
        # via _is_bare_pointer_reference() simply not matching, so this
        # falls through to ordinary path-narrowing logic instead (which
        # then fails to recognize ":readme()" as a legal path-building
        # segment at all).
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.files.orders/:readme()", ALPHA_HOME, ALPHA_MANIFEST
            ).query()


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
        "file_name": "orders.csv",
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

    def test_file_home(self):
        # :home() split 2026-08-26 -- FILES' own field-read job is now
        # :file_home().
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():file_home()',
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

    def test_file_name(self):
        # added 2026-10-15, closing the deferred-work bucket list gap --
        # confirmed against FileRegistrar/FilesListener's real write
        # path before building: a real, already-written field on both
        # the per-named-file manifest (table 1, read here) and the
        # global arrivals ledger (table 2), the basename of file_home.
        finder = _finder(
            '$rich.files.:name("orders.csv").:first():file_name()',
            RICH_HOME,
            RICH_MANIFEST,
        )
        results = finder.resolve()
        assert results.results[0].data == "orders.csv"

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


class TestUsernameHostLedgerFallback:
    # username/host widened 2026-08-26 to also cover FILES -- RICH_
    # MANIFEST's own entries never have these fields (confirmed, the
    # Named-File Manifest genuinely has no such fields), only the
    # global arrivals ledger does. host/hostname consolidated into one
    # function, "host", 2026-09-20 -- ip_address is retired (confirmed
    # always-null in practice, not worth its own accessor), so this
    # ledger fixture no longer carries it.
    LEDGER = [
        {
            "uuid": "u-rich-2",
            "username": "bot",
            "hostname": "worker-1",
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

    def test_host_falls_back_to_the_ledger_entry(self):
        finder = _finder(
            '$rich.files.:name("orders.csv").:last():host()',
            RICH_HOME,
            RICH_MANIFEST,
            ledger=self.LEDGER,
        )
        assert finder.resolve().results[0].data == "worker-1"

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
        assert results.files == [pathu.resep(f"{RICH_HOME}/definition.json")]
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

    def test_metadata_file_kind_unreachable_via_a_real_reference(self):
        # :meta() is not a registered function at all, so a real
        # query()/resolve() would already reject this reference earlier
        # (unknown function, in build_chain()). calling _extract_data()
        # directly tests its own resolve_kind branching in isolation --
        # this confirms the generic resolve_kind fallback (not-yet-
        # supported sweep #10) is a defensive safety net, not a pending
        # gap.
        finder = _finder("$alpha.files.*.:meta()", ALPHA_HOME, ALPHA_MANIFEST)
        with pytest.raises(ReferenceException3):
            finder._extract_data(ReferenceResult3(path="p", uuid="u"))

    def test_metadata_field_kind_unreachable_via_a_real_reference(self):
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


BOOK1_XLSX = os.path.join(
    "tests", "csvpaths", "test_resources", "Book1.xlsx"
)


class TestNameTwoWorksheetMarker:
    # '#worksheet' (name_two) -- settled 2026-08-26, see the "#name_two"
    # bucket-list entry. Book1.xlsx (a real, shared test fixture -- also
    # used by tests/csvpaths/test_csvpaths_xlsx.py) has two known real
    # worksheets, "hello" and "world".
    def test_query_populates_identity_with_the_worksheet_name(self):
        manifest = [
            {"file": BOOK1_XLSX, "file_home": f"{ALPHA_HOME}/Book1.xlsx", "uuid": "u-1"}
        ]
        results = _finder(
            '$alpha.files.:name("Book1.xlsx")#hello.:last()',
            ALPHA_HOME,
            manifest,
        ).query()
        assert results.results[0].identity == "hello"
        assert results.results[0].path == BOOK1_XLSX

    def test_resolve_reads_the_named_worksheets_own_rows(self):
        manifest = [
            {"file": BOOK1_XLSX, "file_home": f"{ALPHA_HOME}/Book1.xlsx", "uuid": "u-1"}
        ]
        results = _finder(
            '$alpha.files.:name("Book1.xlsx")#hello.:last()',
            ALPHA_HOME,
            manifest,
        ).resolve()
        rows = results.results[0].data
        assert isinstance(rows, list)
        assert len(rows) > 0
        assert all(isinstance(row, list) for row in rows)

    def test_a_different_worksheet_gives_different_rows(self):
        manifest = [
            {"file": BOOK1_XLSX, "file_home": f"{ALPHA_HOME}/Book1.xlsx", "uuid": "u-1"}
        ]
        hello = _finder(
            '$alpha.files.:name("Book1.xlsx")#hello.:last()',
            ALPHA_HOME,
            manifest,
        ).resolve()
        world = _finder(
            '$alpha.files.:name("Book1.xlsx")#world.:last()',
            ALPHA_HOME,
            manifest,
        ).resolve()
        assert hello.results[0].data != world.results[0].data

    def test_worksheet_marker_requires_a_pointer(self):
        # no name_three pointer at all -- there is no single version to
        # read a worksheet from.
        manifest = [
            {"file": BOOK1_XLSX, "file_home": f"{ALPHA_HOME}/Book1.xlsx", "uuid": "u-1"}
        ]
        with pytest.raises(ReferenceException3):
            _finder(
                '$alpha.files.:name("Book1.xlsx")#hello', ALPHA_HOME, manifest
            ).query()

    def test_worksheet_marker_rejects_a_non_xlsx_file(self):
        results = _finder(
            '$alpha.files.:name("one.csv")#hello.:last()',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        )
        with pytest.raises(ReferenceException3):
            results.resolve()

    def test_worksheet_marker_rejects_a_bare_marker_function(self):
        # ':all()' (or ':manifest()'/':home()'/etc.) occupies name_one's
        # entire content on its own -- there is no literal file for a
        # worksheet marker to apply to.
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.files.:all()#hello.:last()", ALPHA_HOME, ALPHA_MANIFEST
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


REGEX_ACME_HOME = "inputs/named_files/acme_orders"
REGEX_ACME_MANIFEST = [
    {
        "file": "inputs/named_files/acme_orders/x.csv",
        "file_home": "inputs/named_files/acme_orders",
        "uuid": "u-acme-1",
    },
]
REGEX_ABBA_HOME = "inputs/named_files/abba_invoices"
REGEX_ABBA_MANIFEST = [
    {
        "file": "inputs/named_files/abba_invoices/y.csv",
        "file_home": "inputs/named_files/abba_invoices",
        "uuid": "u-abba-1",
    },
]
REGEX_BY_NAME = {
    "acme_orders": (REGEX_ACME_HOME, REGEX_ACME_MANIFEST),
    "abba_invoices": (REGEX_ABBA_HOME, REGEX_ABBA_MANIFEST),
}


class TestRegexRootMajor:
    # :regex() at root_major -- added 2026-08-27, the crowded-namespace
    # motivating case (David): "acme_orders"/"acme_invoices"/
    # "abba_invoices" are more manageable when a reference can target
    # "/abba_.*/" directly, instead of enumerating every exact name.
    # Reuses FilesReferenceFinder3's own '*'-traversal machinery, just
    # pre-filtered by pattern before it enumerates named_file_names.
    def test_regex_filters_to_matching_named_files(self):
        results = _finder(
            "$:regex(/^abba_.*/).files.:home()",
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
        ).query()
        assert results.files == [REGEX_ABBA_HOME]

    def test_regex_excludes_non_matching_named_files(self):
        results = _finder(
            "$:regex(/^abba_.*/).files.:home()",
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
        ).query()
        assert REGEX_ACME_HOME not in results.files

    def test_regex_with_no_matches_gives_empty(self):
        results = _finder(
            "$:regex(/^zzz_.*/).files.:home()",
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
        ).query()
        assert results.files == []

    def test_wrong_root_major_function_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$:having("x").files.:home()',
                REGEX_ACME_HOME,
                REGEX_ACME_MANIFEST,
                by_name=REGEX_BY_NAME,
            ).query()

    def test_regex_accepts_a_registered_variable(self):
        results = _finder(
            "$:regex(@aregex).files.:home()",
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
            variables={"aregex": "^abba_.*"},
        ).query()
        assert results.files == [REGEX_ABBA_HOME]
