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


class _FakeFileManager:
    def __init__(self, home, manifest):
        self._home = home
        self._manifest = manifest

    def named_file_home(self, name):
        return self._home

    def get_manifest(self, name):
        return self._manifest


class _FakeCsvPaths:
    def __init__(self, file_manager):
        self.file_manager = file_manager


def _finder(reference: str, home: str, manifest: list) -> FilesReferenceFinder3:
    csvpaths = _FakeCsvPaths(_FakeFileManager(home, manifest))
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
    def test_star_root_major_not_yet_supported(self):
        finder = _finder("$*.files.*.:last()", ALPHA_HOME, ALPHA_MANIFEST)
        with pytest.raises(ReferenceException3):
            finder.query()

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


class TestManifestCombinedWithNameThree:
    # :manifest() never narrows/selects anything itself -- combined with
    # real name_one path narrowing plus name_three, it either rides
    # alongside a real version pointer (giving that one matched entry)
    # or appears alone with no pointer at all (giving every matching
    # entry, unreduced). Neither shape routes through
    # _is_bare_pointer_reference -- that is only for the sole-content
    # "$acme.files.:manifest()" case.
    def test_manifest_alone_in_name_three_gives_every_matching_entry(self):
        # "one.csv" has two versions in ALPHA_MANIFEST -- no pointer, so
        # both come back, each resolving to its own manifest entry dict.
        finder = _finder(
            '$alpha.files.:name("one.csv").:manifest()', ALPHA_HOME, ALPHA_MANIFEST
        )
        results = finder.resolve()
        assert results.uuids == ["u-one-1", "u-one-2"]
        assert results.data_for_uuid("u-one-1") == ALPHA_MANIFEST[1]
        assert results.data_for_uuid("u-one-2") == ALPHA_MANIFEST[2]

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
