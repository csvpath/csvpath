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


class _FakePathsManager:
    def __init__(self, manifest):
        self._manifest = manifest

    def get_manifest_for_name(self, name):
        return self._manifest


class _FakeCsvPaths:
    def __init__(self, paths_manager):
        self.paths_manager = paths_manager


def _finder(reference: str, manifest: list = ACME_MANIFEST) -> CsvpathsReferenceFinder3:
    csvpaths = _FakeCsvPaths(_FakePathsManager(manifest))
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
