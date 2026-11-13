import os

import pytest

from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
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
    # (':definition(:on_arrival(:has_value()))') -- those need a
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

    @pytest.mark.parametrize(
        "pointer, expected",
        [(":last()", -1), (":first()", 0), (":index(1)", 1)],
    )
    @pytest.mark.parametrize("manifest_first", [True, False])
    def test_both_orders_resolve_the_ledger_record(
        self, pointer, expected, manifest_first
    ):
        # ':manifest():last()' resolved None until 2026-11-12, though its
        # query was right: the name_one file-pointer branch (5.21) read
        # the live entry, and a ledger-only record (none of LEDGER's has a
        # live manifest here) has none. ':last():manifest()' gave it.
        chain = f":manifest(){pointer}" if manifest_first else f"{pointer}:manifest()"
        finder = _finder(
            f"$*.files.{chain}",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=LEDGER,
        )
        assert [r.data for r in finder.resolve().results] == [LEDGER[expected]]

    @pytest.mark.parametrize(
        "chain",
        [":manifest():last()", ":last():manifest()", ":manifest():index(4)"],
    )
    def test_a_live_record_resolves_its_live_entry_in_both_orders(self, chain):
        # D6: live first, the ledger for a ledger-only record. The ledger
        # fingerprints differ ("L-"), so a ledger read cannot pass.
        ledger = [dict(e, fingerprint="L-" + e["fingerprint"]) for e in STAR_LEDGER]
        finder = _finder(
            f"$*.files.{chain}",
            STAR_ALPHA_HOME,
            STAR_ALPHA_MANIFEST,
            by_name=STAR_BY_NAME,
            ledger=ledger,
            inputs_files_path="inputs/named_files",
        )
        assert [r.data for r in finder.resolve().results] == [STAR_BETA_MANIFEST[1]]

    # Rule 1b under ':regex()'/':choice()': the ledger set filtered by
    # name (6.13b), in ledger order. It raised at query until 2026-11-12.
    # "alfa" is a deleted named-file, so u-alfa-1 is ledger-only.
    @staticmethod
    def _regex_ledger() -> list:
        names = ["alpha", "alpha", "alpha", "beta", "beta"]
        ledger = [
            dict(e, fingerprint="L-" + e["fingerprint"], named_file_name=name)
            for e, name in zip(STAR_LEDGER, names)
        ]
        alfa = {"uuid": "u-alfa-1", "fingerprint": "L-alfa", "named_file_name": "alfa"}
        return ledger + [alfa]

    def _regex_data(self, reference: str) -> list:
        finder = _finder(
            reference,
            STAR_ALPHA_HOME,
            STAR_ALPHA_MANIFEST,
            by_name=STAR_BY_NAME,
            ledger=self._regex_ledger(),
            inputs_files_path="inputs/named_files",
        )
        return [r.data["fingerprint"] for r in finder.resolve().results]

    @pytest.mark.parametrize("root", ["$:regex(/^alpha$/)", '$:choice("alpha")'])
    @pytest.mark.parametrize(
        "chain, expected",
        [
            # live records give their live entry (D6)
            (":manifest():last()", ["ccc"]),
            (":last():manifest()", ["ccc"]),
            (":manifest():first()", ["aaa"]),
            (":first():manifest()", ["aaa"]),
            (":manifest():index(1)", ["bbb"]),
            (":manifest():index(9)", []),
        ],
    )
    def test_a_filtered_root_picks_from_its_own_records(self, root, chain, expected):
        assert self._regex_data(f"{root}.files.{chain}") == expected

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # the ledger order of the filtered set: alpha's three, then
            # the deleted alfa's record, which only the ledger holds
            ("$:regex(/^al/).files.:manifest():last()", ["L-alfa"]),
            ("$:regex(/^al/).files.:last():manifest()", ["L-alfa"]),
            ('$:choice("alfa|beta").files.:manifest():first()', ["ddd"]),
            ('$:choice("alfa|beta").files.:manifest():index(2)', ["L-alfa"]),
        ],
    )
    def test_a_filtered_root_keeps_ledger_order_and_ledger_records(
        self, reference, expected
    ):
        assert self._regex_data(reference) == expected

    def test_a_bare_manifest_under_a_filtered_root_still_raises(self):
        # what a bare ':manifest()' returns under ':regex()' waits for
        # David (decision log W1); the pointer forms above do not
        with pytest.raises(ReferenceException3):
            self._regex_data("$:regex(/^al/).files.:manifest()")

    def test_a_literal_root_reads_its_own_manifest_in_both_orders(self):
        # unchanged: '$alpha' reads alpha's own manifest.json
        for chain in (":manifest():last()", ":last():manifest()"):
            finder = _finder(
                f"$alpha.files.{chain}",
                ALPHA_HOME,
                ALPHA_MANIFEST,
                inputs_files_path="inputs/named_files",
                ledger=LEDGER,
            )
            assert [r.data for r in finder.resolve().results] == [ALPHA_MANIFEST[-1]]


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
# narrowed 2026-08-29 -- read the global arrivals ledger until 2026-11-12;
# it now reads the holding named-file's own manifest first (decision D4),
# with this ledger as the fallback for ledger-only fields.
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
    # a '$*' root groups by named-file (compendium 4.1b, David
    # 2026-11-06; pooled across every named-file until then). The '*' in
    # name_one pools that named-file's one-level files, time-sorted, and
    # the pointer picks within each named-file. ':flatten()' is the
    # pooled form. Times: zero-1, one-1, one-2 (alpha), two-1, two-2
    # (beta).
    def test_last_is_each_named_files_most_recent(self):
        # alpha's last is one-2, from a different file than its first
        results = _star_finder("$*.files.*.:last()").query()
        assert results.uuids == ["u-one-2", "u-two-2"]

    def test_first_is_each_named_files_earliest(self):
        results = _star_finder("$*.files.*.:first()").query()
        assert results.uuids == ["u-zero-1", "u-two-1"]

    def test_index_selects_by_chronological_position(self):
        # beta has no third version
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
        assert [r.data["uuid"] for r in results.results] == ["u-one-2", "u-two-2"]

    def test_combining_with_a_field_accessor_now_works(self):
        # narrowed 2026-08-29 -- POOL mode always reduces to exactly one
        # overall candidate, so a field accessor riding alongside the
        # pointer is unambiguous the same way it already was for every
        # other pointer+field-accessor position in this file.
        results = _star_finder("$*.files.*.:last():uuid()").resolve()
        assert [r.data for r in results.results] == ["u-one-2", "u-two-2"]

    def test_functions_directly_on_name_one_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _star_finder("$*.files.*:last().v1").query()

    def test_an_index_range_is_within_each_named_file(self):
        # built 2026-10-21; pooled until 2026-11-06. A range is a
        # multi-valued pointer, so it groups too (4.1b).
        results = _star_finder("$*.files.*.:from(-2)").query()
        assert results.uuids == ["u-one-1", "u-one-2", "u-two-1", "u-two-2"]

    def test_a_pointer_reduces_the_range_not_the_full_candidate_set(self):
        results = _star_finder("$*.files.*.:from(0):to(1):last()").query()
        assert results.uuids == ["u-one-1", "u-two-2"]


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


class TestTraversalRootResolve:
    # ':regex()' and ':choice()' at root_major are a filtered '*'
    # (compendium 6.13b(iv)), so they resolve as '*' does. Until
    # 2026-11-12 _extract_data() tested for Star3 alone: a name_one
    # pointer or a name_three field or ':manifest()' passed the
    # FunctionCall3 to file_manifest() and raised TypeError, and
    # ':named_file_name()' returned the FunctionCall3 itself as the value.
    # The ledger carries the names, so ':named_file_name()' reads each.
    LEDGER = [{**e, "named_file_name": "alpha"} for e in STAR_LEDGER[:3]] + [
        {**e, "named_file_name": "beta"} for e in STAR_LEDGER[3:]
    ]
    ROOTS = ["$*", "$:regex(/^.*/)", '$:choice("alpha|beta")']

    def _resolve(self, reference: str) -> list:
        results = _finder(
            reference,
            STAR_ALPHA_HOME,
            STAR_ALPHA_MANIFEST,
            by_name=STAR_BY_NAME,
            ledger=self.LEDGER,
        ).resolve()
        return [(r.uuid, r.data) for r in results.results]

    @pytest.mark.parametrize("root", ROOTS)
    @pytest.mark.parametrize(
        "tail, expected",
        [
            (".files.:flatten().:last():fingerprint()", [("u-two-2", "eee")]),
            (".files.:flatten().:last():uuid()", [("u-two-2", "u-two-2")]),
            (".files.:flatten().:last():named_file_name()", [("u-two-2", "beta")]),
            (".files.:flatten().:last():manifest():uuid()", [("u-two-2", "u-two-2")]),
            (
                ".files.*.:last():named_file_name()",
                [("u-one-2", "alpha"), ("u-two-2", "beta")],
            ),
            (
                ".files.*.:last():fingerprint()",
                [("u-one-2", "ccc"), ("u-two-2", "eee")],
            ),
        ],
    )
    def test_a_field_reads_as_under_star(self, root, tail, expected):
        assert self._resolve(root + tail) == expected

    ONE_2 = "inputs/named_files/alpha/one.csv/ccc.csv"
    TWO_2 = "inputs/named_files/beta/two.csv/eee.csv"

    @pytest.mark.parametrize("root", ROOTS)
    @pytest.mark.parametrize(
        "tail, expected",
        [
            (".files.:last()", [("u-one-2", ONE_2), ("u-two-2", TWO_2)]),
            (".files.*.:last():manifest()", [("u-one-2", ONE_2), ("u-two-2", TWO_2)]),
            (".files.:flatten().:last():manifest()", [("u-two-2", TWO_2)]),
        ],
    )
    def test_a_manifest_entry_reads_as_under_star(self, root, tail, expected):
        # the live entry from each named-file's own manifest (6.13b(iv)):
        # only a live entry has "file"; the ledger's entries do not
        assert [
            (uuid, entry.get("file")) for uuid, entry in self._resolve(root + tail)
        ] == expected

    def test_a_regex_root_filters_by_name(self):
        reference = "$:regex(/^al/).files.*.:last():named_file_name()"
        assert self._resolve(reference) == [("u-one-2", "alpha")]


class TestTraversalFieldReadsLiveFirst:
    # decision D4 (2026-11-12): a name_three field after a traversal root
    # reads as the literal reference does, the holding named-file's own
    # manifest first and the ledger as fallback (6.13b(iv), (v)). It read
    # the ledger first, so '$*' and '$alpha' disagreed when the two did.
    # A name_one read under '*' stays on the ledger (ruling C Q1).
    #
    # Every ledger value differs from the live one, so a ledger-first read
    # cannot pass. The live entries carry a stale "lifecycle" and
    # "status" that must not win: both are the ledger's (6.13b(v), (vi),
    # (vii)). u-gone-1 is a ledger-only record of a deleted named-file.
    LEDGER = [
        {
            "uuid": e["uuid"],
            "fingerprint": "L-" + e["fingerprint"],
            "time": "2030-01-01T00:00:00+00:00",
            "named_file_name": "beta" if e["uuid"].startswith("u-two") else "alpha",
            "lifecycle": "active",
            "status": "complete",
        }
        for e in STAR_LEDGER
    ] + [
        {
            "uuid": "u-gone-1",
            "fingerprint": "L-gone",
            "time": "2030-01-02T00:00:00+00:00",
            "named_file_name": "alfa",
            "lifecycle": "deleted",
        }
    ]
    BY_NAME = {
        name: (home, [dict(e, lifecycle="stale", status="stale") for e in manifest])
        for name, (home, manifest) in STAR_BY_NAME.items()
    }
    ROOTS = ["$*", "$:regex(/^.*/)", '$:choice("alpha|beta")']

    def _values(self, reference: str, *, ledger: list | None = None) -> list:
        results = _finder(
            reference,
            STAR_ALPHA_HOME,
            STAR_ALPHA_MANIFEST,
            by_name=self.BY_NAME,
            ledger=self.LEDGER if ledger is None else ledger,
            inputs_files_path="inputs/named_files",
        ).resolve()
        return [r.data for r in results.results]

    @pytest.mark.parametrize("root", ROOTS)
    @pytest.mark.parametrize(
        "tail, expected",
        [
            (".files.*.:last():fingerprint()", ["ccc", "eee"]),
            (".files.*.:last():manifest():fingerprint()", ["ccc", "eee"]),
            (
                ".files.*.:last():time()",
                ["2026-01-03T00:00:00+00:00", "2026-01-05T00:00:00+00:00"],
            ),
            (".files.:flatten().:last():fingerprint()", ["eee"]),
            (".files.*.:last():lifecycle()", ["active", "active"]),
            # ':status()' is the ledger's in FILES too (6.13b(vii))
            (".files.*.:last():status()", ["complete", "complete"]),
            (".files.*.:last():named_file_name()", ["alpha", "beta"]),
        ],
    )
    def test_a_name_three_field_reads_the_live_entry_first(
        self, root, tail, expected
    ):
        assert self._values(root + tail) == expected

    @pytest.mark.parametrize(
        "tail",
        [
            ".files.*.:last():fingerprint()",
            ".files.*.:last():time()",
            ".files.*.:last():lifecycle()",
            ".files.*.:last():status()",
            ".files.*.:last():named_file_name()",
        ],
    )
    def test_star_agrees_with_the_literal_root_for_each_name(self, tail):
        # 6.13b(iv): '$*' is the same reference for every live name
        literal = self._values("$alpha" + tail) + self._values("$beta" + tail)
        assert self._values("$*" + tail) == literal

    @pytest.mark.parametrize("root", ROOTS)
    def test_the_name_comes_from_the_live_named_file(self, root):
        # never None under a traversal root, even when the ledger has no
        # names, as the literal root never is
        nameless = [
            {k: v for k, v in e.items() if k != "named_file_name"}
            for e in self.LEDGER
        ]
        reference = root + ".files.*.:last():named_file_name()"
        assert self._values(reference, ledger=nameless) == ["alpha", "beta"]

    # a name_one read under '*' reaches the ledger set (ruling C Q1): its
    # records, deleted ones too, in ledger order. A live record's values
    # come from its live entry, the ledger's only where that has none
    # (6.13b(v); C1; decision D7, 2026-11-12). This test pinned the
    # ledger's values until then (see D6's correction to D4).
    def _uuids(self, reference: str) -> list:
        return _finder(
            reference,
            STAR_ALPHA_HOME,
            STAR_ALPHA_MANIFEST,
            by_name=self.BY_NAME,
            ledger=self.LEDGER,
            inputs_files_path="inputs/named_files",
        ).query().uuids

    @pytest.mark.parametrize(
        "reference, expected",
        [
            (
                "$*.files.:manifest():fingerprint()",
                ["aaa", "bbb", "ccc", "ddd", "eee", "L-gone"],
            ),
            ("$*.files.:manifest():first():fingerprint()", ["aaa"]),
            # the deleted, ledger-only record keeps its ledger values
            ("$*.files.:manifest():last():fingerprint()", ["L-gone"]),
            ('$*.files.:manifest():lifecycle("deleted"):fingerprint()', ["L-gone"]),
            (
                "$:regex(/^al/).files.:manifest():fingerprint()",
                ["aaa", "bbb", "ccc", "L-gone"],
            ),
            (
                '$:choice("alpha|alfa").files.:manifest():fingerprint()',
                ["aaa", "bbb", "ccc", "L-gone"],
            ),
            # lifecycle and status are the ledger's, not the stale live keys
            (
                "$*.files.:manifest():lifecycle()",
                ["active"] * 5 + ["deleted"],
            ),
            ("$:regex(/^al/).files.:manifest():status()", ["complete"] * 3 + [None]),
            (
                "$*.files.:manifest():named_file_name()",
                ["alpha", "alpha", "alpha", "beta", "beta", "alfa"],
            ),
        ],
    )
    def test_a_name_one_read_takes_the_set_and_live_values(self, reference, expected):
        assert self._values(reference) == expected

    def test_star_values_agree_with_the_literal_root(self):
        star = self._values("$*.files.:manifest():fingerprint()")
        literal = self._values("$alpha.files.:manifest():fingerprint()")
        literal += self._values("$beta.files.:manifest():fingerprint()")
        assert star[:5] == literal

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # a gate matches the value resolve shows, the live one
            ('$*.files.:manifest():fingerprint("ccc")', ["u-one-2"]),
            ('$*.files.:manifest():fingerprint("L-ccc")', []),
            ('$:regex(/^al/).files.:manifest():fingerprint("ccc")', ["u-one-2"]),
            ('$*.files.:manifest():fingerprint("L-gone")', ["u-gone-1"]),
            # a date bound filters on the live time ':time()' resolves
            (
                '$*.files.:manifest():from(:date("2026-01-03"))',
                ["u-one-2", "u-two-1", "u-two-2", "u-gone-1"],
            ),
            # an index range counts in ledger order
            ("$*.files.:manifest():from(2):to(3)", ["u-one-2", "u-two-1"]),
        ],
    )
    def test_a_name_one_gate_sees_the_values_resolve_shows(self, reference, expected):
        assert self._uuids(reference) == expected

    def test_a_filter_only_read_resolves_the_live_entry(self):
        # as for Rule 1b (D6): a live record is its live entry
        values = self._values('$*.files.:manifest():fingerprint("ccc")')
        live = dict(STAR_ALPHA_MANIFEST[2], lifecycle="stale", status="stale")
        assert values == [live]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # a chain with no field resolves whole records: a live record
            # is its live entry ("ccc", not "L-ccc"), a ledger-only one its
            # ledger record. It gave the ledger record (reviewer on #585).
            ('$*.files.:manifest():fingerprint("ccc"):last()', ["ccc"]),
            ('$*.files.:manifest():lifecycle("active"):last()', ["eee"]),
            ("$*.files.:manifest():from(1):to(2)", ["bbb", "ccc"]),
            ("$*.files.:manifest():from(4)", ["eee", "L-gone"]),
            ('$*.files.:manifest():from(:date("2026-01-03")):first()', ["ccc"]),
            ("$:regex(/^al/).files.:manifest():from(1):to(2)", ["bbb", "ccc"]),
        ],
    )
    def test_a_whole_record_read_gives_the_live_entry(self, reference, expected):
        assert [e["fingerprint"] for e in self._values(reference)] == expected

    @pytest.mark.parametrize(
        "reference",
        [
            # the bare one-gate form and the general chain take two paths
            '$*.files.:manifest():fingerprint("ccc")',
            '$*.files.:manifest():fingerprint("ccc"):type("csv")',
        ],
    )
    def test_a_gate_reads_each_manifest_once(self, reference):
        # one map of live entries per query, not a walk of every manifest
        # per record (reviewer on #585, cost on a cloud backend)
        finder = _finder(
            reference,
            STAR_ALPHA_HOME,
            STAR_ALPHA_MANIFEST,
            by_name=self.BY_NAME,
            ledger=self.LEDGER,
            inputs_files_path="inputs/named_files",
        )
        reads = []
        real = finder.source.file_manifest
        finder.source.file_manifest = lambda name: reads.append(name) or real(name)
        finder.query()
        assert sorted(reads) == ["alpha", "beta"]

    @pytest.mark.parametrize(
        "reference",
        [
            "$*.files.:manifest():fingerprint()",
            "$*.files.:manifest():from(0):to(4)",
            "$*.files.:manifest():from(0):to(4):fingerprint()",
            "$*.files.:manifest():last():fingerprint()",
        ],
    )
    def test_resolve_reads_each_manifest_once(self, reference):
        # resolve_from() reads the live entries once for all its results,
        # not once per result (reviewer on #585)
        finder = _finder(
            reference,
            STAR_ALPHA_HOME,
            STAR_ALPHA_MANIFEST,
            by_name=self.BY_NAME,
            ledger=self.LEDGER,
            inputs_files_path="inputs/named_files",
        )
        selection = finder.query()
        reads = []
        real = finder.source.file_manifest
        finder.source.file_manifest = lambda name: reads.append(name) or real(name)
        finder.resolve_from(selection)
        assert sorted(reads) == ["alpha", "beta"]

    def test_a_date_bound_and_time_agree(self):
        reference = '$*.files.:manifest():from(:date("2026-01-03")):time()'
        assert self._values(reference) == [
            "2026-01-03T00:00:00+00:00",
            "2026-01-04T00:00:00+00:00",
            "2026-01-05T00:00:00+00:00",
            "2030-01-02T00:00:00+00:00",
        ]


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

    @pytest.mark.parametrize(
        "reference, expected",
        [
            ("$:regex(/^al.*/).files.:manifest():uuid()", ["u-ledger-1"]),
            ("$:regex(/^al.*/).files.:manifest():named_file_name()", ["alpha"]),
            ("$:regex(/^.*/).files.:manifest():named_file_name()", ["alpha", "beta"]),
            ("$:regex(/^zz/).files.:manifest():uuid()", []),
            ('$:choice("alpha").files.:manifest():uuid()', ["u-ledger-1"]),
            (
                '$:choice("alpha|beta").files.:manifest():named_file_name()',
                ["alpha", "beta"],
            ),
        ],
    )
    def test_a_regex_or_choice_root_resolves_from_the_ledger(
        self, reference, expected
    ):
        # resolve read the named-file's own manifest for any root but '*',
        # so ':regex()' and ':choice()' passed their FunctionCall3 to
        # file_manifest() and raised TypeError (2026-11-12). Like '*',
        # they read the ledger, as their query does.
        results = _finder(
            reference,
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=MANIFEST_FIELD_LEDGER,
        ).resolve()
        assert [r.data for r in results.results] == expected

    # the ledger holds every record, deleted and failed ones included
    # (compendium 6.13b(i), (vi)): what separates the Rule 1a read from a
    # live-name traversal. "alfa" was deleted; alpha's second arrival
    # failed.
    REGEX_LEDGER = [
        {
            "named_file_name": "alpha",
            "uuid": "u-a1",
            "lifecycle": "active",
            "status": "complete",
        },
        {
            "named_file_name": "alpha",
            "uuid": "u-a2",
            "lifecycle": "active",
            "status": "failed",
        },
        {
            "named_file_name": "alfa",
            "uuid": "u-d1",
            "lifecycle": "deleted",
            "status": "complete",
        },
        {
            "named_file_name": "beta",
            "uuid": "u-b1",
            "lifecycle": "active",
            "status": "complete",
        },
    ]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            (
                "$:regex(/^al/).files.:manifest():lifecycle()",
                ["active", "active", "deleted"],
            ),
            (
                "$:regex(/^al/).files.:manifest():status()",
                ["complete", "failed", "complete"],
            ),
            (
                '$:regex(/^al/).files.:manifest():lifecycle("deleted"):uuid()',
                ["u-d1"],
            ),
            ('$:regex(/^al/).files.:manifest():status("failed"):uuid()', ["u-a2"]),
            (
                '$:choice("alfa|beta").files.:manifest():lifecycle()',
                ["deleted", "active"],
            ),
        ],
    )
    def test_a_regex_or_choice_root_reads_deleted_and_failed_entries(
        self, reference, expected
    ):
        results = _finder(
            reference,
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=self.REGEX_LEDGER,
        ).resolve()
        assert [r.data for r in results.results] == expected

    def test_combined_with_name_three_is_not_yet_supported(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.files.:manifest():uuid().:last()",
                ALPHA_HOME,
                ALPHA_MANIFEST,
                inputs_files_path="inputs/named_files",
                ledger=MANIFEST_FIELD_LEDGER,
            ).query()


#
# the global ledger and a per-name manifest spell some keys differently:
# "file_path"/"origin_path" in the ledger, "file"/"from" per name. the
# definition's template differs from every stored one, so a read of the
# wrong source shows.
#
FIELD_SOURCE_LEDGER = [
    {
        "named_file_name": "alpha",
        "uuid": "u-alpha-1",
        "file_path": "inputs/named_files/alpha/one.csv/aaa.csv",
        "origin_path": "/landing/alpha/one.csv",
        "template": "alpha-stored",
    },
    {
        "named_file_name": "beta",
        "uuid": "u-beta-1",
        "file_path": "inputs/named_files/beta/two.csv/bbb.csv",
        "origin_path": "/landing/beta/two.csv",
        "template": "beta-stored",
    },
]
FIELD_SOURCE_MANIFEST = [
    {
        "file": "inputs/named_files/alpha/one.csv/aaa.csv",
        "file_home": "inputs/named_files/alpha/one.csv",
        "from": "/landing/alpha/one.csv",
        "template": "alpha-stored",
        "uuid": "u-alpha-1",
    },
]
FIELD_SOURCE_DEFINITION = {"template": "current-default"}


def _field_source_finder(reference: str) -> FilesReferenceFinder3:
    return _finder(
        reference,
        ALPHA_HOME,
        FIELD_SOURCE_MANIFEST,
        definition=FIELD_SOURCE_DEFINITION,
        inputs_files_path="inputs/named_files",
        ledger=FIELD_SOURCE_LEDGER,
    )


def _resolved(reference: str) -> list:
    return [r.data for r in _field_source_finder(reference).resolve().results]


class TestManifestFieldReadsTheManifest:
    # ':manifest():<field>()' reads each field from the manifest entries
    # it maps over: the global ledger under '*', the named-file's own
    # manifest for a literal root. Under '*' these five used to give
    # None, '*', or crash.
    def test_star_file_path_reads_the_ledger_spelling(self):
        assert _resolved("$*.files.:manifest():file_path()") == [
            "inputs/named_files/alpha/one.csv/aaa.csv",
            "inputs/named_files/beta/two.csv/bbb.csv",
        ]

    def test_star_origin_reads_the_ledger_spelling(self):
        assert _resolved("$*.files.:manifest():origin()") == [
            "/landing/alpha/one.csv",
            "/landing/beta/two.csv",
        ]

    def test_star_named_file_name_is_each_entrys_own_name(self):
        assert _resolved("$*.files.:manifest():named_file_name()") == [
            "alpha",
            "beta",
        ]

    def test_star_template_is_each_entrys_stored_template(self):
        assert _resolved("$*.files.:manifest():template()") == [
            "alpha-stored",
            "beta-stored",
        ]

    def test_literal_file_path_is_unchanged(self):
        assert _resolved("$alpha.files.:manifest():file_path()") == [
            "inputs/named_files/alpha/one.csv/aaa.csv"
        ]

    def test_literal_origin_is_unchanged(self):
        assert _resolved("$alpha.files.:manifest():origin()") == [
            "/landing/alpha/one.csv"
        ]

    def test_literal_named_file_name_is_unchanged(self):
        assert _resolved("$alpha.files.:manifest():named_file_name()") == ["alpha"]

    def test_literal_template_is_the_stored_template_not_the_definition(self):
        # changed: this used to read definition.json's current default.
        # a per-entry read gives each version's own stored snapshot, as
        # ':name("one.csv").:first():template()' already does.
        assert _resolved("$alpha.files.:manifest():template()") == ["alpha-stored"]

    def test_pointer_template_agrees_with_the_manifest_chain(self):
        assert _resolved('$alpha.files.:name("one.csv").:first():template()') == [
            "alpha-stored"
        ]

    def test_bare_template_still_reads_the_definition(self):
        assert _resolved("$alpha.files.:template()") == ["current-default"]

    @pytest.mark.parametrize("root", ["$*", "$alpha"])
    @pytest.mark.parametrize("field", ["on_arrival", "sources", "run_method"])
    def test_a_definition_field_on_manifest_raises_and_names_it(self, root, field):
        with pytest.raises(ReferenceException3) as error:
            _field_source_finder(f"{root}.files.:manifest():{field}()").query()
        message = str(error.value)
        assert f"':{field}()' reads definition.json" in message
        assert "not supported on ':manifest()'" in message

    def test_bare_definition_field_still_reads_the_definition(self):
        finder = _finder(
            "$alpha.files.:on_arrival()",
            ALPHA_HOME,
            FIELD_SOURCE_MANIFEST,
            definition={
                "on_arrival": {
                    "named_paths_group": "g",
                    "run_method": "collect_paths",
                }
            },
        )
        data = finder.resolve().results[0].data
        assert data["named_paths_group"] == "g"


#
# for the ':manifest():<field>(arg)' gate. alpha has two registrations
# with different types and templates; beta has one, and a failed
# registration with no file_path, which a '*' read never lists.
#
GATE_LEDGER = [
    {
        "named_file_name": "alpha",
        "uuid": "u-a1",
        "file_path": "inputs/named_files/alpha/one.csv/a1.csv",
        "status": "complete",
        "type": "csv",
        "template": "",
        "fingerprint": "f-a1",
    },
    {
        "named_file_name": "alpha",
        "uuid": "u-a2",
        "file_path": "inputs/named_files/alpha/one.csv/a2.xlsx",
        "status": "complete",
        "type": "xlsx",
        "template": ":0/:filename",
        "fingerprint": "f-a2",
    },
    {
        "named_file_name": "beta",
        "uuid": "u-b1",
        "file_path": "inputs/named_files/beta/two.csv/b1.csv",
        "status": "complete",
        "type": "csv",
        "template": "",
        "fingerprint": "f-b1",
    },
    {
        "named_file_name": "beta",
        "uuid": "u-b2",
        "file_path": None,
        "status": "failed",
        "type": None,
        "template": None,
        "fingerprint": None,
    },
]
GATE_MANIFEST = [
    {
        "file": "inputs/named_files/alpha/one.csv/a1.csv",
        "file_home": "inputs/named_files/alpha/one.csv",
        "type": "csv",
        "template": "",
        "fingerprint": "f-a1",
        "uuid": "u-a1",
    },
    {
        "file": "inputs/named_files/alpha/one.csv/a2.xlsx",
        "file_home": "inputs/named_files/alpha/one.csv",
        "type": "xlsx",
        "template": ":0/:filename",
        "fingerprint": "f-a2",
        "uuid": "u-a2",
    },
]


def _gate_finder(reference: str) -> FilesReferenceFinder3:
    return _finder(
        reference,
        ALPHA_HOME,
        GATE_MANIFEST,
        definition={"template": "current-default"},
        inputs_files_path="inputs/named_files",
        ledger=GATE_LEDGER,
    )


def _gate_uuids(reference: str) -> list:
    return _gate_finder(reference).query().uuids


class TestManifestChainGate:
    # a field with an argument after ':manifest()' filters the entries
    # the chain maps over. it used to be silently ignored, so every
    # entry came back whatever the argument said.
    @pytest.mark.parametrize(
        "gate, star, literal",
        [
            ('type("csv")', ["u-a1", "u-b1"], ["u-a1"]),
            ('type("xlsx")', ["u-a2"], ["u-a2"]),
            ('type("json")', [], []),
            # the ledger set lists the failed u-b2 since 2026-11-01. Its
            # template is missing, which does not have a value (compendium
            # 6.36, 2026-11-03; the retired ':not_empty()' matched it).
            (
                "template(:does_not_have_value())",
                ["u-a1", "u-b1", "u-b2"],
                ["u-a1"],
            ),
            ("template(:has_value())", ["u-a2"], ["u-a2"]),
            ('uuid("u-a2")', ["u-a2"], ["u-a2"]),
            ('uuid("nope")', [], []),
            ('fingerprint("f-b1")', ["u-b1"], []),
            ('named_file_name("beta")', ["u-b1", "u-b2"], []),
            ('named_file_name("alpha")', ["u-a1", "u-a2"], ["u-a1", "u-a2"]),
        ],
    )
    def test_gate_filters_both_roots(self, gate, star, literal):
        assert _gate_uuids(f"$*.files.:manifest():{gate}") == star
        assert _gate_uuids(f"$alpha.files.:manifest():{gate}") == literal

    @pytest.mark.parametrize("name", ["none", "not_none", "empty", "not_empty"])
    def test_the_retired_predicates_raise(self, name):
        # retired 2026-11-03 for ':has_value()'/':does_not_have_value()'
        # (compendium 6.36), with no aliases
        for root in ("$*", "$alpha"):
            with pytest.raises(ReferenceException3):
                _gate_uuids(f"{root}.files.:manifest():template(:{name}())")

    def test_status_gate_matches_the_ledger_status(self):
        # status is ledger-only; a literal root reads it through the
        # ledger fallback.
        assert _gate_uuids('$*.files.:manifest():status("complete")') == [
            "u-a1",
            "u-a2",
            "u-b1",
        ]
        assert _gate_uuids('$alpha.files.:manifest():status("complete")') == [
            "u-a1",
            "u-a2",
        ]

    def test_status_failed_finds_the_failure_in_the_ledger_set(self):
        # changed 2026-11-01 (was: matches nothing, because the ledger set
        # skipped entries with no file_path). A failure is a ledger record;
        # its query path is the ledger. A named-file's own manifest never
        # holds a failure, so the literal root still finds none.
        results = _gate_finder('$*.files.:manifest():status("failed")').query()
        assert results.uuids == ["u-b2"]
        assert results.files == ["inputs/named_files/manifest.json"]
        assert _gate_uuids('$alpha.files.:manifest():status("failed")') == []

    def test_gate_composes_with_a_regex_root(self):
        assert _gate_uuids('$:regex(/^be/).files.:manifest():type("csv")') == [
            "u-b1"
        ]

    def test_query_paths_are_the_manifests_holding_the_matches(self):
        # changed 2026-11-01 (was: the matching version files). The
        # entries are manifest records, so query() gives the manifest
        # each is read from (compendium 5.7): the ledger under '*', the
        # named-file's own manifest at a literal root.
        results = _gate_finder('$*.files.:manifest():type("xlsx")').query()
        assert results.files == ["inputs/named_files/manifest.json"]
        assert results.uuids == ["u-a2"]
        results = _gate_finder('$alpha.files.:manifest():type("xlsx")').query()
        assert results.files == ["inputs/named_files/alpha/manifest.json"]
        assert results.uuids == ["u-a2"]

    def test_star_resolve_gives_the_matching_ledger_entries(self):
        # a filter supplies no value (compendium 5.20b/6.40), so resolve
        # gives the matching manifest entries (5.21, a file pointer).
        data = [
            r.data
            for r in _gate_finder('$*.files.:manifest():type("csv")').resolve().results
        ]
        assert data == [GATE_LEDGER[0], GATE_LEDGER[2]]

    def test_literal_resolve_gives_the_matching_manifest_entries(self):
        data = [
            r.data
            for r in _gate_finder('$alpha.files.:manifest():type("csv")')
            .resolve()
            .results
        ]
        assert data == [GATE_MANIFEST[0]]

    def test_resolve_with_no_match_is_empty(self):
        assert _gate_finder('$*.files.:manifest():type("json")').resolve().results == []

    @pytest.mark.parametrize("root", ["$*", "$alpha"])
    @pytest.mark.parametrize("field", ["type", "uuid", "named_file_name"])
    def test_without_an_argument_the_field_is_still_the_value(self, root, field):
        finder = _gate_finder(f"{root}.files.:manifest():{field}()")
        # the ledger set includes the failed u-b2 (2026-11-01)
        assert len(finder.query().results) == (4 if root == "$*" else 2)
        values = [r.data for r in finder.resolve().results]
        assert all(not isinstance(v, dict) for v in values)

    @pytest.mark.parametrize("root", ["$*", "$alpha"])
    @pytest.mark.parametrize(
        "gate", ['file_name("one.csv")', "time(:has_value())", 'host("h")']
    )
    def test_a_field_that_takes_no_argument_raises(self, root, gate):
        # these do not filter yet. they raise instead of being ignored.
        with pytest.raises(ReferenceException3) as error:
            _gate_finder(f"{root}.files.:manifest():{gate}").query()
        assert "does not take an argument" in str(error.value)

    def test_literal_name_gate_does_not_need_the_ledger(self):
        # with a literal root the name is the root itself, so an entry
        # missing from the global ledger still matches.
        finder = _finder(
            '$alpha.files.:manifest():named_file_name("alpha")',
            ALPHA_HOME,
            GATE_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=[],
        )
        assert finder.query().uuids == ["u-a1", "u-a2"]

    def test_bare_type_gate_is_unchanged(self):
        # the bare form reads each named-file's own manifest, not the
        # ledger, and gives the matching file home; not touched here.
        finder = _finder(
            '$alpha.files.:type("xlsx")',
            ALPHA_HOME,
            GATE_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=GATE_LEDGER,
        )
        assert finder.query().files == ["inputs/named_files/alpha/one.csv"]


class _FakeLogger:
    def __init__(self):
        self.warnings = []

    def warning(self, message, *args):
        self.warnings.append(message % args)


def _chain_values(reference: str) -> list:
    return [r.data for r in _gate_finder(reference).resolve().results]


class TestManifestChainParts:
    # _manifest_chain() sorts a general ':manifest()' chain into its
    # parts, and leaves every other shape to its own branch (finding E).
    def _parts(self, reference: str):
        name_one = _gate_finder(reference).ref.parsed.name_one
        return FilesReferenceFinder3._manifest_chain(name_one=name_one)

    def test_none_raises(self):
        with pytest.raises(ValueError):
            FilesReferenceFinder3._manifest_chain(name_one=None)

    def test_the_parts_of_a_chain(self):
        parts = self._parts(
            '$*.files.:manifest():status("failed"):last():uuid():type("csv")'
        )
        assert parts["pointer"].name == "last"
        assert [g.name for g in parts["gates"]] == ["status", "type"]
        assert [v.name for v in parts["values"]] == ["uuid"]

    @pytest.mark.parametrize(
        "reference, ranges, pointer",
        [
            # a range or a bare time window is claimed (2026-11-07);
            # these two shapes used to be left to their old handling
            ("$alpha.files.:manifest():last():from(1)", ["from"], "last"),
            ("$alpha.files.:manifest():last():yesterday()", ["yesterday"], "last"),
            # alone beside ':manifest()', in either order: not a field
            ("$alpha.files.:manifest():yesterday()", ["yesterday"], None),
            ("$alpha.files.:year():manifest()", ["year"], None),
            ("$alpha.files.:manifest():from(1)", ["from"], None),
            ("$*.files.:manifest():from(0):to(1)", ["from", "to"], None),
        ],
    )
    def test_a_range_is_its_own_part(self, reference, ranges, pointer):
        parts = self._parts(reference)
        assert [r.name for r in parts["ranges"]] == ranges
        assert (parts["pointer"] and parts["pointer"].name) == pointer
        assert parts["gates"] == [] and parts["values"] == []

    def test_a_chain_without_a_range_has_none(self):
        parts = self._parts("$alpha.files.:manifest():last():uuid()")
        assert parts["ranges"] == []

    def test_the_parts_when_manifest_is_not_first(self):
        parts = self._parts('$alpha.files.:type("csv"):manifest()')
        assert parts["pointer"] is None
        assert [g.name for g in parts["gates"]] == ["type"]
        assert parts["values"] == []

    @pytest.mark.parametrize(
        "reference",
        [
            "$alpha.files.:manifest()",
            "$alpha.files.:manifest():uuid()",
            '$alpha.files.:manifest():type("csv")',
            "$alpha.files.:manifest():last()",
            "$alpha.files.:last():manifest()",
            '$alpha.files.:name("one.csv"):manifest()',
            '$alpha.files.:name("one.csv"):last():manifest()',
            "$alpha.files.:last():uuid()",
        ],
    )
    def test_other_shapes_are_not_claimed(self, reference):
        assert self._parts(reference) is None

    def test_two_pointers_raise(self):
        with pytest.raises(ReferenceException3) as error:
            self._parts("$alpha.files.:manifest():first():last()")
        assert "at most one pointer" in str(error.value)

    @pytest.mark.parametrize(
        "field", ["on_arrival()", "run_method()", "named_file_home()"]
    )
    def test_a_field_not_read_from_the_manifest_raises(self, field):
        with pytest.raises(ReferenceException3) as error:
            self._parts(f"$alpha.files.:manifest():last():{field}")
        assert "does not read a named-file's manifest.json" in str(error.value)


class TestManifestGeneralChain:
    # finding E (2026-11-02): FILES takes a general chain after
    # ':manifest()', as CSVPATHS and RESULTS do. Every gate filters, the
    # pointer picks after, in any written order (compendium 6.1), and the
    # last unargued field supplies the value (5.20b). These all raised
    # "functions attached directly to name_one" before.
    @pytest.mark.parametrize(
        "chain",
        [
            ":manifest():last():uuid()",
            ":manifest():uuid():last()",
            ":last():manifest():uuid()",
            ":uuid():last():manifest()",
        ],
    )
    def test_pointer_and_field_in_any_order(self, chain):
        assert _gate_uuids(f"$*.files.{chain}") == ["u-b2"]
        assert _chain_values(f"$*.files.{chain}") == ["u-b2"]
        assert _gate_uuids(f"$alpha.files.{chain}") == ["u-a2"]
        assert _chain_values(f"$alpha.files.{chain}") == ["u-a2"]

    def test_first_and_index_pointers(self):
        assert _chain_values("$*.files.:manifest():first():uuid()") == ["u-a1"]
        assert _chain_values("$*.files.:manifest():index(2):uuid()") == ["u-b1"]
        assert _chain_values("$*.files.:manifest():index(9):uuid()") == []

    def test_a_gate_with_a_field(self):
        reference = '$*.files.:manifest():type("csv"):uuid()'
        assert _gate_uuids(reference) == ["u-a1", "u-b1"]
        assert _chain_values(reference) == ["u-a1", "u-b1"]
        reference = '$alpha.files.:manifest():type("csv"):fingerprint()'
        assert _chain_values(reference) == ["f-a1"]

    @pytest.mark.parametrize(
        "chain", [':manifest():type("csv"):last()', ':manifest():last():type("csv")']
    )
    def test_gates_filter_before_the_pointer_picks(self, chain):
        # pointer first would pick the failed u-b2, which is not a csv.
        assert _gate_uuids(f"$*.files.{chain}") == ["u-b1"]
        assert _chain_values(f"$*.files.{chain}") == [GATE_LEDGER[2]]
        assert _gate_uuids(f"$alpha.files.{chain}") == ["u-a1"]
        assert _chain_values(f"$alpha.files.{chain}") == [GATE_MANIFEST[0]]

    def test_two_gates_are_anded(self):
        assert _gate_uuids(
            '$*.files.:manifest():status("failed"):named_file_name("beta")'
        ) == ["u-b2"]
        reference = '$*.files.:manifest():status("failed"):named_file_name("alpha")'
        assert _gate_uuids(reference) == []
        assert _gate_uuids(
            '$alpha.files.:manifest():status("complete"):type("xlsx")'
        ) == ["u-a2"]

    def test_gates_a_pointer_and_a_field(self):
        reference = (
            '$*.files.:manifest():status("complete"):type("csv"):first():fingerprint()'
        )
        assert _gate_uuids(reference) == ["u-a1"]
        assert _chain_values(reference) == ["f-a1"]

    def test_no_match_is_empty(self):
        reference = '$*.files.:manifest():type("json"):last():uuid()'
        assert _gate_uuids(reference) == []
        assert _chain_values(reference) == []

    def test_the_last_value_field_wins_with_a_warning(self):
        finder = _gate_finder("$alpha.files.:manifest():last():uuid():fingerprint()")
        logger = _FakeLogger()
        finder.csvpaths.logger = logger
        assert [r.data for r in finder.resolve().results] == ["f-a2"]
        assert len(logger.warnings) == 1
        assert ":fingerprint()" in logger.warnings[0]

    def test_one_value_field_does_not_warn(self):
        finder = _gate_finder('$alpha.files.:manifest():type("csv"):uuid()')
        logger = _FakeLogger()
        finder.csvpaths.logger = logger
        finder.query()
        assert logger.warnings == []

    def test_a_gate_before_manifest_filters(self):
        # ':status("complete"):manifest()' used to query every version,
        # the gate ignored, and then raise on resolve.
        assert _gate_uuids('$alpha.files.:type("xlsx"):manifest()') == ["u-a2"]
        assert _gate_uuids('$alpha.files.:status("failed"):manifest()') == []
        assert _gate_uuids('$*.files.:status("failed"):manifest()') == ["u-b2"]
        assert _chain_values('$alpha.files.:type("xlsx"):manifest()') == [
            GATE_MANIFEST[1]
        ]

    def test_a_field_before_manifest_is_the_value(self):
        # used to query every version, then raise on resolve.
        assert _chain_values("$alpha.files.:uuid():manifest()") == ["u-a1", "u-a2"]

    def test_query_paths_are_the_manifests_holding_the_entries(self):
        results = _gate_finder("$*.files.:manifest():last():uuid()").query()
        assert results.files == ["inputs/named_files/manifest.json"]
        results = _gate_finder("$alpha.files.:manifest():last():uuid()").query()
        assert results.files == ["inputs/named_files/alpha/manifest.json"]

    def test_a_regex_root_reads_the_ledger_set(self):
        reference = "$:regex(/^be/).files.:manifest():last():named_file_name()"
        assert _gate_uuids(reference) == ["u-b2"]
        assert _chain_values(reference) == ["beta"]

    def test_a_regex_root_filters_the_ledger_set_by_name(self):
        # the ledger's last record is beta's, so only the filter makes
        # ':last()' pick alpha's.
        reference = "$:regex(/^al/).files.:manifest():last():uuid()"
        assert _chain_values(reference) == ["u-a2"]

    def test_a_regex_root_name_gate_reads_each_entry(self):
        # the name is read from each entry, not taken from the root,
        # which under ':regex()' is not a name.
        reference = '$:regex(/^a/).files.:manifest():named_file_name("alpha"):first()'
        assert _gate_uuids(reference) == ["u-a1"]

    def test_name_three_raises(self):
        with pytest.raises(ReferenceException3) as error:
            _gate_uuids("$alpha.files.:manifest():last():uuid().:first()")
        assert "':manifest()' chain with name_three" in str(error.value)

    def test_the_two_function_shapes_are_unchanged(self):
        assert _gate_uuids("$alpha.files.:manifest():last()") == _gate_uuids(
            "$alpha.files.:last():manifest()"
        )
        assert _chain_values("$alpha.files.:manifest():uuid()") == _chain_values(
            "$alpha.files.:uuid():manifest()"
        )
        assert _gate_uuids('$*.files.:manifest():type("csv")') == _gate_uuids(
            '$*.files.:type("csv"):manifest()'
        )


#
# finding G (2026-11-02): FILES name_three field chains. orders has two
# file homes: orders.csv with four versions (csv, xlsx, csv, csv) and
# other.csv with two (xlsx, csv). The version files are real, so a read
# of a version's bytes can be checked.
#
G_TYPES = {
    "g0": ("orders.csv", "csv", ""),
    "g1": ("orders.csv", "xlsx", ""),
    "g2": ("orders.csv", "csv", ":0/:filename"),
    "g3": ("orders.csv", "csv", ""),
    "h0": ("other.csv", "xlsx", ""),
    "h1": ("other.csv", "csv", ""),
}


def _g_manifest(root) -> list:
    entries = []
    for n, (uuid, (file_name, file_type, template)) in enumerate(G_TYPES.items()):
        file_home = os.path.join(str(root), "orders", file_name)
        os.makedirs(file_home, exist_ok=True)
        path = os.path.join(file_home, f"{uuid}.{file_type}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"id\n{uuid}\n")
        entries.append(
            {
                "file": path,
                "file_home": file_home,
                "type": file_type,
                "template": template,
                "fingerprint": f"f-{uuid}",
                "uuid": uuid,
                "time": f"2026-01-0{n + 1}T00:00:00+00:00",
            }
        )
    return entries


def _g_finder(reference: str, root, *, star: bool = False) -> FilesReferenceFinder3:
    manifest = _g_manifest(root)
    home = os.path.join(str(root), "orders")
    return _finder(
        reference,
        home,
        manifest,
        inputs_files_path=str(root),
        # under '*' a field value is read from the ledger, which holds
        # every arrival, as a real one does
        ledger=manifest if star else [],
        by_name={"orders": (home, manifest)} if star else None,
    )


def _g_uuids(reference: str, root, *, star: bool = False) -> list:
    return _g_finder(reference, root, star=star).query().uuids


def _g_values(reference: str, root, *, star: bool = False) -> list:
    finder = _g_finder(reference, root, star=star)
    finder.csvpaths.logger = _FakeLogger()
    return [r.data for r in finder.resolve().results]


ORDERS = '$orders.files.:name("orders.csv")'


# a named-file with five versions a day apart, csv but for v3, and a
# ledger whose entries interleave two named-files in time. "now" is pinned
# to 2026-01-04, so yesterday is Jan 3.
CHAIN_RANGE_MANIFEST = [
    {
        "file": f"inputs/named_files/ranger/orders.csv/v{i}.csv",
        "file_home": "inputs/named_files/ranger/orders.csv",
        "uuid": f"v{i}",
        "type": "xlsx" if i == 3 else "csv",
        "time": f"2026-01-0{i + 1}T00:00:00+00:00",
    }
    for i in range(5)
]

CHAIN_RANGE_LEDGER = [
    {
        "named_file_name": name,
        "uuid": uuid,
        "time": f"2026-01-0{day}T{hour}:00:00+00:00",
    }
    for name, uuid, day, hour in (
        ("alpha", "l1", 1, "00"),
        ("beta", "l2", 2, "00"),
        ("alpha", "l3", 3, "00"),
        ("beta", "l4", 3, "12"),
        ("alpha", "l5", 5, "00"),
    )
]


class TestManifestChainRanges:
    # 2026-11-07: a range or a bare time window beside ':manifest()' in
    # name_one narrows the entries, as CSVPATHS and RESULTS do. Before,
    # ':manifest():yesterday()' took the window for a field (it queried
    # every entry, then raised on resolve), ':manifest():yesterday():last()'
    # raised calling it a field function, and ':manifest():from(1)'
    # raised "functions attached directly to name_one". The range comes
    # first, then the gates, then the pointer (6.28).
    #
    # "now" is pinned to 2026-01-04 12:30 UTC, the whole instant. It was
    # the date only (DateUtility.OFFSET_DAYS), with the real time of day,
    # so an ':hour()' window found v3 (00:00 UTC) whenever the suite ran
    # between 00:00 and 00:59 UTC (2026-11-11).
    @pytest.fixture(autouse=True)
    def pinned_now(self, monkeypatch):
        self._pin_clock(monkeypatch=monkeypatch, hour=12)

    @staticmethod
    def _pin_clock(*, monkeypatch: pytest.MonkeyPatch, hour: int) -> None:
        from datetime import datetime, timezone

        pinned = datetime(2026, 1, 4, hour, 30, tzinfo=timezone.utc)
        monkeypatch.setattr(daut, "now", classmethod(lambda cls: pinned))

    @staticmethod
    def _finder(reference: str) -> FilesReferenceFinder3:
        return _finder(
            reference,
            RANGE_HOME,
            CHAIN_RANGE_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=CHAIN_RANGE_LEDGER,
        )

    def _uuids(self, reference: str) -> list:
        return self._finder(reference).query().uuids

    def _data(self, reference: str) -> list:
        return [r.data for r in self._finder(reference).resolve().results]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            ("$ranger.files.:manifest():yesterday()", ["v2"]),
            ("$ranger.files.:yesterday():manifest()", ["v2"]),
            ("$ranger.files.:manifest():today()", ["v3"]),
            ("$ranger.files.:manifest():month()", ["v0", "v1", "v2", "v3", "v4"]),
            ("$ranger.files.:manifest():month():first()", ["v0"]),
            ("$ranger.files.:manifest():last():yesterday()", ["v2"]),
            ("$ranger.files.:manifest():from(1):to(2)", ["v1", "v2"]),
            ("$ranger.files.:manifest():from(-2)", ["v3", "v4"]),
            ("$ranger.files.:manifest():before(2)", ["v0", "v1"]),
            ("$ranger.files.:manifest():from(1):to(3):last()", ["v3"]),
            ('$ranger.files.:manifest():after(:date("2026-01-03"))', ["v3", "v4"]),
            (
                '$ranger.files.:manifest():from(:date("2026-01-02"))'
                ":to(:yesterday())",
                ["v1", "v2"],
            ),
        ],
    )
    def test_the_literal_root_narrows(self, reference, expected):
        assert self._uuids(reference) == expected

    @pytest.mark.parametrize(
        "reference, expected",
        [
            ("$*.files.:manifest():yesterday()", ["l3", "l4"]),
            ("$*.files.:manifest():yesterday():last()", ["l4"]),
            ("$*.files.:manifest():from(1):to(2)", ["l2", "l3"]),
            ('$*.files.:manifest():from(:date("2026-01-03"))', ["l3", "l4", "l5"]),
            ("$:regex(/^b/).files.:manifest():yesterday()", ["l4"]),
            ("$:regex(/^a/).files.:manifest():from(-2)", ["l3", "l5"]),
        ],
    )
    def test_the_ledger_narrows(self, reference, expected):
        # an index range is in ledger order, across named-files, as
        # '$*.csvpaths.:manifest():from(0):to(1)' is
        assert self._uuids(reference) == expected

    def test_the_range_comes_before_the_gate_and_the_pointer(self):
        # the range first keeps v3, v4, and the gate drops the xlsx v3.
        # the gate first would keep v0, v1, v2, v4 and the range v2, v4
        assert self._uuids('$ranger.files.:manifest():from(-2):type("csv")') == [
            "v4"
        ]
        assert self._uuids(
            '$ranger.files.:manifest():type("csv"):from(-2):first()'
        ) == ["v4"]

    def test_resolve_gives_each_entry(self):
        assert self._data("$ranger.files.:manifest():yesterday()") == [
            CHAIN_RANGE_MANIFEST[2]
        ]
        assert self._data("$*.files.:manifest():yesterday()") == [
            CHAIN_RANGE_LEDGER[2],
            CHAIN_RANGE_LEDGER[3],
        ]

    def test_a_field_reads_each_kept_entry(self):
        assert self._data("$ranger.files.:manifest():yesterday():uuid()") == ["v2"]
        assert self._data("$ranger.files.:manifest():from(1):to(2):type()") == [
            "csv",
            "csv",
        ]
        reference = "$*.files.:manifest():yesterday():named_file_name()"
        assert self._data(reference) == ["alpha", "beta"]

    def test_a_window_with_nothing_in_it_finds_nothing(self):
        # 12:30, an hour with no entry
        assert self._uuids("$ranger.files.:manifest():hour()") == []
        assert self._data("$ranger.files.:manifest():hour()") == []

    def test_an_hour_window_finds_the_entry_in_that_hour(self, monkeypatch):
        # the same window, in the hour v3 arrived: not empty by accident
        self._pin_clock(monkeypatch=monkeypatch, hour=0)
        assert self._uuids("$ranger.files.:manifest():hour()") == ["v3"]
        assert self._data("$ranger.files.:manifest():hour()") == [
            CHAIN_RANGE_MANIFEST[3]
        ]

    @pytest.mark.parametrize(
        "reference, message",
        [
            ("$ranger.files.:manifest():yesterday():today()", "more than one"),
            ("$ranger.files.:manifest():yesterday():from(1)", "bare time"),
            (
                '$ranger.files.:manifest():from(1):to(:date("2026-01-03"))',
                "mixing index",
            ),
            ("$ranger.files.:manifest():from(1):after(2)", "two lower-bound"),
            ('$ranger.files.:manifest():from("not-a-date")', "date-mode"),
        ],
    )
    def test_a_bad_range_raises(self, reference, message):
        with pytest.raises(ReferenceException3) as error:
            self._uuids(reference)
        assert message in str(error.value)


class TestManifestChainRuleOne:
    # Rule 1 (manifest_field_functions_proposal.md): several whole manifest
    # entries of one named-file cannot be resolved at once; a pointer must
    # pick one. Rule 3: a field can be read for several. Rule 1a: the
    # ledger under '*' is one file. Before 2026-11-08 the name_one
    # ':manifest()' chain resolved several whole entries, where
    # ':name("x").:manifest()' and CSVPATHS raise. Same fixture as
    # TestManifestChainRanges, "now" pinned to 2026-01-04.
    @pytest.fixture(autouse=True)
    def pinned_now(self):
        from datetime import date

        daut.OFFSET_DAYS = (date(2026, 1, 4) - daut.now().date()).days
        try:
            yield
        finally:
            daut.OFFSET_DAYS = 0

    @staticmethod
    def _finder(reference: str) -> FilesReferenceFinder3:
        return TestManifestChainRanges._finder(reference)

    @pytest.mark.parametrize(
        "reference, expected",
        [
            ("$ranger.files.:manifest():from(1):to(2)", ["v1", "v2"]),
            ("$ranger.files.:manifest():month()", ["v0", "v1", "v2", "v3", "v4"]),
            ('$ranger.files.:manifest():type("csv")', ["v0", "v1", "v2", "v4"]),
            ('$ranger.files.:manifest():type("csv"):from(0)', ["v0", "v1", "v2", "v4"]),
        ],
    )
    def test_several_whole_entries_raise(self, reference, expected):
        finder = self._finder(reference)
        results = finder.query()
        assert results.uuids == expected
        assert results.ambiguous_content_read
        with pytest.raises(ReferenceException3) as error:
            finder.resolve()
        assert "more than one match" in str(error.value)

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # a pointer picks one
            (
                "$ranger.files.:manifest():from(1):to(2):last()",
                [CHAIN_RANGE_MANIFEST[2]],
            ),
            # only one matches
            ("$ranger.files.:manifest():yesterday()", [CHAIN_RANGE_MANIFEST[2]]),
            ('$ranger.files.:manifest():type("xlsx")', [CHAIN_RANGE_MANIFEST[3]]),
            # a field, one value per entry (Rule 3)
            ("$ranger.files.:manifest():from(1):to(2):uuid()", ["v1", "v2"]),
            ('$ranger.files.:manifest():type("csv"):type()', ["csv"] * 4),
            ("$ranger.files.:manifest():uuid()", ["v0", "v1", "v2", "v3", "v4"]),
            # the ledger (Rule 1a)
            (
                "$*.files.:manifest():yesterday()",
                [CHAIN_RANGE_LEDGER[2], CHAIN_RANGE_LEDGER[3]],
            ),
            (
                '$:regex("a").files.:manifest():yesterday()',
                [CHAIN_RANGE_LEDGER[2], CHAIN_RANGE_LEDGER[3]],
            ),
        ],
    )
    def test_these_still_resolve(self, reference, expected):
        finder = self._finder(reference)
        assert not finder.query().ambiguous_content_read
        assert [r.data for r in finder.resolve().results] == expected

    def test_the_name_three_form_agrees(self, tmp_path):
        # the same shapes on ':name("orders.csv").' already raised
        for reference in (
            f"{ORDERS}.:manifest():from(1):to(2)",
            f'{ORDERS}.:manifest():type("csv")',
        ):
            with pytest.raises(ReferenceException3):
                _g_finder(reference, tmp_path).resolve()


class TestTimeWindowExamples:
    # compendium 6.27d/6.27e/6.27g's FILES examples as written, on 6.27f's
    # own date ("now" is 2026-01-02). In FILES name_one is the path and
    # name_three the version (E2), so a window that narrows registrations
    # goes in name_three; in name_one it is a path segment (David,
    # 2026-11-07). acme's orders.csv has versions on Dec 31, Jan 1 (two)
    # and Jan 2; a home named for yesterday, 2026-01-01, has one version
    # from Dec 30.
    MANIFEST = [
        {
            "file": f"inputs/named_files/acme/{home}/{uuid}.csv",
            "file_home": f"inputs/named_files/acme/{home}",
            "uuid": uuid,
            "time": time,
        }
        for home, uuid, time in (
            ("2026-01-01", "d1", "2025-12-30T09:00:00+00:00"),
            ("orders.csv", "o1", "2025-12-31T09:00:00+00:00"),
            ("orders.csv", "o2", "2026-01-01T09:00:00+00:00"),
            ("orders.csv", "o3", "2026-01-01T17:00:00+00:00"),
            ("orders.csv", "o4", "2026-01-02T09:00:00+00:00"),
        )
    ]

    @pytest.fixture(autouse=True)
    def pinned_now(self):
        from datetime import date

        daut.OFFSET_DAYS = (date(2026, 1, 2) - daut.now().date()).days
        try:
            yield
        finally:
            daut.OFFSET_DAYS = 0

    def _query(self, reference: str):
        return _finder(reference, "inputs/named_files/acme", self.MANIFEST).query()

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # 6.27e, the range; 6.27g's own example in the same form
            ("$acme.files.:flatten().:yesterday()", ["o2", "o3"]),
            # 6.27d and 6.27e, the context for a pointer
            ("$acme.files.:flatten().:yesterday():last()", ["o3"]),
            # 6.27d, the direction: before excludes the whole of yesterday
            ("$acme.files.:flatten().:before(:yesterday())", ["d1", "o1"]),
            # 6.27e, the anchor
            (
                "$acme.files.:flatten().:from(:yesterday()):before(:today())",
                ["o2", "o3"],
            ),
            # one level and one file give the same here
            ("$acme.files.*.:yesterday()", ["o2", "o3"]),
            ('$acme.files.:name("orders.csv").:yesterday()', ["o2", "o3"]),
        ],
    )
    def test_the_examples_as_written(self, reference, expected):
        assert self._query(reference).uuids == expected

    def test_in_name_one_a_window_is_a_path_segment(self):
        results = self._query("$acme.files.:yesterday()")
        assert results.files == [pathu.resep("inputs/named_files/acme/2026-01-01")]

    def test_a_pointer_after_it_picks_in_that_home(self):
        # d1 arrived on Dec 30, not yesterday: the window named the home
        assert self._query("$acme.files.:yesterday():last()").uuids == ["d1"]

    def test_the_old_range_form_in_name_one_raises(self):
        with pytest.raises(ReferenceException3) as error:
            self._query("$acme.files.:before(:yesterday())")
        assert "attached directly to name_one" in str(error.value)


class TestNameThreeGateParts:
    def _built(self, reference: str, tmp_path) -> list:
        finder = _g_finder(reference, tmp_path)
        return finder._build_chain(finder.ref.parsed.name_three.functions)

    def test_none_raises(self):
        with pytest.raises(ValueError):
            FilesReferenceFinder3._is_name_three_gate(None)

    def test_which_functions_are_gates(self, tmp_path):
        built = self._built(
            f'{ORDERS}.:last():type("csv"):uuid():template(:does_not_have_value())', tmp_path
        )
        assert [FilesReferenceFinder3._is_name_three_gate(f) for f in built] == [
            False,
            True,
            False,
            True,
        ]

    @pytest.mark.parametrize(
        "field", ['source_port("email")', "on_arrival(:has_value())"]
    )
    def test_a_definition_field_is_not_a_gate(self, field, tmp_path):
        # its argument picks a key or filters definition.json, never the
        # versions, so the last version still comes back
        reference = f"{ORDERS}.:last():{field}"
        built = self._built(reference, tmp_path)
        assert not FilesReferenceFinder3._is_name_three_gate(built[1])
        assert _g_uuids(reference, tmp_path) == ["g3"]

    def test_a_time_window_is_not_a_gate(self, tmp_path):
        built = self._built(f"{ORDERS}.:yesterday()", tmp_path)
        assert not FilesReferenceFinder3._is_name_three_gate(built[0])

    def test_filter_by_gates_rejects_none(self, tmp_path):
        finder = _g_finder(f"{ORDERS}.:last()", tmp_path)
        with pytest.raises(ValueError):
            finder._filter_by_gates(
                reference=finder.ref.parsed, gates=None, candidates=[]
            )
        with pytest.raises(ValueError):
            finder._filter_by_gates(
                reference=finder.ref.parsed, gates=[], candidates=None
            )


class TestNameThreeGates:
    # an argued manifest.json field in name_three filters the versions.
    # it was never applied on query, and on resolve the first field won,
    # the gate's own value included.
    def test_a_gate_filters(self, tmp_path):
        assert _g_uuids(f'{ORDERS}.:type("xlsx"):uuid()', tmp_path) == ["g1"]
        assert _g_uuids(f'{ORDERS}.:type("json"):uuid()', tmp_path) == []

    def test_a_gate_supplies_no_value(self, tmp_path):
        assert _g_values(f'{ORDERS}.:type("csv"):uuid()', tmp_path) == [
            "g0",
            "g2",
            "g3",
        ]
        assert _g_values(f'{ORDERS}.:last():uuid():type("csv")', tmp_path) == ["g3"]

    @pytest.mark.parametrize(
        "chain", [':last():type("xlsx")', ':type("xlsx"):last()']
    )
    def test_the_pointer_picks_from_what_the_gate_leaves(self, chain, tmp_path):
        # the last version is a csv, so a pointer before the gate would
        # find nothing; the last xlsx is g1.
        assert _g_uuids(f"{ORDERS}.{chain}", tmp_path) == ["g1"]

    def test_first_after_a_gate(self, tmp_path):
        assert _g_uuids(f'{ORDERS}.:first():type("xlsx")', tmp_path) == ["g1"]

    @pytest.mark.parametrize(
        "chain",
        [':from(0):to(1):type("csv"):uuid()', ':type("csv"):from(0):to(1):uuid()'],
    )
    def test_the_range_comes_before_the_gate(self, chain, tmp_path):
        # compendium 6.28 (2026-11-02): the csv versions among the first
        # two, not the first two csv versions (that would be g0, g2).
        assert _g_values(f"{ORDERS}.{chain}", tmp_path) == ["g0"]

    def test_range_then_gate_then_pointer(self, tmp_path):
        reference = f'{ORDERS}.:from(0):to(2):type("csv"):last():uuid()'
        assert _g_values(reference, tmp_path) == ["g2"]

    def test_two_gates_are_anded(self, tmp_path):
        reference = f'{ORDERS}.:type("csv"):template(:does_not_have_value()):uuid()'
        assert _g_values(reference, tmp_path) == ["g0", "g3"]

    def test_with_only_a_gate_resolve_gives_the_version_bytes(self, tmp_path):
        # as '.:last()' does without the gate: name_three always points.
        finder = _g_finder(f'{ORDERS}.:last():type("csv")', tmp_path)
        assert finder.query().uuids == ["g3"]
        assert finder.resolve().results[0].data == b"id\ng3\n"

    def test_with_only_a_gate_beside_manifest_resolve_gives_the_entry(self, tmp_path):
        finder = _g_finder(f'{ORDERS}.:last():manifest():type("xlsx")', tmp_path)
        results = finder.resolve().results
        assert [r.data["uuid"] for r in results] == ["g1"]
        assert results[0].path == os.path.join(str(tmp_path), "orders", "manifest.json")

    def test_a_gate_beside_manifest_is_still_a_whole_entry_read(self, tmp_path):
        # several whole entries at once: flagged, as without the gate
        results = _g_finder(f'{ORDERS}.:manifest():type("csv")', tmp_path).query()
        assert results.uuids == ["g0", "g2", "g3"]
        assert results.ambiguous_content_read
        reference = f'{ORDERS}.:manifest():type("csv"):uuid()'
        results = _g_finder(reference, tmp_path).query()
        assert not results.ambiguous_content_read

    def test_gates_apply_in_each_file_home(self, tmp_path):
        reference = '$orders.files.:all().:last():type("xlsx")'
        assert _g_uuids(reference, tmp_path) == ["g1", "h0"]

    def test_gates_apply_in_each_file_home_with_a_range(self, tmp_path):
        reference = '$orders.files.:all().:from(0):to(1):type("csv"):uuid()'
        assert _g_values(reference, tmp_path) == ["g0", "h1"]


class TestNameThreeValueField:
    # compendium 5.20b: the last value field wins, with a warning.
    def test_the_last_field_wins(self, tmp_path):
        assert _g_values(f"{ORDERS}.:last():fingerprint():template()", tmp_path) == [
            ""
        ]
        assert _g_values(f"{ORDERS}.:last():template():fingerprint()", tmp_path) == [
            "f-g3"
        ]

    def test_two_value_fields_warn(self, tmp_path):
        finder = _g_finder(f"{ORDERS}.:last():fingerprint():uuid()", tmp_path)
        logger = _FakeLogger()
        finder.csvpaths.logger = logger
        assert [r.data for r in finder.resolve().results] == ["g3"]
        assert len(logger.warnings) == 1

    def test_a_gate_does_not_count_toward_the_warning(self, tmp_path):
        finder = _g_finder(f'{ORDERS}.:last():type("csv"):uuid()', tmp_path)
        logger = _FakeLogger()
        finder.csvpaths.logger = logger
        assert [r.data for r in finder.resolve().results] == ["g3"]
        assert logger.warnings == []


class TestStarNameThreeGates:
    # the same rules under '*' traversal.
    def test_a_gate_filters_the_pool(self, tmp_path):
        reference = '$*.files.:name("orders.csv").:type("xlsx"):uuid()'
        assert _g_values(reference, tmp_path, star=True) == ["g1"]

    def test_a_gate_with_no_pointer(self, tmp_path):
        reference = '$*.files.*.:type("xlsx")'
        assert _g_uuids(reference, tmp_path, star=True) == ["g1", "h0"]

    def test_the_pointer_picks_from_what_the_gate_leaves(self, tmp_path):
        # h1 (other.csv) is the latest arrival, and a csv
        reference = '$*.files.*.:type("xlsx"):last():uuid()'
        assert _g_values(reference, tmp_path, star=True) == ["h0"]

    def test_gates_apply_in_each_file_home(self, tmp_path):
        reference = '$*.files.:all().:last():type("xlsx")'
        assert _g_uuids(reference, tmp_path, star=True) == ["g1", "h0"]

    def test_the_range_comes_before_the_gate(self, tmp_path):
        reference = '$*.files.:name("orders.csv").:from(0):to(1):type("csv"):uuid()'
        assert _g_values(reference, tmp_path, star=True) == ["g0"]

    def test_the_last_field_wins(self, tmp_path):
        reference = '$*.files.:name("orders.csv").:last():fingerprint():template()'
        assert _g_values(reference, tmp_path, star=True) == [""]

    def test_with_only_a_gate_resolve_gives_the_version_bytes(self, tmp_path):
        finder = _g_finder('$*.files.*.:type("xlsx"):last()', tmp_path, star=True)
        assert finder.resolve().results[0].data == b"id\nh0\n"


class TestAttachedFieldFunctionsMessage:
    # E2, option C (David, 2026-11-02): a field chain attached to name_one
    # with no '.' still raises, and the message now gives the reference
    # with the dot, since name_one picks the file and name_three picks the
    # version and reads its fields.
    FIELD_ERROR = "does not support field functions attached directly to name_one"

    def test_none_raises(self):
        with pytest.raises(ValueError):
            FilesReferenceFinder3._attached_functions_message(
                name_one=None, star_traversal=False
            )

    @pytest.mark.parametrize(
        "reference, suggestion",
        [
            (
                '$alpha.files.:name("one.csv"):fingerprint():template()',
                ':name("one.csv").:fingerprint():template()',
            ),
            (
                '$alpha.files.:name("one.csv"):last():uuid()',
                ':name("one.csv").:last():uuid()',
            ),
            ("$alpha.files.*:uuid()", "*.:uuid()"),
        ],
    )
    def test_a_literal_root_gives_the_dot_form(self, reference, suggestion):
        with pytest.raises(ReferenceException3) as error:
            _finder(reference, ALPHA_HOME, ALPHA_MANIFEST).query()
        assert self.FIELD_ERROR in str(error.value)
        assert f"'{suggestion}'" in str(error.value)

    def test_star_traversal_gives_the_dot_form(self):
        with pytest.raises(ReferenceException3) as error:
            _star_finder('$*.files.:name("one.csv"):uuid()').query()
        assert self.FIELD_ERROR in str(error.value)
        assert "':name(\"one.csv\").:uuid()'" in str(error.value)

    def test_the_suggestion_is_a_working_reference(self):
        results = _finder(
            '$alpha.files.:name("one.csv").:last():uuid()', ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert [r.data for r in results.results] == ["u-one-2"]

    def test_without_a_field_the_message_is_unchanged(self):
        with pytest.raises(ReferenceException3) as error:
            _finder(
                '$alpha.files.:name("one.csv"):from(1)', ALPHA_HOME, ALPHA_MANIFEST
            ).query()
        assert str(error.value) == (
            "FilesReferenceFinder3 does not support functions attached "
            "directly to name_one -- put the version-selecting function in "
            "name_three instead."
        )
        with pytest.raises(ReferenceException3) as error:
            _star_finder('$*.files.:name("one.csv"):from(1)').query()
        assert "for '*' traversal" in str(error.value)
        assert self.FIELD_ERROR not in str(error.value)

    def test_a_lone_pointer_and_a_lone_gate_still_work(self):
        finder = _finder(
            '$alpha.files.:name("one.csv"):last()', ALPHA_HOME, ALPHA_MANIFEST
        )
        assert finder.query().uuids == ["u-one-2"]
        finder = _finder(
            '$alpha.files.:name("one.csv"):manifest()', ALPHA_HOME, ALPHA_MANIFEST
        )
        assert finder.query().uuids == ["u-one-1", "u-one-2"]


#
# E3 (2026-11-02): ':definition()' with a field chain. ':definition()'
# names one file per named-file, like ':manifest()'; definition.json has
# no file home or version, so the chain reads and filters that one record.
#
DEF_ALPHA = {
    "template": ":0/:filename",
    "on_arrival": {"named_paths_group": "checks", "run_method": "collect_paths"},
    "sources": {
        "email": {"address": "mail.local", "port": 22, "username": "u", "password": "p"}
    },
}
DEF_BETA = {"template": ":filename"}


def _def_finder(reference: str) -> FilesReferenceFinder3:
    finder = _finder(
        reference,
        STAR_ALPHA_HOME,
        STAR_ALPHA_MANIFEST,
        by_name=STAR_BY_NAME,
        definitions={"alpha": DEF_ALPHA, "beta": DEF_BETA},
    )
    finder.csvpaths.logger = _FakeLogger()
    return finder


def _def_values(reference: str) -> list:
    return [r.data for r in _def_finder(reference).resolve().results]


def _def_path(home: str) -> str:
    return pathu.resep(f"{home}/definition.json")


class TestDefinitionChainParts:
    def _calls(self, reference: str):
        name_one = _def_finder(reference).ref.parsed.name_one
        return FilesReferenceFinder3._definition_chain(name_one=name_one)

    def test_none_raises(self):
        with pytest.raises(ValueError):
            FilesReferenceFinder3._definition_chain(name_one=None)

    @pytest.mark.parametrize(
        "reference, names",
        [
            ("$alpha.files.:definition():on_arrival()", ["on_arrival"]),
            ("$alpha.files.:on_arrival():definition()", ["on_arrival"]),
            ("$alpha.files.:definition(:on_arrival(:has_value()))", ["on_arrival"]),
            (
                "$alpha.files.:definition(:on_arrival(:has_value())):template()",
                ["on_arrival", "template"],
            ),
            # a bare definition field is a one-field chain (2026-11-03)
            ("$alpha.files.:on_arrival()", ["on_arrival"]),
            ("$alpha.files.:template(:has_value())", ["template"]),
            ('$*.files.:source_port("email")', ["source_port"]),
        ],
    )
    def test_the_field_calls(self, reference, names):
        assert [c.name for c in self._calls(reference)] == names

    @pytest.mark.parametrize(
        "reference",
        [
            "$alpha.files.:definition()",
            '$alpha.files.:name("orders.csv"):definition()',
            "$alpha.files.:manifest():uuid()",
        ],
    )
    def test_other_shapes_are_not_claimed(self, reference):
        assert self._calls(reference) is None

    def test_a_retired_home_raises(self):
        # ':home()' was retired 2026-11-03; it no longer scopes a
        # ':definition()' chain.
        with pytest.raises(ReferenceException3) as error:
            self._calls("$*.files.:home():definition(:on_arrival(:has_value()))")
        assert "':home()' is not supported" in str(error.value)

    @pytest.mark.parametrize("field", ["uuid()", "fingerprint()", "named_file_home()"])
    def test_a_field_not_in_definition_json_raises(self, field):
        with pytest.raises(ReferenceException3) as error:
            self._calls(f"$alpha.files.:definition():{field}")
        assert "does not read a named-file's definition.json" in str(error.value)

    @pytest.mark.parametrize("function", ["last()", "index(1)", "from(1)", "today()"])
    def test_a_version_selector_raises(self, function):
        with pytest.raises(ReferenceException3) as error:
            self._calls(f"$alpha.files.:definition():{function}")
        assert "definition.json is not versioned" in str(error.value)


class TestDefinitionChain:
    def test_a_field_value(self):
        # compendium 6.19 and NRE 345: "returns the arrival activation
        # field value". these raised before.
        assert _def_values("$alpha.files.:definition():on_arrival()") == [
            DEF_ALPHA["on_arrival"]
        ]
        assert _def_values("$alpha.files.:definition():run_method()") == [
            "collect_paths"
        ]
        assert _def_values("$alpha.files.:definition():template()") == [":0/:filename"]

    def test_a_key_argument_is_a_value(self):
        assert _def_values('$alpha.files.:definition():source_port("email")') == [22]

    def test_the_same_value_as_the_bare_field(self):
        for field in ("on_arrival()", "run_method()", 'source_port("email")'):
            assert _def_values(f"$alpha.files.:definition():{field}") == _def_values(
                f"$alpha.files.:{field}"
            )

    def test_the_query_path_is_the_definition_file(self):
        results = _def_finder("$alpha.files.:definition():on_arrival()").query()
        assert results.files == [_def_path(STAR_ALPHA_HOME)]
        assert results.uuids == [None]

    @pytest.mark.parametrize(
        "reference",
        [
            "$NAME.files.:definition(:on_arrival(:has_value()))",
            "$NAME.files.:definition():on_arrival(:has_value())",
            "$NAME.files.:on_arrival(:has_value()):definition()",
        ],
    )
    def test_a_predicate_filters_nested_or_chained(self, reference):
        # 6.19: the definition is returned only if an arrival activation
        # is found
        alpha = _def_finder(reference.replace("NAME", "alpha")).query()
        assert alpha.files == [_def_path(STAR_ALPHA_HOME)]
        assert _def_finder(reference.replace("NAME", "beta")).query().results == []

    def test_a_filter_with_a_value(self):
        reference = "$*.files.:definition():on_arrival(:has_value()):template()"
        assert _def_values(reference) == [":0/:filename"]

    def test_two_filters_are_anded(self):
        base = "$*.files.:definition():on_arrival(:has_value())"
        assert _def_finder(f"{base}:template(:does_not_have_value())").query().results == []
        assert _def_finder(f"{base}:template(:has_value())").query().files == [
            _def_path(STAR_ALPHA_HOME)
        ]

    def test_the_last_value_field_wins_with_a_warning(self):
        finder = _def_finder("$alpha.files.:definition():template():run_method()")
        assert [r.data for r in finder.resolve().results] == ["collect_paths"]
        assert len(finder.csvpaths.logger.warnings) == 1
        reversed_ = "$alpha.files.:definition():run_method():template()"
        assert _def_values(reversed_) == [":0/:filename"]

    def test_a_filter_does_not_count_toward_the_warning(self):
        finder = _def_finder(
            "$alpha.files.:definition():on_arrival(:has_value()):template()"
        )
        finder.resolve()
        assert finder.csvpaths.logger.warnings == []

    def test_star_gives_each_matching_named_file(self):
        # compendium 6.35's own example, which raised before
        results = _def_finder("$*.files.:definition(:on_arrival(:has_value()))").query()
        assert results.files == [_def_path(STAR_ALPHA_HOME)]
        assert not results.ambiguous_content_read
        results = _def_finder("$*.files.:definition(:on_arrival(:does_not_have_value()))").query()
        assert results.files == [_def_path(STAR_BETA_HOME)]

    def test_star_values_come_from_each_named_files_own_definition(self):
        values = _def_values("$*.files.:definition():template()")
        assert sorted(values) == [":0/:filename", ":filename"]

    def test_star_with_several_whole_files_is_flagged(self):
        # compendium 5.8: several definition files can be queried, not
        # resolved
        results = _def_finder("$*.files.:definition(:template(:has_value()))").query()
        assert len(results.results) == 2
        assert results.ambiguous_content_read
        results = _def_finder("$*.files.:definition():template()").query()
        assert not results.ambiguous_content_read

    def test_a_regex_root(self):
        assert _def_values("$:regex(/^be/).files.:definition():template()") == [
            ":filename"
        ]

    def test_name_three_raises(self):
        with pytest.raises(ReferenceException3) as error:
            _def_finder("$alpha.files.:definition():template().:last()").query()
        assert "':definition()' chain with name_three" in str(error.value)

    def test_with_only_a_filter_resolve_gives_the_definition_file(self, tmp_path):
        home = tmp_path / "alpha"
        home.mkdir()
        (home / "definition.json").write_text('{"on_arrival": {}}', encoding="utf-8")
        finder = _finder(
            "$alpha.files.:definition(:on_arrival(:has_value()))",
            str(home),
            [],
            definitions={"alpha": DEF_ALPHA},
        )
        assert finder.resolve().results[0].data == b'{"on_arrival": {}}'


class TestBareDefinitionField:
    # a bare definition field means the one-field ':definition()' chain
    # (2026-11-03): ':template(:has_value())' is
    # ':definition(:template(:has_value()))' and ':template()' is
    # ':definition():template()'. Before, a bare filter resolved to the
    # field's value, not the definition.json (D), and every bare field
    # raised on resolve under '*', ':regex()' and ':choice()'.
    @pytest.mark.parametrize(
        "bare, chain",
        [
            ("$alpha.files.:template()", "$alpha.files.:definition():template()"),
            (
                '$alpha.files.:source_port("email")',
                '$alpha.files.:definition():source_port("email")',
            ),
            ("$*.files.:template()", "$*.files.:definition():template()"),
            (
                '$:choice("beta").files.:template()',
                '$:choice("beta").files.:definition():template()',
            ),
            (
                "$:regex(/^al/).files.:on_arrival()",
                "$:regex(/^al/).files.:definition():on_arrival()",
            ),
        ],
    )
    def test_a_value_is_the_same_as_the_chain(self, bare, chain):
        assert _def_finder(bare).query().files == _def_finder(chain).query().files
        assert _def_values(bare) == _def_values(chain)

    @pytest.mark.parametrize(
        "bare, chain",
        [
            (
                "$*.files.:on_arrival(:has_value())",
                "$*.files.:definition(:on_arrival(:has_value()))",
            ),
            (
                "$*.files.:on_arrival(:does_not_have_value())",
                "$*.files.:definition(:on_arrival(:does_not_have_value()))",
            ),
            (
                "$alpha.files.:template(:does_not_have_value())",
                "$alpha.files.:definition(:template(:does_not_have_value()))",
            ),
            (
                "$*.files.:template(:has_value())",
                "$*.files.:definition(:template(:has_value()))",
            ),
        ],
    )
    def test_a_filter_queries_the_same_as_the_chain(self, bare, chain):
        bare_results = _def_finder(bare).query()
        chain_results = _def_finder(chain).query()
        assert bare_results.files == chain_results.files
        assert (
            bare_results.ambiguous_content_read
            == chain_results.ambiguous_content_read
        )

    def test_star_values_are_not_flagged(self):
        # a value per named-file, not several whole files; this raised
        # "cannot resolve more than one match" before.
        assert not _def_finder("$*.files.:template()").query().ambiguous_content_read
        assert sorted(_def_values("$*.files.:template()")) == [
            ":0/:filename",
            ":filename",
        ]

    def test_a_key_argument_under_choice(self):
        # raised "unhashable type: 'FunctionCall3'" before.
        assert _def_values('$:choice("alpha").files.:source_port("email")') == [22]

    def _real_homes(self, tmp_path):
        homes = {}
        for name, text in {
            "alpha": '{"template": ":0/:filename"}',
            "beta": "{}",
        }.items():
            home = tmp_path / name
            home.mkdir()
            (home / "definition.json").write_text(text, encoding="utf-8")
            homes[name] = (str(home), [])
        return homes

    @pytest.mark.parametrize(
        "reference",
        [
            "$alpha.files.:template(:has_value())",
            "$*.files.:template(:has_value())",
            '$:choice("alpha").files.:template(:has_value())',
        ],
    )
    def test_a_filter_resolves_to_the_definition_file(self, tmp_path, reference):
        # D: a filter gives no value. this gave ":0/:filename" at a
        # literal root and raised under '*' and ':choice()' before.
        homes = self._real_homes(tmp_path)
        finder = _finder(
            reference,
            homes["alpha"][0],
            [],
            by_name=homes,
            definitions={"alpha": {"template": ":0/:filename"}, "beta": {}},
        )
        assert finder.resolve().results[0].data == b'{"template": ":0/:filename"}'

    def test_name_three_raises(self):
        with pytest.raises(ReferenceException3):
            _def_finder("$alpha.files.:on_arrival().:last()").query()


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
        # gamma has no one-level file, so '*' gives it no group
        star_results = _flatten_star_finder("$*.files.*.:last()").query()
        assert star_results.uuids == ["u-one-2", "u-two-2"]
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

    def test_range_with_no_pointer_applies_within_each_group(self):
        # built 2026-10-21 -- David's own worked example (now in the
        # compendium's Wildcards section): "$*.files.:groups().
        # :from(0):to(1)" -> "first 2 registrations for each group
        # found in name_one." zero.csv/one.csv/two.csv each have 1 or 2
        # entries here, so "first 2" keeps everything (no group has a
        # 3rd to exclude) -- this test confirms the combination no
        # longer raises and resolves to every real entry, not that it
        # narrows (see the next test for the narrowing proof).
        results = _star_finder("$*.files.:groups().:from(0):to(1)").query()
        assert set(results.uuids) == {
            "u-zero-1",
            "u-one-1",
            "u-one-2",
            "u-two-1",
            "u-two-2",
        }

    def test_range_without_a_pointer_reduces_within_each_group_not_pooled(self):
        # the actual GROUP-vs-POOL proof: the pooled '*' equivalent
        # ("$*.files.*.:last()", TestStarTraversalFlatten above) gives
        # ONE overall answer (u-two-2, the true global-latest). Grouping
        # first gives one PER group instead -- the same convention
        # already built/tested for a plain pointer in GROUP mode, now
        # extended to a range.
        results = _star_finder("$*.files.:groups().:from(-1)").query()
        assert set(results.uuids) == {"u-zero-1", "u-one-2", "u-two-2"}


#
# two named-files for the '*' traversal ':definition()' and worksheet
# tests below. The fixture once also served ':home()', retired
# 2026-11-03.
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


class TestStarTraversalWorksheet:
    def test_worksheet_marker_is_rejected(self):
        # not-yet-supported sweep #6, 2026-10-20: '#worksheet' means
        # content from exactly one specific XLSX file -- '*' traversal
        # matches across every named-file by definition, so this is a
        # settled rejection, not a pending gap.
        with pytest.raises(ReferenceException3):
            _home_star_finder("$*.files.*#Summary.:last()").query()


class TestStarTraversalDefinition:
    # bare ':definition()' during '*' traversal, added 2026-08-27, and
    # ':definition()' with a predicate-argued field (E3's chain). Neither
    # takes name_three -- definition.json is never versioned, so there is
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

    def test_bare_definition_combined_with_name_three_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _home_star_finder("$*.files.:definition().:last()").query()

    def test_on_arrival_predicate_filters_to_named_files_that_have_it_set(self):
        # the generic predicate-argument filtering mechanism (added
        # 2026-10-17, closing the deferred-work bucket list's own
        # "Predicate-argument field accessors" entry) -- its own
        # motivating worked example (compendium 6.35):
        # "$*.files.:definition(:on_arrival(:has_value()))" -- "which
        # named-files have on_arrival set." Only alpha has on_arrival
        # configured.
        results = _finder(
            "$*.files.:definition(:on_arrival(:has_value()))",
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
        # bytes for a survivor) is proven by
        # test_on_arrival_predicate_survivor_resolves_its_real_definition_
        # bytes below -- this test is only about WHICH named-files
        # survive the predicate filter.
        assert results.files == [pathu.resep(f"{HOME_STAR_ALPHA_HOME}/definition.json")]
        assert results.ambiguous_content_read is False

    def test_on_arrival_predicate_with_no_survivors_gives_empty_results(self):
        results = _finder(
            "$*.files.:definition(:on_arrival(:has_value()))",
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
                "$*.files.:definition(:on_arrival(:has_value())).:last()",
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
            "$*.files.:definition(:on_arrival(:has_value()))",
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

    def test_all_combined_with_a_range_applies_within_each_group(self):
        # built 2026-10-21 (David: "isn't :groups() being different
        # from :flatten() the whole point? Wasn't that already the
        # answer?") -- yes: GROUP mode's own established convention
        # (already built/tested for a plain pointer just above) is
        # "reduce independently within each distinct file_home," and a
        # range is just a multi-valued pointer, so it follows the same
        # convention. "zero.csv" has one version (the window's own
        # last 1 is itself); "one.csv" has two (the window's own last 1
        # is u-one-2, its own last array entry) -- NOT the pooled last 1
        # across everything (which would have been u-one-2 alone).
        results = _finder(
            "$alpha.files.:all().:from(-1)", ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert set(results.uuids) == {"u-zero-1", "u-one-2"}

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


class TestHomeIsRetired:
    # ':home()' was retired 2026-11-03 (David). It was a zero-level
    # placeholder that matched nothing a real registration writes: a
    # no-template file home is "<named-file>/<filename>", never the
    # named-file home itself, which is all HOME_TEST_MANIFEST's first
    # two entries have. It is no longer a registered function, so every
    # use raises.
    def test_it_is_not_registered(self):
        assert ReferenceFunctionFactory.get_registered_class("home") is None

    @pytest.mark.parametrize(
        "reference",
        [
            "$homer.files.:home()",
            "$homer.files.:home().:last()",
            '$homer.files.:home("x").:last()',
            '$homer.files.:name("orders.csv").:first():home()',
            "$*.files.:home()",
            "$*.files.:home().:last()",
            "$*.files.:home():definition()",
            "$*.files.:home():definition(:on_arrival(:has_value()))",
        ],
    )
    def test_every_use_raises(self, reference):
        with pytest.raises(ReferenceException3):
            _finder(
                reference,
                HOME_TEST_HOME,
                HOME_TEST_MANIFEST,
                by_name={"homer": (HOME_TEST_HOME, HOME_TEST_MANIFEST)},
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

# orders.csv registered twice, for a filter that leaves the pointer a choice
TWO_ORDERS_MANIFEST = FINGERPRINT_MANIFEST + [
    {
        "file": "inputs/named_files/finn/orders.csv/bbbb.csv",
        "file_home": "inputs/named_files/finn/orders.csv",
        "uuid": "u-orders-2",
        "fingerprint": "bbbb",
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

    def test_combined_with_name_three_is_rejected(self):
        # a fingerprint already identifies one specific version -- no
        # further narrowing is meaningful. Settled, not a gap -- see
        # query()'s own comment.
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

    # in name_three an argued ':fingerprint()' filters the versions, then
    # the pointer picks, as in RESULTS (David, 2026-11-06; 6.44). It used
    # to raise, which kept the argument from being ignored.
    @pytest.mark.parametrize(
        "reference, expected",
        [
            (
                '$finn.files.:name("orders.csv").:last():fingerprint("aaaa")',
                ["u-orders-1"],
            ),
            (
                '$finn.files.:name("orders.csv").:fingerprint("aaaa"):last()',
                ["u-orders-1"],
            ),
            (
                '$finn.files.:name("orders.csv").:first():fingerprint("bbbb")',
                ["u-orders-2"],
            ),
            (
                '$finn.files.:name("orders.csv").:all():fingerprint("bbbb")',
                ["u-orders-2"],
            ),
            ('$finn.files.:name("orders.csv").:last():fingerprint("cccc")', []),
        ],
    )
    def test_an_argument_in_name_three_filters(self, reference, expected):
        results = _finder(reference, FINGERPRINT_HOME, TWO_ORDERS_MANIFEST).query()
        assert results.uuids == expected

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
    # already has (see test_an_argument_in_name_three_filters above for
    # what an argument beside a pointer does) --
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

    # in name_three it filters, the same as ':fingerprint()' (2026-11-06)
    @pytest.mark.parametrize(
        "reference, expected",
        [
            (
                '$finn.files.:name("orders.csv").:last():uuid("u-orders-1")',
                ["u-orders-1"],
            ),
            (
                '$finn.files.:name("orders.csv").:uuid("u-orders-1"):last()',
                ["u-orders-1"],
            ),
            (
                '$finn.files.:name("orders.csv").:first():uuid("u-orders-2")',
                ["u-orders-2"],
            ),
            ('$finn.files.:name("orders.csv").:last():uuid("x")', []),
        ],
    )
    def test_an_argument_in_name_three_filters(self, reference, expected):
        results = _finder(reference, FINGERPRINT_HOME, TWO_ORDERS_MANIFEST).query()
        assert results.uuids == expected

    def test_a_filter_and_a_value_field_together(self):
        ref = (
            '$finn.files.:name("orders.csv").:last()'
            ':uuid("u-orders-1"):fingerprint()'
        )
        results = _finder(ref, FINGERPRINT_HOME, TWO_ORDERS_MANIFEST).resolve()
        assert [r.data for r in results.results] == ["aaaa"]


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
        "status": "failed",
        "uuid": "fail-1",
        "file_path": None,
        "origin_path": "/tmp/orders1.csv",
    },
    {
        "named_file_name": "orders",
        "status": "complete",
        "uuid": "ok-1",
        "file_path": "inputs/named_files/orders/orders.csv/aaaa.csv",
    },
    {
        "named_file_name": "invoices",
        "status": "failed",
        "uuid": "fail-2",
        "file_path": None,
        "origin_path": "/tmp/invoices1.csv",
    },
]

# a deleted version: in the ledger, "complete", but in no live manifest
STATUS_GONE = {
    "named_file_name": "orders",
    "status": "complete",
    "uuid": "gone-1",
    "file_path": "inputs/named_files/orders/orders.csv/gone.csv",
}
STATUS_BY_NAME = {
    "orders": (
        "inputs/named_files/orders",
        [
            {
                "file": "inputs/named_files/orders/orders.csv/aaaa.csv",
                "file_home": "inputs/named_files/orders/orders.csv",
                "uuid": "ok-1",
            }
        ],
    ),
    "invoices": ("inputs/named_files/invoices", []),
}


class TestStatusGate:
    # ':status()' widened 2026-10-18 to also cover FILES -- the global
    # arrivals ledger's own "status" field (a failure message),
    # confirmed live by tracing the real registration code
    # (file_manager.py's own "mdata.status = 'failed'",
    # written only to files_root_manifest, never a per-name manifest).
    # normative_reference_examples.txt's own worked example: "select
    # named-files registrations for orders that failed" --
    # "$*.files.:status(\"failed\"):named_file_name(
    # \"orders\")". Both the '*' form AND the literal-root form are
    # built -- David confirmed the literal form is at least as common
    # an operational need ("if you were inspecting a run that should
    # have happened overnight you would know what status you were
    # looking for... we know those high risk files by name").
    # changed 2026-11-01 (C1 bare-half revert, agreed with David): a
    # bare ':status()' gates the live versions only, at '*' and at a
    # literal root; each version's status is read from its ledger entry.
    # A failure is never a live version, so it is reached only through
    # the ledger set, ':manifest():status("failed")' (NRE 253, rewritten
    # by David). These tests used to select the failures directly.
    @staticmethod
    def _status_finder(reference: str) -> FilesReferenceFinder3:
        return _finder(
            reference,
            TYPE_HOME,
            [],
            ledger=STATUS_LEDGER + [STATUS_GONE],
            by_name=STATUS_BY_NAME,
            inputs_files_path="inputs/named_files",
        )

    def test_the_old_normative_example_is_legal_but_finds_nothing(self):
        results = self._status_finder(
            '$*.files.:status("failed"):named_file_name("orders")'
        ).query()
        assert results.results == []

    def test_star_root_bare_status_finds_no_failure(self):
        assert self._status_finder('$*.files.:status("failed")').query().results == []

    def test_star_root_bare_status_gates_the_live_versions(self):
        # gone-1 is "complete" in the ledger, but deleted, so it drops out
        results = self._status_finder('$*.files.:status("complete")').query()
        assert results.uuids == ["ok-1"]
        assert results.files == ["inputs/named_files/orders/orders.csv/aaaa.csv"]

    def test_literal_root_bare_status_gates_its_live_versions(self):
        finder = self._status_finder('$orders.files.:status("failed")')
        assert finder.query().results == []
        results = self._status_finder('$orders.files.:status("complete")').query()
        assert results.uuids == ["ok-1"]

    def test_literal_root_combined_with_named_file_name_chain(self):
        results = self._status_finder(
            '$orders.files.:status("complete"):named_file_name("orders")'
        ).query()
        assert results.uuids == ["ok-1"]

    def test_the_ledger_set_finds_the_failures(self):
        results = self._status_finder('$*.files.:manifest():status("failed")').query()
        assert results.uuids == ["fail-1", "fail-2"]
        assert results.files == ["inputs/named_files/manifest.json"] * 2

    def test_the_new_normative_example_finds_the_orders_failure(self):
        results = self._status_finder(
            '$*.files.:manifest():status("failed"):named_file_name("orders")'
        ).query()
        assert results.uuids == ["fail-1"]

    def test_no_match_gives_empty(self):
        assert self._status_finder('$*.files.:status("nope")').query().results == []

    def test_name_three_pointer_star_root(self):
        # not-yet-supported sweep #2, 2026-10-20: a lone version-
        # selecting pointer in name_three reduces the status-filtered
        # matches to one (see _pointer_into_status_matches()).
        results = self._status_finder('$*.files.:status("complete").:last()').query()
        assert results.uuids == ["ok-1"]

    def test_name_three_pointer_literal_root(self):
        results = self._status_finder(
            '$orders.files.:status("complete").:first()'
        ).query()
        assert results.uuids == ["ok-1"]

    def test_name_three_index_pointer(self):
        results = self._status_finder('$*.files.:status("complete").:index(0)').query()
        assert results.uuids == ["ok-1"]
        assert self._status_finder(
            '$*.files.:status("complete").:index(1)'
        ).query().results == []

    def test_name_three_pointer_narrows_a_named_file_name_chain_too(self):
        results = self._status_finder(
            '$*.files.:status("complete"):named_file_name("orders").:first()'
        ).query()
        assert results.uuids == ["ok-1"]

    def test_name_three_pointer_no_match_gives_empty(self):
        results = self._status_finder('$*.files.:status("nope").:last()').query()
        assert results.results == []

    def test_name_three_field_accessor_is_rejected(self):
        # the ledger-vs-manifest plumbing a chained field accessor would
        # need in _extract_data() is not built -- see
        # _pointer_into_status_matches()'s own docstring. Only a lone
        # pointer is supported.
        with pytest.raises(ReferenceException3):
            _finder(
                '$*.files.:status("failed").:last():uuid()',
                TYPE_HOME,
                [],
                ledger=STATUS_LEDGER,
            ).query()

    def test_name_three_literal_body_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$orders.files.:status("failed").some_fingerprint',
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


#
# name_three fixture (2026-11-06): orders.csv has two versions. Neither
# per-name entry holds a status or lifecycle; each registration's arrivals
# ledger entry does. o1 was registered before harmonization PR 6, so its
# ledger entry has neither.
#
N3_HOME = "inputs/named_files/orders"
N3_MANIFEST = [
    {
        "file": f"{N3_HOME}/orders.csv/{uuid}.csv",
        "file_home": f"{N3_HOME}/orders.csv",
        "uuid": uuid,
        "time": f"2026-01-0{day}T00:00:00+00:00",
    }
    for uuid, day in (("o1", 1), ("o2", 2))
]
N3_LEDGER = [
    {"named_file_name": "orders", "uuid": "o1", "file_path": N3_MANIFEST[0]["file"]},
    {
        "named_file_name": "orders",
        "uuid": "o2",
        "file_path": N3_MANIFEST[1]["file"],
        "status": "complete",
        "lifecycle": "active",
    },
]


def _n3_finder(reference: str) -> FilesReferenceFinder3:
    return _finder(
        reference,
        N3_HOME,
        [dict(e) for e in N3_MANIFEST],
        ledger=[dict(e) for e in N3_LEDGER],
        by_name={"orders": (N3_HOME, [dict(e) for e in N3_MANIFEST])},
        inputs_files_path="inputs/named_files",
    )


class TestLedgerOnlyFieldsAtNameThree:
    # ':lifecycle()' and ':status()' at name_three (David, 2026-11-06): a
    # registration's own value, read from its arrivals ledger entry by the
    # version's uuid. Both raised "is not legal at name_three for files".
    @pytest.mark.parametrize(
        "reference, expected",
        [
            ('$orders.files.:name("orders.csv").:last():lifecycle()', ["active"]),
            ('$orders.files.:name("orders.csv").:last():status()', ["complete"]),
            # absence implies nothing
            ('$orders.files.:name("orders.csv").:first():lifecycle()', [None]),
            ('$orders.files.:name("orders.csv").:first():status()', [None]),
        ],
    )
    def test_a_version_reads_its_own_registration(self, reference, expected):
        assert [r.data for r in _n3_finder(reference).resolve().results] == expected

    @pytest.mark.parametrize(
        "reference, expected",
        [
            ('$orders.files.:name("orders.csv").:all():lifecycle("active")', ["o2"]),
            ('$orders.files.:name("orders.csv").:lifecycle("active"):first()', ["o2"]),
            ('$orders.files.:name("orders.csv").:first():lifecycle("active")', ["o2"]),
            ('$orders.files.:name("orders.csv").:all():status("complete")', ["o2"]),
            ('$orders.files.:name("orders.csv").:all():status("failed")', []),
            (
                '$orders.files.:name("orders.csv").:all():status("complete")'
                ':lifecycle("active")',
                ["o2"],
            ),
            ('$*.files.:flatten().:lifecycle("active")', ["o2"]),
        ],
    )
    def test_a_name_three_gate(self, reference, expected):
        assert _n3_finder(reference).query().uuids == expected

    def test_a_gate_with_a_value(self):
        results = _n3_finder(
            '$orders.files.:name("orders.csv").:all():lifecycle("active"):uuid()'
        ).resolve()
        assert [r.data for r in results.results] == ["o2"]


class TestLifecycleGateOnTheFilesLedger:
    # ':lifecycle()' (2026-11-05). STATUS_LEDGER's entries have no
    # lifecycle, as entries written before harmonization PR 6 don't:
    # absence implies nothing, so they match neither value (David,
    # 2026-10-29). See test_lifecycle_end_to_end.py for the real ledgers.
    @pytest.mark.parametrize(
        "reference",
        [
            '$*.files.:manifest():lifecycle("active")',
            '$*.files.:manifest():lifecycle("deleted")',
            '$*.files.:lifecycle("active")',
            '$*.files.:status("complete"):lifecycle("active")',
        ],
    )
    def test_an_entry_with_no_lifecycle_matches_neither(self, reference):
        assert TestStatusGate._status_finder(reference).query().results == []

    def test_the_field_reads_none_for_an_entry_with_no_lifecycle(self):
        finder = TestStatusGate._status_finder("$*.files.:manifest():lifecycle()")
        assert {r.data for r in finder.resolve().results} == {None}

    @pytest.mark.parametrize(
        "reference",
        [
            '$*.files.:status("complete"):named_file_name("orders")',
            # gates commute (compendium 6.1): any ledger-only gate starts
            # the bare ledger chain, not just a leading ':status()'. This
            # one used to raise.
            '$*.files.:named_file_name("orders"):status("complete")',
        ],
    )
    def test_a_ledger_gate_chain_in_either_order(self, reference):
        assert TestStatusGate._status_finder(reference).query().uuids == ["ok-1"]


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

    def test_more_than_one_chained_function_is_a_general_chain(self):
        # changed 2026-11-02 (finding E, was: raises "functions attached
        # directly to name_one"). Two value fields are a general
        # ':manifest()' chain: the last one supplies the value, with a
        # warning (compendium 5.20b).
        finder = _finder(
            "$alpha.files.:manifest():time():uuid()", ALPHA_HOME, ALPHA_MANIFEST
        )
        logger = _FakeLogger()
        finder.csvpaths.logger = logger
        assert [r.data for r in finder.resolve().results] == [
            "u-zero-1",
            "u-one-1",
            "u-one-2",
        ]
        assert len(logger.warnings) == 1

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

    def test_query_gives_the_named_files_manifest_and_the_entry_uuid(self):
        # changed 2026-11-01 (was: the selected version's own file). The
        # reference names a manifest entry, so query() gives the
        # manifest.json it is read from, as the global ledger case
        # (Rule 1b) always has (compendium 5.7).
        results = _finder(
            "$alpha.files.:manifest():last()", ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert results.results[0].uuid == "u-one-2"
        assert results.results[0].path == "inputs/named_files/alpha/manifest.json"

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

    def test_range_combined_with_grouping_applies_within_each_group(self):
        # built 2026-10-21 -- see TestAllForOneNamedFile's own
        # test_all_combined_with_a_range_applies_within_each_group for
        # the full multi-group proof (this fixture's own 5 versions all
        # share one file_home, so it cannot distinguish pooled-vs-per-
        # group on its own -- it only confirms the combination no
        # longer raises and windows correctly).
        results = _finder(
            "$ranger.files.:all().:from(-1)", RANGE_HOME, RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v4"]

    def test_bare_time_window_function_is_gap_1s_flagship_files_example(
        self,
    ):
        # Gap 1 of compendium 6.27/TimeWindowFunction3, added 2026-10-17
        # -- a BARE time-component function riding in the chain, no
        # explicit :from()/:to(). The compendium's flagship example was
        # "$acme.files.:yesterday()" (6.27d/6.27e/6.27f), rewritten
        # 2026-11-07 as "$acme.files.:flatten().:yesterday()": in FILES
        # the window goes in name_three (see TestTimeWindowExamples).
        # Confirmed here with a real version pinned to "yesterday" via
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
        # ':all()' (or ':manifest()'/':flatten()'/etc.) occupies name_one's
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
            "$:regex(/^abba_.*/).files.:flatten()",
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
        ).query()
        assert results.files == [REGEX_ABBA_HOME]

    def test_regex_excludes_non_matching_named_files(self):
        results = _finder(
            "$:regex(/^abba_.*/).files.:flatten()",
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
        ).query()
        assert REGEX_ACME_HOME not in results.files

    def test_regex_with_no_matches_gives_empty(self):
        results = _finder(
            "$:regex(/^zzz_.*/).files.:flatten()",
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
        ).query()
        assert results.files == []

    def test_wrong_root_major_function_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$:having("x").files.:flatten()',
                REGEX_ACME_HOME,
                REGEX_ACME_MANIFEST,
                by_name=REGEX_BY_NAME,
            ).query()

    def test_regex_accepts_a_registered_variable(self):
        results = _finder(
            "$:regex(@aregex).files.:flatten()",
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
            variables={"aregex": "^abba_.*"},
        ).query()
        assert results.files == [REGEX_ABBA_HOME]


class TestChoiceRootMajor:
    # :choice() at root_major -- added 2026-10-20, closing one of the
    # 30 "does not yet support" sites catalogued that day
    # (reference_finder_3.py's own "Does not yet support :X() as a
    # name_one path segment," since the compendium lists :choice() as
    # a path-segment-occupying analog of :name()/:regex() -- but
    # :choice() was never a registered function at all until now).
    # Compendium "Functions in root_major": "a pipe-delimited sequence
    # of matching names" -- exact-match alternative to :regex()'s own
    # pattern match. Reuses the exact same '*'-traversal machinery
    # :regex() already does (same REGEX_* fixtures), just via
    # ChoiceSelector3's own .pattern property instead.
    def test_choice_selects_every_listed_name(self):
        results = _finder(
            '$:choice("acme_orders|abba_invoices").files.:flatten()',
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
        ).query()
        assert set(results.files) == {REGEX_ACME_HOME, REGEX_ABBA_HOME}

    def test_choice_excludes_names_not_listed(self):
        results = _finder(
            '$:choice("abba_invoices").files.:flatten()',
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
        ).query()
        assert results.files == [REGEX_ABBA_HOME]

    def test_choice_with_no_matching_name_gives_empty(self):
        results = _finder(
            '$:choice("zzz_nonexistent").files.:flatten()',
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
        ).query()
        assert results.files == []

    def test_choice_does_not_do_partial_or_pattern_matching(self):
        # exact match only -- "acme" alone must not match
        # "acme_orders" the way a :regex() substring search would.
        results = _finder(
            '$:choice("acme").files.:flatten()',
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
        ).query()
        assert results.files == []

    def test_choice_accepts_a_registered_variable(self):
        results = _finder(
            "$:choice(@names).files.:flatten()",
            REGEX_ACME_HOME,
            REGEX_ACME_MANIFEST,
            by_name=REGEX_BY_NAME,
            variables={"names": "abba_invoices"},
        ).query()
        assert results.files == [REGEX_ABBA_HOME]


class TestChoiceAsNameOnePathSegment:
    # :choice() as a bare/implied-'*' name_one path segment -- the
    # OTHER half of compendium 3.9c's own "fully occupies a path
    # segment" listing (:name()/:regex()/:choice()). Reuses the exact
    # same _compile_path_pattern()/_apply_implied_star() machinery
    # :regex() already does, via the shared Regex3 wrapper.
    def test_choice_matches_one_of_several_literal_files_in_a_group(self):
        results = _finder(
            '$alpha.files.:choice("one.csv|zero.csv").:last()',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        ).query()
        assert results.uuids == ["u-one-2"]

    def test_choice_excludes_a_file_not_listed(self):
        results = _finder(
            '$alpha.files.:choice("zero.csv"):last()',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        ).query()
        assert results.uuids == ["u-zero-1"]

    def test_choice_combined_with_the_worksheet_marker_is_legal(self):
        # same exemption :name()/:regex() already get -- a path-
        # BUILDING function (a literal name, pattern, or alternation)
        # is not a version-selector/grouping marker, so '#worksheet'
        # is allowed alongside it (an actual version still needs to
        # be selected too, via name_three, or this still raises for
        # an unrelated reason -- not exercised further here, just
        # confirming the '#worksheet'-requires-literal-path guard
        # itself does not reject :choice() outright the way it would
        # an unrelated function).
        with pytest.raises(ReferenceException3) as exc_info:
            _finder(
                '$alpha.files.:choice("one.csv")#sheet1',
                ALPHA_HOME,
                ALPHA_MANIFEST,
            ).query()
        # the raised error must be the "needs a pointer" one, not the
        # "#worksheet only means anything against a literal path" one
        # -- proving :choice() was correctly recognized as path-
        # building, same as :name()/:regex().
        assert "requires a version-selecting pointer" in str(exc_info.value)


def _entry_star_finder(reference: str) -> FilesReferenceFinder3:
    return _finder(
        reference,
        STAR_ALPHA_HOME,
        STAR_ALPHA_MANIFEST,
        by_name=STAR_BY_NAME,
        ledger=STAR_LEDGER,
        inputs_files_path="inputs/named_files",
    )


ALPHA_MANIFEST_JSON = "inputs/named_files/alpha/manifest.json"
BETA_MANIFEST_JSON = "inputs/named_files/beta/manifest.json"
LEDGER_MANIFEST_JSON = "inputs/named_files/manifest.json"


class TestManifestEntryQueryPaths:
    # added 2026-11-01. A reference with an explicit ':manifest()' names
    # a manifest entry, a record, so query() gives the manifest.json the
    # entry is read from, with the entry's uuid (compendium 5.7; agreed
    # with David 2026-11-01): the named-file's own manifest, or the
    # global ledger for a '*' ledger read. These used to give the
    # version's own data file. Forms without ':manifest()' name the
    # version and keep its file. resolve() is unchanged except under '*'
    # traversal, which now reads the live named-file's entry.

    @staticmethod
    def _alpha(reference: str):
        return _finder(reference, ALPHA_HOME, ALPHA_MANIFEST).query()

    @pytest.mark.parametrize(
        "reference,uuids",
        [
            ("$alpha.files.:last():manifest()", ["u-one-2"]),
            ("$alpha.files.:manifest():last()", ["u-one-2"]),
            ("$alpha.files.:index(0):manifest()", ["u-zero-1"]),
            ('$alpha.files.:name("one.csv").:first():manifest()', ["u-one-1"]),
            ('$alpha.files.:name("one.csv").:last():manifest()', ["u-one-2"]),
            ('$alpha.files.:name("one.csv").:manifest()', ["u-one-1", "u-one-2"]),
            ('$alpha.files.:name("one.csv"):manifest()', ["u-one-1", "u-one-2"]),
            ("$alpha.files.*.:last():manifest()", ["u-one-2"]),
            ("$alpha.files.:all().:last():manifest()", ["u-one-2", "u-zero-1"]),
            ("$alpha.files.:flatten().:last():manifest()", ["u-one-2"]),
            ("$alpha.files.:manifest():uuid()", ["u-zero-1", "u-one-1", "u-one-2"]),
            ('$alpha.files.:name("one.csv").:first():manifest():uuid()', ["u-one-1"]),
        ],
    )
    def test_literal_root_gives_the_named_files_manifest(self, reference, uuids):
        results = self._alpha(reference)
        assert results.uuids == uuids
        assert results.files == [ALPHA_MANIFEST_JSON] * len(uuids)

    def test_a_gate_beside_manifest_gives_the_named_files_manifest(self):
        results = _gate_finder('$alpha.files.:manifest():status("complete")').query()
        assert results.uuids == ["u-a1", "u-a2"]
        assert results.files == [ALPHA_MANIFEST_JSON] * 2

    def test_a_templated_named_file_gives_its_own_manifest(self):
        results = _finder(
            "$acme.files.:manifest():last()", TEMPLATED_HOME, TEMPLATED_MANIFEST
        ).query()
        assert results.files == ["inputs/named_files/acme/manifest.json"]
        assert results.uuids == ["u-q2-1"]

    @pytest.mark.parametrize(
        "reference",
        [
            '$alpha.files.:name("one.csv").:first()',
            '$alpha.files.:name("one.csv").:first():uuid()',
            "$alpha.files.:first()",
            "$alpha.files.*.:last()",
        ],
    )
    def test_without_manifest_the_version_keeps_its_file(self, reference):
        for result in self._alpha(reference).results:
            assert result.path.endswith(".csv")

    def test_bare_manifest_is_still_the_whole_file(self):
        results = self._alpha("$alpha.files.:manifest()")
        assert results.files == [ALPHA_MANIFEST_JSON]
        assert results.uuids == [None]

    def test_literal_resolve_still_gives_the_entry(self):
        results = _finder(
            '$alpha.files.:name("one.csv").:first():manifest()',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        ).resolve()
        assert results.results[0].data == ALPHA_MANIFEST[1]

    def test_literal_field_resolve_is_unchanged(self):
        results = _finder(
            "$alpha.files.:manifest():uuid()", ALPHA_HOME, ALPHA_MANIFEST
        ).resolve()
        assert [r.data for r in results.results] == ["u-zero-1", "u-one-1", "u-one-2"]

    @pytest.mark.parametrize(
        "reference,expected",
        [
            (
                "$*.files.*.:last():manifest()",
                [(ALPHA_MANIFEST_JSON, "u-one-2"), (BETA_MANIFEST_JSON, "u-two-2")],
            ),
            (
                "$*.files.:flatten().:last():manifest()",
                [(BETA_MANIFEST_JSON, "u-two-2")],
            ),
            ("$*.files.*.bbb:manifest()", [(ALPHA_MANIFEST_JSON, "u-one-1")]),
            (
                "$*.files.:all().:last():manifest()",
                [
                    (ALPHA_MANIFEST_JSON, "u-one-2"),
                    (ALPHA_MANIFEST_JSON, "u-zero-1"),
                    (BETA_MANIFEST_JSON, "u-two-2"),
                ],
            ),
            (
                "$*.files.:groups().:last():manifest()",
                [
                    (ALPHA_MANIFEST_JSON, "u-one-2"),
                    (ALPHA_MANIFEST_JSON, "u-zero-1"),
                    (BETA_MANIFEST_JSON, "u-two-2"),
                ],
            ),
        ],
    )
    def test_star_traversal_gives_each_entrys_own_named_file(self, reference, expected):
        results = _entry_star_finder(reference).query()
        assert [(r.path, r.uuid) for r in results.results] == expected

    def test_star_traversal_without_a_pointer_lists_every_entry(self):
        results = _entry_star_finder("$*.files.*.:manifest()").query()
        assert [(r.path, r.uuid) for r in results.results] == [
            (ALPHA_MANIFEST_JSON, "u-zero-1"),
            (ALPHA_MANIFEST_JSON, "u-one-1"),
            (ALPHA_MANIFEST_JSON, "u-one-2"),
            (BETA_MANIFEST_JSON, "u-two-1"),
            (BETA_MANIFEST_JSON, "u-two-2"),
        ]

    def test_star_traversal_without_manifest_keeps_the_version_file(self):
        results = _entry_star_finder("$*.files.*.:last()").query()
        assert results.files == [
            "inputs/named_files/alpha/one.csv/ccc.csv",
            "inputs/named_files/beta/two.csv/eee.csv",
        ]

    def test_star_traversal_resolve_reads_the_named_files_entry(self):
        # R1, fixed 2026-11-01: it read the ledger entry. STAR_LEDGER's
        # entries hold only uuid and fingerprint, so a "file" key shows
        # the named-file's own entry was read.
        results = _entry_star_finder("$*.files.*.bbb:manifest()").resolve()
        assert results.results[0].data == STAR_ALPHA_MANIFEST[1]

    def test_star_group_resolve_reads_each_named_files_entry(self):
        results = _entry_star_finder("$*.files.:all().:last():manifest()").resolve()
        assert [r.data["file"] for r in results.results] == [
            "inputs/named_files/alpha/one.csv/ccc.csv",
            "inputs/named_files/alpha/zero.csv/aaa.csv",
            "inputs/named_files/beta/two.csv/eee.csv",
        ]

    def test_rule_1b_gives_the_ledger_and_reads_the_live_entry(self):
        # the query names the ledger set (5.7); a live record resolves to
        # its named-file's own entry, as CSVPATHS does under C1 (6.13b(v),
        # decision D6, 2026-11-12). It resolved to the ledger record
        # {"uuid": "u-two-2", "fingerprint": "eee"} until then.
        finder = _entry_star_finder("$*.files.:last():manifest()")
        results = finder.query()
        assert [(r.path, r.uuid) for r in results.results] == [
            (LEDGER_MANIFEST_JSON, "u-two-2")
        ]
        data = _entry_star_finder("$*.files.:last():manifest()").resolve()
        assert data.results[0].data == STAR_BETA_MANIFEST[1]

    def test_a_star_ledger_field_read_gives_the_ledger(self):
        finder = _finder(
            "$*.files.:manifest():uuid()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=MANIFEST_FIELD_LEDGER,
        )
        results = finder.query()
        assert results.files == [LEDGER_MANIFEST_JSON] * 2
        assert results.uuids == ["u-ledger-1", "u-ledger-2"]

    def test_a_star_ledger_gate_gives_the_ledger(self):
        results = _gate_finder('$*.files.:manifest():status("complete")').query()
        assert results.files == [LEDGER_MANIFEST_JSON] * 3
        assert results.uuids == ["u-a1", "u-a2", "u-b1"]

    def test_a_bare_star_gate_keeps_the_version_files(self):
        # no ':manifest()': Group 3, unchanged here (the C1 bare-half
        # revert will move it off the ledger).
        results = _gate_finder('$*.files.:status("complete")').query()
        assert all(f.endswith((".csv", ".xlsx")) for f in results.files)


class TestNamedFileManifestPathHelpers:
    # the helpers behind TestManifestEntryQueryPaths.

    @staticmethod
    def _star():
        return _entry_star_finder("$*.files.*.:last():manifest()")

    def test_finds_the_named_file_holding_the_entry(self):
        entry = STAR_BY_NAME["beta"][1][0]
        path = self._star()._named_file_manifest_path(
            entry=entry, names=["alpha", "beta"]
        )
        assert path == BETA_MANIFEST_JSON

    def test_a_name_that_prefixes_another_is_not_confused(self):
        by_name = {
            "alpha": ("inputs/named_files/alpha", []),
            "alphabet": ("inputs/named_files/alphabet", []),
        }
        finder = _finder(
            "$*.files.*.:last():manifest()", ALPHA_HOME, [], by_name=by_name
        )
        entry = {"file_home": "inputs/named_files/alphabet/x.csv", "uuid": "u"}
        path = finder._named_file_manifest_path(
            entry=entry, names=["alpha", "alphabet"]
        )
        assert path == "inputs/named_files/alphabet/manifest.json"

    def test_an_entry_in_no_named_file_raises(self):
        entry = {"file_home": "elsewhere/x.csv", "uuid": "u"}
        with pytest.raises(ReferenceException3):
            self._star()._named_file_manifest_path(entry=entry, names=["alpha"])

    def test_bad_arguments_raise(self):
        finder = self._star()
        with pytest.raises(TypeError):
            finder._named_file_manifest_path(entry=None, names=["alpha"])
        with pytest.raises(ValueError):
            finder._named_file_manifest_path(entry={"file_home": "x"}, names=[])
        with pytest.raises(ValueError, match="has no file_home"):
            finder._named_file_manifest_path(entry={"uuid": "u"}, names=["alpha"])

    def test_root_manifest_path(self):
        finder = _finder("$alpha.files.:manifest()", ALPHA_HOME, ALPHA_MANIFEST)
        assert finder._root_manifest_path("alpha") == ALPHA_MANIFEST_JSON
        with pytest.raises(ValueError):
            finder._root_manifest_path("")
        with pytest.raises(ValueError):
            finder._root_manifest_path(None)

    def test_files_ledger_path(self):
        assert self._star()._files_ledger_path() == LEDGER_MANIFEST_JSON

    def test_live_manifest_entry_by_uuid(self):
        finder = self._star()
        assert finder._live_manifest_entry_by_uuid("u-two-1") == STAR_BETA_MANIFEST[0]
        assert finder._live_manifest_entry_by_uuid("nope") is None
        with pytest.raises(ValueError):
            finder._live_manifest_entry_by_uuid("")


class TestLiveLedgerEntries:
    # the helper behind the bare ':status()' gate since the C1 bare-half
    # revert (2026-11-01): the ledger entries of live versions only.
    @staticmethod
    def _finder():
        return TestStatusGate._status_finder('$*.files.:status("complete")')

    def test_keeps_only_live_versions_in_ledger_order(self):
        entries = self._finder()._live_ledger_entries(names=["orders", "invoices"])
        assert [e["uuid"] for e in entries] == ["ok-1"]

    def test_scoped_to_the_names_given(self):
        assert self._finder()._live_ledger_entries(names=["invoices"]) == []

    def test_no_names_gives_no_entries(self):
        assert self._finder()._live_ledger_entries(names=[]) == []

    def test_none_raises(self):
        with pytest.raises(ValueError):
            self._finder()._live_ledger_entries(names=None)

    def test_a_live_version_with_no_ledger_entry_is_absent(self):
        # a manifest from before the ledger: the bare gate has nothing to
        # read its status from, as before
        by_name = {
            "orders": (
                "inputs/named_files/orders",
                [{"file_home": "inputs/named_files/orders/x", "uuid": "pre-ledger"}],
            )
        }
        finder = _finder(
            '$*.files.:status("complete")',
            TYPE_HOME,
            [],
            ledger=STATUS_LEDGER,
            by_name=by_name,
        )
        assert finder._live_ledger_entries(names=["orders"]) == []
        assert finder.query().results == []


class TestLedgerSetListsFailures:
    # since 2026-11-01 the '*' ledger set lists failed registrations (a
    # failure is tracked only in the ledger; each result's path is the
    # ledger). A failure may carry no named_file_name at all.
    LEDGER = MANIFEST_FIELD_LEDGER + [
        {"uuid": "nameless-failure", "status": "failed", "file_path": None}
    ]

    def _query(self, reference: str):
        return _finder(
            reference,
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=self.LEDGER,
        ).query()

    def test_a_nameless_failure_is_listed_under_star(self):
        results = self._query("$*.files.:manifest():uuid()")
        assert results.uuids == ["u-ledger-1", "u-ledger-2", "nameless-failure"]
        assert results.files == ["inputs/named_files/manifest.json"] * 3

    def test_a_name_filter_passes_over_a_nameless_failure(self):
        results = self._query("$:regex(/^al/).files.:manifest():uuid()")
        assert results.uuids == ["u-ledger-1"]


class TestStarRootGroupsByNamedFile:
    # a '$*' root groups by named-file (compendium 4.1b; David,
    # 2026-11-06): a pointer or an index range picks within each named-
    # file, as '$*.csvpaths.:last()' and '$*.results.:last()' do.
    # ':flatten()' pools (so does the ledger ':manifest()', tested with
    # the ledger fixtures). The star fixture:
    # alpha zero-1, one-1, one-2; beta two-1, two-2, in time order.
    @pytest.mark.parametrize(
        "reference, expected",
        [
            ("$*.files.*.:last()", ["u-one-2", "u-two-2"]),
            ("$*.files.*.:index(-2)", ["u-one-1", "u-two-1"]),
            ("$*.files.*.:from(1):to(1)", ["u-one-1", "u-two-2"]),
            # a lone pointer in name_one, each named-file's own pick
            ("$*.files.:last()", ["u-one-2", "u-two-2"]),
            ("$*.files.:first()", ["u-zero-1", "u-two-1"]),
            # a gate filters within each group, then the pointer picks
            ('$*.files.*.:last():fingerprint("bbb")', ["u-one-1"]),
            ('$*.files.*.:fingerprint("ddd"):last()', ["u-two-1"]),
            # a regex root groups the same way
            ("$:regex(/a/).files.*.:last()", ["u-one-2", "u-two-2"]),
            ("$:regex(/^b/).files.*.:last()", ["u-two-2"]),
        ],
    )
    def test_one_result_per_named_file(self, reference, expected):
        assert _star_finder(reference).query().uuids == expected

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # a date range matches each version's own time, so it keeps
            # the pooled time order
            (
                '$*.files.*.:from(:date("2026-01-03"))',
                ["u-one-2", "u-two-1", "u-two-2"],
            ),
            ("$*.files.:flatten().:last()", ["u-two-2"]),
            ("$*.files.:flatten().:from(-2)", ["u-two-1", "u-two-2"]),
        ],
    )
    def test_the_pooled_forms(self, reference, expected):
        assert _star_finder(reference).query().uuids == expected

    @pytest.mark.parametrize(
        "pointer", [":last()", ":first()", ":index(1)", ":from(0):to(1)"]
    )
    def test_each_group_is_its_literal_roots_answer(self, pointer):
        grouped = _star_finder(f"$*.files.*.{pointer}").query().uuids
        literal = []
        for name in ("alpha", "beta"):
            literal.extend(_star_finder(f"${name}.files.*.{pointer}").query().uuids)
        assert grouped == literal

    def test_a_lone_pointer_resolves_each_named_files_entry(self):
        # as '$alpha.files.:last()' does, the implied ':manifest()' (5.21)
        results = _star_finder("$*.files.:last()").resolve()
        assert [r.data for r in results.results] == [
            STAR_ALPHA_MANIFEST[2],
            STAR_BETA_MANIFEST[1],
        ]

    def test_a_lone_pointer_queries_to_the_version_files(self):
        results = _star_finder("$*.files.:last()").query()
        assert results.files == [
            "inputs/named_files/alpha/one.csv/ccc.csv",
            "inputs/named_files/beta/two.csv/eee.csv",
        ]

    def test_a_field_reads_each_groups_pick(self):
        results = _star_finder("$*.files.*.:last():fingerprint()").resolve()
        assert [r.data for r in results.results] == ["ccc", "eee"]

    def test_a_date_range_keeps_the_pooled_time_order(self):
        # alpha's and beta's versions interleave in time, so grouping
        # would reorder them; a pointer still groups
        def _entry(name, file, uuid, day):
            home = f"inputs/named_files/{name}/{file}"
            return {
                "file": f"{home}/{uuid}.csv",
                "file_home": home,
                "uuid": uuid,
                "time": f"2026-01-0{day}T00:00:00+00:00",
            }

        by_name = {
            "alpha": (
                "inputs/named_files/alpha",
                [_entry("alpha", "a.csv", "a1", 1), _entry("alpha", "a.csv", "a2", 3)],
            ),
            "beta": ("inputs/named_files/beta", [_entry("beta", "b.csv", "b1", 2)]),
        }

        def _uuids(reference):
            finder = _finder(
                reference,
                "inputs/named_files/alpha",
                by_name["alpha"][1],
                by_name=by_name,
                ledger=[],
            )
            return finder.query().uuids

        assert _uuids('$*.files.*.:from(:date("2026-01-01"))') == ["a1", "b1", "a2"]
        assert _uuids('$*.files.*.:from(:date("2026-01-01")):last()') == ["a2", "b1"]
