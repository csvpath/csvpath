import json

import pytest

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.results_reference_finder_3 import ResultsReferenceFinder3

#
# unlike files/csvpaths (which read a fake in-memory manifest list), results
# has no per-named-results-group manifest array to fake -- query() walks
# real directories (confirmed by direct experiment: there is no equivalent
# to files'/csvpaths' manifest.json array at the group level). So these
# fixtures build real directory trees under tmp_path, mirroring the
# confirmed real layout: archive/<name>/<template path>/<run dir>/<instance
# dir>, run/instance directories each with their own small manifest.json
# ("run_uuid"/"uuid" respectively).
#


class _FakeResultsManager:
    def __init__(self, home: str):
        self._home = home

    def get_named_results_home(self, name):
        return self._home


class _FakeCsvPaths:
    def __init__(self, results_manager):
        self.results_manager = results_manager


def _write_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _make_run(base, run_name: str, run_uuid: str, instances: dict) -> None:
    """instances: {identity: instance_uuid}"""
    run_dir = base / run_name
    _write_json(run_dir / "manifest.json", {"run_uuid": run_uuid})
    for identity, inst_uuid in instances.items():
        _write_json(run_dir / identity / "manifest.json", {"uuid": inst_uuid})


def _finder(reference: str, home: str) -> ResultsReferenceFinder3:
    csvpaths = _FakeCsvPaths(_FakeResultsManager(home))
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return ResultsReferenceFinder3(csvpaths=csvpaths, ref=ref)


@pytest.fixture
def acme_home(tmp_path):
    base = tmp_path / "acme" / "customers" / "2025"
    _make_run(
        base,
        "2026-01-01_00-00-00",
        "run1-uuid",
        {"company_names": "inst1-uuid", "1": "inst2-uuid"},
    )
    _make_run(
        base,
        "2026-01-02_00-00-00",
        "run2-uuid",
        {"0": "inst3-uuid"},
    )
    return str(tmp_path / "acme")


class TestVersionPointer:
    def test_last(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025:last()", acme_home
        ).query()
        assert results.uuids == ["run2-uuid"]

    def test_first(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025:first()", acme_home
        ).query()
        assert results.uuids == ["run1-uuid"]

    def test_index(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025:index(1)", acme_home
        ).query()
        assert results.uuids == ["run2-uuid"]

    def test_index_out_of_range_returns_empty_not_an_error(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025:index(99)", acme_home
        ).query()
        assert results.files == []

    def test_result_path_is_the_run_directory(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025:first()", acme_home
        ).query()
        assert results.files == [
            f"{acme_home}/customers/2025/2026-01-01_00-00-00"
        ]


class TestNoPointerReturnsEveryRun:
    def test_no_pointer_returns_every_run_unreduced(self, acme_home):
        results = _finder("$acme.results.customers/2025", acme_home).query()
        assert results.uuids == ["run1-uuid", "run2-uuid"]

    def test_no_pointer_no_matching_prefix_returns_empty(self, acme_home):
        results = _finder("$acme.results.orders/2025", acme_home).query()
        assert results.files == []


class TestPathMatching:
    def test_star_segment_matches_any_prefix(self, acme_home):
        results = _finder("$acme.results.*/2025:last()", acme_home).query()
        assert results.uuids == ["run2-uuid"]

    def test_name_function_as_path_segment(self, acme_home):
        results = _finder(
            '$acme.results.:name("customers")/2025:last()', acme_home
        ).query()
        assert results.uuids == ["run2-uuid"]

    def test_under_specified_path_is_a_known_limitation_not_validated(
        self, acme_home
    ):
        # "customers" alone does not reach the real run-directory level
        # (that is one level short of "customers/2025") -- this finder
        # has no way to know the group's own template depth, so it
        # treats whatever it finds ("2025", a directory) as if it were a
        # run. Documented as a known limitation, not a silent-failure
        # regression: this locks in the actual (if unhelpful) behavior.
        results = _finder("$acme.results.customers:last()", acme_home).query()
        assert results.files == [f"{acme_home}/customers/2025"]
        assert results.results[0].uuid is None


class TestBareFunctionOnlyNameOne:
    # mirrors csvpaths: no literal path at all -- the sole path
    # "segment" is itself a version-selecting function. Used when the
    # caller does not care about path narrowing (or there is no
    # template) -- the named-results home directory itself is the
    # "prefix". Exercised against a flat, no-template layout (unlike
    # acme_home's own templated "customers/2025" structure).
    @pytest.fixture
    def flat_home(self, tmp_path):
        base = tmp_path / "flat"
        _make_run(base, "2026-01-01_00-00-00", "run1-uuid", {})
        _make_run(base, "2026-01-02_00-00-00", "run2-uuid", {})
        return str(base)

    def test_bare_last(self, flat_home):
        results = _finder("$flat.results.:last()", flat_home).query()
        assert results.uuids == ["run2-uuid"]

    def test_bare_first(self, flat_home):
        results = _finder("$flat.results.:first()", flat_home).query()
        assert results.uuids == ["run1-uuid"]

    def test_bare_all_returns_every_run(self, flat_home):
        results = _finder("$flat.results.:all()", flat_home).query()
        assert set(results.uuids) == {"run1-uuid", "run2-uuid"}


class TestIdentityLookupOnNameThree:
    def test_matches_named_identity(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025:first().company_names", acme_home
        ).query()
        assert results.uuids == ["inst1-uuid"]

    def test_matches_stringified_index_identity(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025:first().1", acme_home
        ).query()
        assert results.uuids == ["inst2-uuid"]

    def test_no_matching_identity_returns_empty(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025:first().nope", acme_home
        ).query()
        assert results.files == []

    def test_result_path_is_the_instance_directory(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025:first().company_names", acme_home
        ).query()
        assert results.files == [
            f"{acme_home}/customers/2025/2026-01-01_00-00-00/company_names"
        ]


class TestAllFunctionOnNameThree:
    def test_all_returns_every_instance_in_the_run(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025:first().:all()", acme_home
        ).query()
        assert set(results.uuids) == {"inst1-uuid", "inst2-uuid"}

    def test_all_with_no_run_pointer_covers_every_matched_run(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025.:all()", acme_home
        ).query()
        assert set(results.uuids) == {"inst1-uuid", "inst2-uuid", "inst3-uuid"}


class TestResolve:
    def test_resolving_a_run_gives_none(self, acme_home):
        results = _finder(
            "$acme.results.customers/2025:first()", acme_home
        ).resolve()
        assert results.results[0].data is None

    def test_resolving_a_named_identity_gives_none(self, acme_home):
        # no well-known instance-level file function is registered yet
        # (:data()/:vars()/:meta()/:unmatched()/:errors()) -- "no
        # default" applies uniformly until one exists.
        results = _finder(
            "$acme.results.customers/2025:first().company_names", acme_home
        ).resolve()
        assert results.results[0].data is None


class TestScopeLimits:
    def test_star_root_major_not_yet_supported(self, acme_home):
        finder = _finder("$*.results.customers/2025:last()", acme_home)
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_name_two_worksheet_marker_not_supported(self, acme_home):
        finder = _finder(
            "$acme.results.customers/2025#sheet1:last()", acme_home
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_two_pointers_in_name_one_raises(self, acme_home):
        finder = _finder(
            "$acme.results.customers/2025:first():last()", acme_home
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_star_body_on_name_three_not_supported(self, acme_home):
        finder = _finder("$acme.results.customers/2025:first().*", acme_home)
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_unregistered_function_on_name_three_not_yet_supported(
        self, acme_home
    ):
        finder = _finder(
            "$acme.results.customers/2025:first().:data()", acme_home
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_manifest_function_on_name_three_not_yet_supported(self, acme_home):
        # :manifest() is registered, but not meaningful as a name_three
        # function for results in this pass -- only :all() is accepted.
        finder = _finder(
            "$acme.results.customers/2025:first().:manifest()", acme_home
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_unsupported_function_valued_path_segment(self, acme_home):
        finder = _finder(
            "$acme.results.:quarter()/2025:last()", acme_home
        )
        with pytest.raises(ReferenceException3):
            finder.query()
