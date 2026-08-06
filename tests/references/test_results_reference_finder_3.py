import json
import os

import pytest

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.results_reference_finder_3 import ResultsReferenceFinder3

#
# unlike files/csvpaths (which read a fake in-memory manifest list), results
# discovery reads a fake archive-root manifest.json (one entry per csvpath-
# statement execution, across every named-paths group -- confirmed against a
# real entry David pasted, and against v1/v2's own working equivalent,
# results_tools/resolve_possibles.py). Each entry's "run_home" is the exact,
# already-resolved path a run landed at -- this is how the finder discovers
# real run directories without ever needing to know/guess a group's
# template depth. Per-run/per-instance manifest.json files (for "run_uuid"/
# "uuid") still need real directories on disk, same as before.
#


class _FakeConfig:
    def __init__(self, archive: str):
        self._archive = archive

    def get(self, *, section, name):
        assert (section, name) == ("results", "archive")
        return self._archive


class _FakeResultsManager:
    def __init__(self, archive: str):
        self._archive = archive

    def get_named_results_home(self, name):
        return os.path.join(self._archive, name)


class _FakeCsvPaths:
    def __init__(self, archive: str):
        self.results_manager = _FakeResultsManager(archive)
        self.config = _FakeConfig(archive)


def _write_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _make_run(base, run_name: str, run_uuid: str, instances: dict) -> str:
    """instances: {identity: instance_uuid}. Returns the run's own full
    path (for use as a "run_home" entry in the fake archive manifest)."""
    run_dir = base / run_name
    _write_json(run_dir / "manifest.json", {"run_uuid": run_uuid})
    for identity, inst_uuid in instances.items():
        _write_json(run_dir / identity / "manifest.json", {"uuid": inst_uuid})
    return str(run_dir)


def _write_archive_manifest(archive, group: str, run_homes: list[str]) -> None:
    entries = [{"named_paths_name": group, "run_home": rh} for rh in run_homes]
    _write_json(archive / "manifest.json", entries)


def _finder(reference: str, archive: str) -> ResultsReferenceFinder3:
    csvpaths = _FakeCsvPaths(archive)
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return ResultsReferenceFinder3(csvpaths=csvpaths, ref=ref)


@pytest.fixture
def acme_archive(tmp_path):
    base = tmp_path / "acme" / "customers" / "2025"
    run1 = _make_run(
        base,
        "2026-01-01_00-00-00",
        "run1-uuid",
        {"company_names": "inst1-uuid", "1": "inst2-uuid"},
    )
    run2 = _make_run(base, "2026-01-02_00-00-00", "run2-uuid", {"0": "inst3-uuid"})
    _write_archive_manifest(tmp_path, "acme", [run1, run2])
    return str(tmp_path)


class TestVersionPointer:
    def test_last(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:last()", acme_archive
        ).query()
        assert results.uuids == ["run2-uuid"]

    def test_first(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:first()", acme_archive
        ).query()
        assert results.uuids == ["run1-uuid"]

    def test_index(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:index(1)", acme_archive
        ).query()
        assert results.uuids == ["run2-uuid"]

    def test_index_out_of_range_returns_empty_not_an_error(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:index(99)", acme_archive
        ).query()
        assert results.files == []

    def test_result_path_is_the_run_directory(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:first()", acme_archive
        ).query()
        assert results.files == [
            f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
        ]


class TestNoPointerReturnsEveryRun:
    def test_no_pointer_returns_every_run_unreduced(self, acme_archive):
        results = _finder("$acme.results.customers/2025", acme_archive).query()
        assert results.uuids == ["run1-uuid", "run2-uuid"]

    def test_no_pointer_no_matching_prefix_returns_empty(self, acme_archive):
        results = _finder("$acme.results.orders/2025", acme_archive).query()
        assert results.files == []


class TestPathMatching:
    def test_star_segment_matches_any_prefix(self, acme_archive):
        results = _finder("$acme.results.*/2025:last()", acme_archive).query()
        assert results.uuids == ["run2-uuid"]

    def test_name_function_as_path_segment(self, acme_archive):
        results = _finder(
            '$acme.results.:name("customers")/2025:last()', acme_archive
        ).query()
        assert results.uuids == ["run2-uuid"]

    def test_under_specified_path_now_correctly_matches_nothing(self, acme_archive):
        # "customers" alone is one segment short of the real template
        # depth ("customers/2025") -- with manifest-driven discovery this
        # correctly matches nothing (the discovered run_homes' own
        # prefixes are 2 segments long, not 1), rather than the old
        # directory-walking design's silent misfire (treating "2025" as
        # if it were itself a run).
        results = _finder("$acme.results.customers:last()", acme_archive).query()
        assert results.files == []


class TestBareFunctionOnlyNameOne:
    # mirrors csvpaths: no literal path at all -- the sole path
    # "segment" is itself a version-selecting function. Every run
    # discovered for the group is a candidate, regardless of how deep
    # its own prefix happens to be (unlike the literal-path shape, which
    # requires an exact segment-count match).
    @pytest.fixture
    def flat_archive(self, tmp_path):
        base = tmp_path / "flat"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1-uuid", {})
        run2 = _make_run(base, "2026-01-02_00-00-00", "run2-uuid", {})
        _write_archive_manifest(tmp_path, "flat", [run1, run2])
        return str(tmp_path)

    def test_bare_last(self, flat_archive):
        results = _finder("$flat.results.:last()", flat_archive).query()
        assert results.uuids == ["run2-uuid"]

    def test_bare_first(self, flat_archive):
        results = _finder("$flat.results.:first()", flat_archive).query()
        assert results.uuids == ["run1-uuid"]

    def test_bare_all_returns_every_run(self, flat_archive):
        results = _finder("$flat.results.:all()", flat_archive).query()
        assert set(results.uuids) == {"run1-uuid", "run2-uuid"}

    def test_bare_pointer_still_finds_a_run_under_a_deep_template(
        self, acme_archive
    ):
        # bare :last() ignores prefix depth entirely -- it still finds
        # the group's runs even though they sit under "customers/2025".
        results = _finder("$acme.results.:last()", acme_archive).query()
        assert results.uuids == ["run2-uuid"]


class TestDiscoveryFromArchiveManifest:
    def test_dedupes_multiple_entries_sharing_one_run_home(self, tmp_path):
        # a real run_home is written once per csvpath-statement
        # execution -- several entries in the archive manifest can share
        # the same run_home for one run with multiple statements.
        base = tmp_path / "acme"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1-uuid", {})
        _write_archive_manifest(tmp_path, "acme", [run1, run1, run1])
        results = _finder("$acme.results.:all()", str(tmp_path)).query()
        assert results.uuids == ["run1-uuid"]

    def test_stale_entry_for_a_deleted_run_is_dropped(self, tmp_path):
        base = tmp_path / "acme"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1-uuid", {})
        deleted_run_home = str(base / "2025-06-06_00-00-00")
        _write_archive_manifest(tmp_path, "acme", [run1, deleted_run_home])
        results = _finder("$acme.results.:all()", str(tmp_path)).query()
        assert results.uuids == ["run1-uuid"]

    def test_other_groups_entries_are_ignored(self, tmp_path):
        acme_base = tmp_path / "acme"
        other_base = tmp_path / "other"
        acme_run = _make_run(acme_base, "2026-01-01_00-00-00", "acme-run-uuid", {})
        other_run = _make_run(
            other_base, "2026-01-01_00-00-00", "other-run-uuid", {}
        )
        _write_json(
            tmp_path / "manifest.json",
            [
                {"named_paths_name": "acme", "run_home": acme_run},
                {"named_paths_name": "other", "run_home": other_run},
            ],
        )
        results = _finder("$acme.results.:all()", str(tmp_path)).query()
        assert results.uuids == ["acme-run-uuid"]

    def test_no_archive_manifest_yet_returns_empty_not_an_error(self, tmp_path):
        (tmp_path / "acme").mkdir()
        results = _finder("$acme.results.:all()", str(tmp_path)).query()
        assert results.files == []


class TestIdentityLookupOnNameThree:
    def test_matches_named_identity(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:first().company_names", acme_archive
        ).query()
        assert results.uuids == ["inst1-uuid"]

    def test_matches_stringified_index_identity(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:first().1", acme_archive
        ).query()
        assert results.uuids == ["inst2-uuid"]

    def test_no_matching_identity_returns_empty(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:first().nope", acme_archive
        ).query()
        assert results.files == []

    def test_result_path_is_the_instance_directory(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:first().company_names", acme_archive
        ).query()
        assert results.files == [
            f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00/company_names"
        ]


class TestAllFunctionOnNameThree:
    def test_all_returns_every_instance_in_the_run(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:first().:all()", acme_archive
        ).query()
        assert set(results.uuids) == {"inst1-uuid", "inst2-uuid"}

    def test_all_with_no_run_pointer_covers_every_matched_run(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025.:all()", acme_archive
        ).query()
        assert set(results.uuids) == {"inst1-uuid", "inst2-uuid", "inst3-uuid"}


class TestResolve:
    def test_resolving_a_run_gives_none(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:first()", acme_archive
        ).resolve()
        assert results.results[0].data is None

    def test_resolving_a_named_identity_gives_none(self, acme_archive):
        # an identity alone, with no well-known-file accessor riding
        # alongside it, has no single unambiguous payload -- "no
        # default" (see TestWellKnownFileAccessors for the accessor
        # case, which does resolve to something).
        results = _finder(
            "$acme.results.customers/2025:first().company_names", acme_archive
        ).resolve()
        assert results.results[0].data is None


class TestWellKnownFileAccessors:
    # :errors()/:vars()/:meta() resolve to parsed JSON; :data()/
    # :unmatched() resolve to raw bytes and tolerate absence (None);
    # :file("...") resolves an arbitrary user-named file the same way,
    # with a bare-filename-only guard against path traversal. All ride
    # alongside the identity/:all() selector already in name_three --
    # they do not select the instance themselves.
    @pytest.fixture
    def instance_dir(self, acme_archive):
        path = (
            f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
            "/company_names"
        )
        os.makedirs(path, exist_ok=True)
        return path

    def test_errors_resolves_parsed_json(self, acme_archive, instance_dir):
        errors = [{"error": "bad row", "line": 3}]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            "$acme.results.customers/2025:first().company_names:errors()",
            acme_archive,
        ).resolve()
        assert results.results[0].data == errors

    def test_vars_resolves_parsed_json(self, acme_archive, instance_dir):
        variables = {"count": 5, "label": "totals"}
        with open(os.path.join(instance_dir, "vars.json"), "w") as f:
            json.dump(variables, f)
        results = _finder(
            "$acme.results.customers/2025:first().company_names:vars()",
            acme_archive,
        ).resolve()
        assert results.results[0].data == variables

    def test_meta_resolves_parsed_json(self, acme_archive, instance_dir):
        meta = {"identity": "company_names", "run_index": 0}
        with open(os.path.join(instance_dir, "meta.json"), "w") as f:
            json.dump(meta, f)
        results = _finder(
            "$acme.results.customers/2025:first().company_names:meta()",
            acme_archive,
        ).resolve()
        assert results.results[0].data == meta

    def test_data_resolves_raw_bytes(self, acme_archive, instance_dir):
        content = b"a,b\n1,2\n"
        with open(os.path.join(instance_dir, "data.csv"), "wb") as f:
            f.write(content)
        results = _finder(
            "$acme.results.customers/2025:first().company_names:data()",
            acme_archive,
        ).resolve()
        assert results.results[0].data == content

    def test_data_resolves_none_when_never_written(
        self, acme_archive, instance_dir
    ):
        # data.csv is only written if at least one line matched --
        # genuinely optional, same as definition.json.
        results = _finder(
            "$acme.results.customers/2025:first().company_names:data()",
            acme_archive,
        ).resolve()
        assert results.results[0].data is None

    def test_unmatched_resolves_raw_bytes(self, acme_archive, instance_dir):
        content = b"x,y\n9,9\n"
        with open(os.path.join(instance_dir, "unmatched.csv"), "wb") as f:
            f.write(content)
        results = _finder(
            "$acme.results.customers/2025:first().company_names:unmatched()",
            acme_archive,
        ).resolve()
        assert results.results[0].data == content

    def test_file_resolves_a_user_named_output(self, acme_archive, instance_dir):
        content = b"custom output"
        with open(os.path.join(instance_dir, "orders.parquet"), "wb") as f:
            f.write(content)
        results = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':file("orders.parquet")',
            acme_archive,
        ).resolve()
        assert results.results[0].data == content

    def test_file_rejects_a_path_valued_argument(self, acme_archive, instance_dir):
        finder = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':file("../escape.txt")',
            acme_archive,
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_accessor_combined_with_all_reads_each_instance_own_file(
        self, acme_archive
    ):
        # run1 has two instances: company_names and "1".
        base = f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
        os.makedirs(f"{base}/company_names", exist_ok=True)
        os.makedirs(f"{base}/1", exist_ok=True)
        with open(f"{base}/company_names/meta.json", "w") as f:
            json.dump({"which": "company_names"}, f)
        with open(f"{base}/1/meta.json", "w") as f:
            json.dump({"which": "1"}, f)
        results = _finder(
            "$acme.results.customers/2025:first().:all():meta()", acme_archive
        ).resolve()
        by_which = {r.data["which"] for r in results.results}
        assert by_which == {"company_names", "1"}


class TestScopeLimits:
    def test_star_root_major_not_yet_supported(self, acme_archive):
        finder = _finder("$*.results.customers/2025:last()", acme_archive)
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_name_two_worksheet_marker_not_supported(self, acme_archive):
        finder = _finder(
            "$acme.results.customers/2025#sheet1:last()", acme_archive
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_two_pointers_in_name_one_raises(self, acme_archive):
        finder = _finder(
            "$acme.results.customers/2025:first():last()", acme_archive
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_star_body_on_name_three_not_supported(self, acme_archive):
        finder = _finder("$acme.results.customers/2025:first().*", acme_archive)
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_truly_unregistered_function_on_name_three_raises(self, acme_archive):
        finder = _finder(
            "$acme.results.customers/2025:first().:quarter()", acme_archive
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_accessor_alone_with_no_identity_or_all_raises(self, acme_archive):
        # :data() is registered and meaningful for results, but it does
        # not itself select which instance it applies to -- it needs a
        # literal identity or :all() riding alongside it.
        finder = _finder(
            "$acme.results.customers/2025:first().:data()", acme_archive
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_identity_combined_with_all_raises(self, acme_archive):
        # contradictory: a literal identity selects one instance, :all()
        # selects every instance.
        finder = _finder(
            "$acme.results.customers/2025:first().company_names:all()",
            acme_archive,
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_manifest_function_on_name_three_not_yet_supported(self, acme_archive):
        # :manifest() is registered, but not meaningful as a name_three
        # function for results in this pass -- only :all() and the
        # well-known-file accessors are accepted there.
        finder = _finder(
            "$acme.results.customers/2025:first().company_names:manifest()",
            acme_archive,
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_unsupported_function_valued_path_segment(self, acme_archive):
        finder = _finder("$acme.results.:quarter()/2025:last()", acme_archive)
        with pytest.raises(ReferenceException3):
            finder.query()
