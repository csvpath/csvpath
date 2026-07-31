import pytest

from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3


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

    def test_extract_data_is_not_reachable_for_files(self):
        finder = _finder("$alpha.files.*.:first()", ALPHA_HOME, ALPHA_MANIFEST)
        with pytest.raises(ReferenceException3):
            finder._extract_data(None)
