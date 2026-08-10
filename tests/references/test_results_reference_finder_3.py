import json
import os
from pathlib import Path

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

    @property
    def results_root_manifest(self):
        with open(os.path.join(self._archive, "manifest.json")) as f:
            return json.load(f)


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


def _write_archive_manifest_multi(archive, groups: dict) -> None:
    """like _write_archive_manifest, but merges more than one group's
    entries into a single archive manifest.json write -- needed for '*'
    traversal tests, since _write_archive_manifest overwrites rather
    than appends. groups: {group_name: [run_home, ...]}."""
    entries = []
    for group, run_homes in groups.items():
        entries.extend({"named_paths_name": group, "run_home": rh} for rh in run_homes)
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


@pytest.fixture
def two_group_archive(tmp_path):
    # acme (2 runs) + widgets (1 run, chronologically LATEST overall).
    # widgets is written FIRST in the merged manifest on purpose -- a
    # naive (unsorted) "last" would give acme's own last run
    # (2026-01-02) instead of the true global-latest (widgets',
    # 2026-01-03), so this fails if the '*' traversal sort-by-trailing-
    # segment logic is ever removed/broken.
    acme_base = tmp_path / "acme" / "customers" / "2025"
    acme_run1 = _make_run(acme_base, "2026-01-01_00-00-00", "acme-run1-uuid", {})
    acme_run2 = _make_run(acme_base, "2026-01-02_00-00-00", "acme-run2-uuid", {})
    widgets_base = tmp_path / "widgets"
    widgets_run1 = _make_run(
        widgets_base, "2026-01-03_00-00-00", "widgets-run1-uuid", {}
    )
    _write_archive_manifest_multi(
        tmp_path,
        {
            "widgets": [widgets_run1],
            "acme": [acme_run1, acme_run2],
        },
    )
    return str(tmp_path)


class TestRunDirSortKey:
    # run directories collide within the same group+prefix+second more
    # often than you would expect during test suite runs (confirmed by
    # David) -- RunHomeMaker disambiguates with a plain, unpadded "_N"
    # suffix starting at "_0". A naive lexicographic sort of the full
    # directory name breaks once a collision count reaches double
    # digits ("_10" sorts before "_9" as strings) -- these tests use
    # "_9"/"_10" specifically to catch that, not just "does sorting
    # work at all".
    def test_double_digit_suffix_sorts_after_single_digit_within_one_group(
        self, tmp_path
    ):
        base = tmp_path / "acme"
        run_base = _make_run(base, "2026-01-01_00-00-00", "run-base-uuid", {})
        run_9 = _make_run(base, "2026-01-01_00-00-00_9", "run-9-uuid", {})
        run_10 = _make_run(base, "2026-01-01_00-00-00_10", "run-10-uuid", {})
        _write_archive_manifest(tmp_path, "acme", [run_10, run_9, run_base])
        results = _finder("$acme.results.:last()", str(tmp_path)).query()
        assert results.uuids == ["run-10-uuid"]

    def test_double_digit_suffix_sorts_after_single_digit_across_groups(
        self, tmp_path
    ):
        base = tmp_path / "acme"
        run_base = _make_run(base, "2026-01-01_00-00-00", "run-base-uuid", {})
        run_9 = _make_run(base, "2026-01-01_00-00-00_9", "run-9-uuid", {})
        run_10 = _make_run(base, "2026-01-01_00-00-00_10", "run-10-uuid", {})
        _write_archive_manifest(tmp_path, "acme", [run_10, run_9, run_base])
        results = _finder("$*.results.:last()", str(tmp_path)).query()
        assert results.uuids == ["run-10-uuid"]

    def test_unsuffixed_run_sorts_before_any_suffixed_collision(self, tmp_path):
        base = tmp_path / "acme"
        run_base = _make_run(base, "2026-01-01_00-00-00", "run-base-uuid", {})
        run_0 = _make_run(base, "2026-01-01_00-00-00_0", "run-0-uuid", {})
        _write_archive_manifest(tmp_path, "acme", [run_0, run_base])
        results = _finder("$acme.results.:first()", str(tmp_path)).query()
        assert results.uuids == ["run-base-uuid"]


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


class TestManifestOnNameOne:
    # :manifest() rides beside the run-selecting pointer in name_one
    # (STRUCTURE table's "Resolve terminating at name_one, with file
    # pointer" row) -- unlike files/csvpaths, a run's own manifest.json
    # is already a single dict, not an array, so there is no "filtered
    # list vs single entry" split: every matched run just resolves to
    # its own dict.
    def test_manifest_beside_a_pointer_in_the_literal_path_shape(
        self, acme_archive
    ):
        results = _finder(
            "$acme.results.customers/2025:first():manifest()", acme_archive
        ).resolve()
        assert results.results[0].data == {"run_uuid": "run1-uuid"}

    def test_manifest_beside_a_pointer_in_the_bare_shape(self, acme_archive):
        results = _finder(
            "$acme.results.:last():manifest()", acme_archive
        ).resolve()
        assert results.results[0].data == {"run_uuid": "run2-uuid"}

    def test_manifest_with_no_pointer_and_more_than_one_matching_run_raises(
        self, acme_archive
    ):
        # "customers/2025" matches both run1 and run2. Resolving full
        # manifest content always touches exactly one entity (settled
        # 2026-08-07), so this is illegal now, not "every run's own
        # manifest, pooled" as it used to be -- a pointer is required to
        # pick one run.
        finder = _finder("$acme.results.customers/2025:manifest()", acme_archive)
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_manifest_with_no_pointer_and_exactly_one_matching_run_still_works(
        self, tmp_path
    ):
        # a prefix that only ever matches one run needs no pointer --
        # there is nothing to pick between.
        base = tmp_path / "solo" / "customers" / "2025"
        run = _make_run(base, "2026-01-01_00-00-00", "solo-uuid", {})
        _write_archive_manifest(tmp_path, "solo", [run])
        results = _finder(
            "$solo.results.customers/2025:manifest()", str(tmp_path)
        ).resolve()
        assert results.results[0].data == {"run_uuid": "solo-uuid"}

    def test_manifest_does_not_count_as_a_second_pointer(self, acme_archive):
        # Manifest3 is VALUE-role, not POINTER -- combined with a real
        # pointer it must not trip "at most one pointer per chain".
        results = _finder(
            "$acme.results.customers/2025:first():manifest()", acme_archive
        ).query()
        assert results.uuids == ["run1-uuid"]

    def test_manifest_combined_with_name_three_raises(self, acme_archive):
        finder = _finder(
            "$acme.results.customers/2025:first():manifest().company_names",
            acme_archive,
        )
        with pytest.raises(ReferenceException3):
            finder.resolve()


class TestFieldAccessorFunctions:
    # generalized field-accessor wiring for RESULTS -- run-level field
    # accessors ride in name_one's combined chain, the same slot
    # :manifest() rides in; instance-level ones ride in name_three, the
    # same slot :errors()/etc. ride in. Reference3.RESULTS picks the
    # run-scope key, Reference3.RESULT the instance-scope key.
    def test_run_uuid_at_run_scope(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:first():run_uuid()", acme_archive
        ).resolve()
        assert results.results[0].data == "run1-uuid"

    def test_run_uuid_at_instance_scope(self, tmp_path):
        # _make_run's default fixture instance manifests only carry
        # "uuid" -- run_uuid at instance scope needs its own manifest
        # data with a "run_uuid" field actually present.
        base = tmp_path / "acme" / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        _write_json(
            run_dir / "company_names" / "manifest.json",
            {"uuid": "inst1-uuid", "run_uuid": "run1-uuid"},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        results = _finder(
            "$widgets.results.:first().company_names:run_uuid()",
            str(tmp_path),
        ).resolve()
        assert results.results[0].data == "run1-uuid"

    def test_uuid_at_instance_scope(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:first().company_names:uuid()",
            acme_archive,
        ).resolve()
        assert results.results[0].data == "inst1-uuid"

    def test_uuid_at_run_scope_gives_none_not_the_deprecated_field(
        self, acme_archive
    ):
        # :uuid()'s KEY has no Reference3.RESULTS entry at all -- run
        # scope's own bare "uuid" is the deprecated field (see #225-
        # adjacent findings) -- this must not accidentally surface it.
        results = _finder(
            "$acme.results.customers/2025:first():uuid()", acme_archive
        ).resolve()
        assert results.results[0].data is None

    def test_run_level_field_accessor_combined_with_name_three_raises(
        self, acme_archive
    ):
        finder = _finder(
            "$acme.results.customers/2025:first():run_uuid().company_names",
            acme_archive,
        )
        with pytest.raises(ReferenceException3):
            finder.resolve()

    def test_run_uuid_with_no_pointer_and_multiple_runs_is_poolable(
        self, acme_archive
    ):
        # unlike :manifest(), a field accessor stays poolable across
        # multiple matched runs with no pointer -- Rule 3.
        results = _finder(
            "$acme.results.customers/2025:run_uuid()", acme_archive
        ).resolve()
        assert sorted(r.data for r in results.results) == [
            "run1-uuid",
            "run2-uuid",
        ]

    def test_uuid_combined_with_all_is_poolable(self, acme_archive):
        # unlike an :errors()-style content accessor, a field accessor
        # combined with :all() is legal -- Rule 3.
        results = _finder(
            "$acme.results.customers/2025:first().:all():uuid()", acme_archive
        ).resolve()
        assert sorted(r.data for r in results.results) == [
            "inst1-uuid",
            "inst2-uuid",
        ]

    def test_serial_and_valid_scope_dependent_keys(self, tmp_path):
        # serial: same literal key at both scopes. valid: genuinely
        # different keys (all_valid at run scope, valid at instance
        # scope) -- the case Reference3.RESULT/RESULTS actually exists
        # for.
        base = tmp_path / "acme" / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(
            run_dir / "manifest.json",
            {"run_uuid": "run-uuid", "serial": True, "all_valid": False},
        )
        _write_json(
            run_dir / "company_names" / "manifest.json",
            {"uuid": "inst-uuid", "serial": True, "valid": True},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        run_serial = _finder(
            "$widgets.results.:first():serial()", str(tmp_path)
        ).resolve()
        assert run_serial.results[0].data is True

        instance_serial = _finder(
            "$widgets.results.:first().company_names:serial()", str(tmp_path)
        ).resolve()
        assert instance_serial.results[0].data is True

        run_valid = _finder(
            "$widgets.results.:first():valid()", str(tmp_path)
        ).resolve()
        assert run_valid.results[0].data is False

        instance_valid = _finder(
            "$widgets.results.:first().company_names:valid()", str(tmp_path)
        ).resolve()
        assert instance_valid.results[0].data is True

    def test_run_only_field_accessors(self, tmp_path):
        # status/method/hostname/username/time_completed/manifest_path/
        # named_paths_name -- run scope only, confirmed real keys in
        # results_registrar.py.
        base = tmp_path / "acme" / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(
            run_dir / "manifest.json",
            {
                "run_uuid": "run-uuid",
                "status": "complete",
                "method": "collect",
                "hostname": "box1",
                "username": "auser",
                "time_completed": "2026-08-09T00:00:00",
                "manifest_path": str(run_dir / "manifest.json"),
                "named_paths_name": "widgets",
            },
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        def resolve(fn):
            return _finder(
                f"$widgets.results.:first():{fn}()", str(tmp_path)
            ).resolve().results[0].data

        assert resolve("status") == "complete"
        assert resolve("method") == "collect"
        assert resolve("hostname") == "box1"
        assert resolve("username") == "auser"
        assert resolve("time_completed") == "2026-08-09T00:00:00"
        assert resolve("manifest_path") == str(run_dir / "manifest.json")
        assert resolve("named_paths_name") == "widgets"

    def test_completed_and_files_complete_scope_dependent_keys(self, tmp_path):
        base = tmp_path / "acme" / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(
            run_dir / "manifest.json",
            {
                "run_uuid": "run-uuid",
                "all_completed": True,
                "all_expected_files": False,
            },
        )
        _write_json(
            run_dir / "company_names" / "manifest.json",
            {"uuid": "inst-uuid", "completed": True, "files_expected": True},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        run_completed = _finder(
            "$widgets.results.:first():completed()", str(tmp_path)
        ).resolve()
        assert run_completed.results[0].data is True

        run_files_complete = _finder(
            "$widgets.results.:first():files_complete()", str(tmp_path)
        ).resolve()
        assert run_files_complete.results[0].data is False

        instance_completed = _finder(
            "$widgets.results.:first().company_names:completed()", str(tmp_path)
        ).resolve()
        assert instance_completed.results[0].data is True

        instance_files_complete = _finder(
            "$widgets.results.:first().company_names:files_complete()",
            str(tmp_path),
        ).resolve()
        assert instance_files_complete.results[0].data is True

    def test_named_file_name_shared_key_both_scopes(self, tmp_path):
        base = tmp_path / "acme" / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(
            run_dir / "manifest.json",
            {"run_uuid": "run-uuid", "named_file_name": "orders.csv"},
        )
        _write_json(
            run_dir / "company_names" / "manifest.json",
            {"uuid": "inst-uuid", "named_file_name": "orders.csv"},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        run_name = _finder(
            "$widgets.results.:first():named_file_name()", str(tmp_path)
        ).resolve()
        assert run_name.results[0].data == "orders.csv"

        instance_name = _finder(
            "$widgets.results.:first().company_names:named_file_name()",
            str(tmp_path),
        ).resolve()
        assert instance_name.results[0].data == "orders.csv"

    def test_instance_only_field_accessors(self, acme_archive):
        run_dir = acme_archive + "/acme/customers/2025/2026-01-01_00-00-00"
        _write_json(
            Path(run_dir) / "company_names" / "manifest.json",
            {
                "uuid": "inst1-uuid",
                "instance_identity": "company_names",
                "actual_data_file": "/data/acme/actual.csv",
                "origin_data_file": "/data/acme/origin.csv",
                "file_fingerprints": {"data.csv": "abc123"},
                "source_mode_preceding": True,
                "preceding_instance_identity": "0",
            },
        )

        def resolve(fn):
            ref = f"$acme.results.customers/2025:first().company_names:{fn}()"
            return _finder(ref, acme_archive).resolve().results[0].data

        assert resolve("identity") == "company_names"
        assert resolve("actual_data_file") == "/data/acme/actual.csv"
        assert resolve("origin_data_file") == "/data/acme/origin.csv"
        assert resolve("file_fingerprints") == {"data.csv": "abc123"}
        assert resolve("source_mode_preceding") is True
        assert resolve("preceding_instance_identity") == "0"

    def test_manifest_path_reachable_at_instance_scope_too(self, tmp_path):
        # confirmed present in the real Result Instance Manifest despite
        # manifest_field_functions_proposal.md flagging it as a gap when
        # that doc was written.
        base = tmp_path / "acme" / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        instance_manifest_path = str(run_dir / "company_names" / "manifest.json")
        _write_json(run_dir / "manifest.json", {"run_uuid": "run-uuid"})
        _write_json(
            run_dir / "company_names" / "manifest.json",
            {"uuid": "inst-uuid", "manifest_path": instance_manifest_path},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        result = _finder(
            "$widgets.results.:first().company_names:manifest_path()",
            str(tmp_path),
        ).resolve()
        assert result.results[0].data == instance_manifest_path


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

    def test_errors_with_idchain_filters_to_matching_source(
        self, acme_archive, instance_dir
    ):
        # confirmed against the real Error class: entries are keyed by
        # "source" (Matchable.my_chain), not literally "idchain" -- the
        # idchain string is just the value being matched against it.
        errors = [
            {"source": "add[0]string[2]", "message": "bad add"},
            {"source": "name[1]", "message": "bad name"},
        ]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':errors(:idchain("add[0]string[2]"))',
            acme_archive,
        ).resolve()
        assert results.results[0].data == [errors[0]]

    def test_errors_with_idchain_no_match_returns_empty_list(
        self, acme_archive, instance_dir
    ):
        # a legitimate empty list, not None and not an error -- the
        # file was found and read fine, it just has no matching entry.
        errors = [{"source": "name[1]", "message": "bad name"}]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':errors(:idchain("add[0]string[2]"))',
            acme_archive,
        ).resolve()
        assert results.results[0].data == []

    def test_errors_with_idchain_regex_filters_by_search_not_full_match(
        self, acme_archive, instance_dir
    ):
        # a regex idchain arg uses search(), so it does not need to
        # anchor to the whole source string -- it just needs to find
        # the match-component pattern somewhere within it.
        errors = [
            {"source": "add[0]string[2]", "message": "bad add"},
            {"source": "add[1]string[2]", "message": "different add"},
            {"source": "name[1]", "message": "bad name"},
        ]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':errors(:idchain(/add\\[\\d\\]/))',
            acme_archive,
        ).resolve()
        assert results.results[0].data == [errors[0], errors[1]]

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

    def test_accessor_combined_with_all_raises(self, acme_archive):
        # run1 has two instances: company_names and "1", each with its
        # own separate meta.json. Resolving full content always touches
        # exactly one entity (settled 2026-08-07), so :all() (every
        # instance in the run) combined with an accessor is illegal now,
        # not "each instance's own file, pooled" as it used to be -- a
        # specific identity is required to pick one instance.
        base = f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
        os.makedirs(f"{base}/company_names", exist_ok=True)
        os.makedirs(f"{base}/1", exist_ok=True)
        with open(f"{base}/company_names/meta.json", "w") as f:
            json.dump({"which": "company_names"}, f)
        with open(f"{base}/1/meta.json", "w") as f:
            json.dump({"which": "1"}, f)
        finder = _finder(
            "$acme.results.customers/2025:first().:all():meta()", acme_archive
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_accessor_combined_with_a_specific_identity_still_works(
        self, acme_archive
    ):
        base = f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
        os.makedirs(f"{base}/company_names", exist_ok=True)
        with open(f"{base}/company_names/meta.json", "w") as f:
            json.dump({"which": "company_names"}, f)
        results = _finder(
            "$acme.results.customers/2025:first().company_names:meta()",
            acme_archive,
        ).resolve()
        assert results.results[0].data == {"which": "company_names"}


class TestGlobalArchiveLedger:
    # Rule 1a: "*" at root_major combined with a bare :manifest() is the
    # one exception to root_major=="*" being unsupported -- it resolves
    # to the Archive Run Manifest, the single global ledger at the
    # archive root already used internally to discover runs.
    def test_query_returns_the_global_ledger_path_with_no_uuid(self, acme_archive):
        results = _finder("$*.results.:manifest()", acme_archive).query()
        assert results.files == [f"{acme_archive}/manifest.json"]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_global_ledger_as_parsed_json(self, acme_archive):
        results = _finder("$*.results.:manifest()", acme_archive).resolve()
        data = results.results[0].data
        assert isinstance(data, list)
        assert {e["named_paths_name"] for e in data} == {"acme"}

    def test_star_with_a_bare_pointer_is_supported(self, acme_archive):
        # '*' traversal is supported now for the bare-pointer case (see
        # TestStarTraversal below) -- with only one named-results group
        # in this fixture, this just confirms it resolves to that
        # group's own last run rather than raising.
        finder = _finder("$*.results.:last()", acme_archive)
        results = finder.query()
        assert len(results.results) == 1
        assert results.results[0].uuid == "run2-uuid"

    def test_star_with_path_narrowing_is_still_not_supported(self, acme_archive):
        finder = _finder("$*.results.customers/2025:last()", acme_archive)
        with pytest.raises(ReferenceException3):
            finder.query()


class TestGlobalArchiveLedgerOrdinalIndexing:
    # Rule 1b: a pointer (:first()/:last()/:index(n)) riding before the
    # bare :manifest() selects one entry out of the ledger by ordinal
    # position, instead of dumping the whole thing. The archive ledger
    # has no "uuid" key of its own (only "run_uuid"), unlike the files/
    # csvpaths ledgers -- a separate, minimal fixture is used here rather
    # than the shared acme_archive fixture, which does not write
    # "run_uuid" into its entries at all.
    LEDGER = [
        {"named_paths_name": "acme", "run_uuid": "run-1"},
        {"named_paths_name": "acme", "run_uuid": "run-2"},
        {"named_paths_name": "acme", "run_uuid": "run-3"},
    ]

    def _archive(self, tmp_path) -> str:
        _write_json(tmp_path / "manifest.json", self.LEDGER)
        return str(tmp_path)

    def test_last_gives_the_most_recent_run(self, tmp_path):
        archive = self._archive(tmp_path)
        results = _finder("$*.results.:last():manifest()", archive).resolve()
        assert results.results[0].data == self.LEDGER[-1]

    def test_index_gives_the_nth_run(self, tmp_path):
        archive = self._archive(tmp_path)
        results = _finder("$*.results.:index(1):manifest()", archive).resolve()
        assert results.results[0].data == self.LEDGER[1]

    def test_out_of_range_index_gives_no_results(self, tmp_path):
        archive = self._archive(tmp_path)
        results = _finder("$*.results.:index(99):manifest()", archive).query()
        assert len(results.results) == 0

    def test_query_gives_the_ledger_path_with_the_entrys_own_run_uuid(
        self, tmp_path
    ):
        archive = self._archive(tmp_path)
        results = _finder("$*.results.:last():manifest()", archive).query()
        assert results.files == [f"{archive}/manifest.json"]
        assert results.results[0].uuid == "run-3"

    def test_manifest_then_pointer_order_also_works(self, tmp_path):
        # order-insensitivity was missing on _pointer_before_manifest
        # and fixed 2026-08-10 -- this exact shape previously fell
        # through to _query_star_traversal's own "not yet supported"
        # raise instead of being recognized as Rule 1b.
        archive = self._archive(tmp_path)
        results = _finder("$*.results.:manifest():last()", archive).query()
        assert results.results[0].uuid == "run-3"


class TestStarTraversal:
    # only the bare-pointer flatten case is supported for results (see
    # _query_star_traversal's own docstring for why) -- every named-
    # results group's discovered runs pool into one combined list,
    # sorted by each run directory's own trailing timestamp segment
    # (not the full path, which would sort by group name first when
    # pooling across groups), reduced by one terminal pointer.
    def test_last_across_every_group_is_the_true_most_recent(self, two_group_archive):
        # widgets' only run (2026-01-03) is the global most-recent, not
        # acme's own last run (2026-01-02) -- proves pooling crosses
        # groups and is truly sorted by timestamp, not enumeration
        # order (widgets is written first in the merged manifest).
        results = _finder("$*.results.:last()", two_group_archive).query()
        assert len(results.results) == 1
        assert results.results[0].uuid == "widgets-run1-uuid"

    def test_first_across_every_group_is_the_true_earliest(self, two_group_archive):
        results = _finder("$*.results.:first()", two_group_archive).query()
        assert results.results[0].uuid == "acme-run1-uuid"

    def test_index_selects_by_chronological_position(self, two_group_archive):
        # chronological order: acme-run1, acme-run2, widgets-run1
        results = _finder("$*.results.:index(1)", two_group_archive).query()
        assert results.results[0].uuid == "acme-run2-uuid"

    def test_all_is_not_yet_supported(self, two_group_archive):
        # results' own :all() already means "every instance within one
        # run" (name_three) -- no syntactic home for group-by-group
        # traversal semantics exists yet, unlike files/csvpaths.
        with pytest.raises(ReferenceException3):
            _finder("$*.results.:all()", two_group_archive).query()

    def test_name_three_combined_with_traversal_is_not_yet_supported(
        self, two_group_archive
    ):
        with pytest.raises(ReferenceException3):
            _finder("$*.results.:last().0", two_group_archive).query()


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
