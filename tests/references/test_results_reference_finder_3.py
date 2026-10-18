import json
import os
from pathlib import Path

import pytest

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.results_reference_finder_3 import ResultsReferenceFinder3
from csvpath.util.date_util import DateUtility as daut
from csvpath.util.path_util import PathUtility as pathu

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
    def __init__(self, archive: str, log_file: str | None = None):
        self._archive = archive
        self.log_file = log_file

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
    def __init__(self, archive: str, log_file: str | None = None):
        self.results_manager = _FakeResultsManager(archive)
        self.config = _FakeConfig(archive, log_file=log_file)


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


def _finder(
    reference: str,
    archive: str,
    log_file: str | None = None,
    variables: dict | None = None,
) -> ResultsReferenceFinder3:
    csvpaths = _FakeCsvPaths(archive, log_file=log_file)
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return ResultsReferenceFinder3(csvpaths=csvpaths, ref=ref, variables=variables)


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
    # acme (2 runs) + widgets (1 run, chronologically LATEST overall) --
    # both groups' runs are flat (zero-level, direct children of their
    # own group's home), since a bare pointer now only considers
    # zero-level runs (settled 2026-08-10) -- a nested group here would
    # be silently excluded from traversal entirely, defeating this
    # fixture's whole point (proving pooling crosses groups correctly).
    # widgets is written FIRST in the merged manifest on purpose -- a
    # naive (unsorted) "last" would give acme's own last run
    # (2026-01-02) instead of the true global-latest (widgets',
    # 2026-01-03), so this fails if the '*' traversal sort-by-trailing-
    # segment logic is ever removed/broken.
    acme_base = tmp_path / "acme"
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
            pathu.resep(f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00")
        ]


class TestHavingFiltersRunsByInstanceIdentity:
    # ':having("identity")' widened to RESULTS 2026-08-27 (deferred-work
    # bucket-list entry) -- mirrors CsvpathsReferenceFinder3's own
    # ':having()' one level down: filters the candidate RUN pool to
    # those containing an instance (csvpath statement result) with the
    # given identity, BEFORE any pointer reduces. acme_archive's run1
    # has "company_names"/"1"; run2 has only "0" -- proves filtering,
    # not just "identity happens to exist somewhere."
    def test_having_then_pointer_gives_the_qualifying_run(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:last():having(\"company_names\")",
            acme_archive,
        ).query()
        assert results.uuids == ["run1-uuid"]

    def test_order_of_pointer_and_having_does_not_matter(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:having(\"company_names\"):last()",
            acme_archive,
        ).query()
        assert results.uuids == ["run1-uuid"]

    def test_having_excludes_a_run_without_the_identity(self, acme_archive):
        # run2 is chronologically last, but only run1 "has" company_names
        # -- proves the filter really runs before the pointer, not after.
        results = _finder(
            "$acme.results.customers/2025:last():having(\"0\")", acme_archive
        ).query()
        assert results.uuids == ["run2-uuid"]

    def test_having_with_no_matching_run_gives_empty(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:last():having(\"nonexistent\")",
            acme_archive,
        ).query()
        assert results.uuids == []

    def test_having_with_no_pointer_returns_every_qualifying_run_unreduced(
        self, acme_archive
    ):
        results = _finder(
            "$acme.results.customers/2025:having(\"company_names\")", acme_archive
        ).query()
        assert results.uuids == ["run1-uuid"]

    def test_having_accepts_a_registered_variable_as_its_argument(self, acme_archive):
        # end-to-end proof of the central, eager @variable-argument
        # resolution added 2026-08-27 -- real grammar parse through to a
        # real registered function (:having(), ARG_TYPES = (str,)),
        # same result as the literal-string version above.
        results = _finder(
            "$acme.results.customers/2025:last():having(@id)",
            acme_archive,
            variables={"id": "company_names"},
        ).query()
        assert results.uuids == ["run1-uuid"]


class TestNoPointerReturnsEveryRun:
    def test_no_pointer_returns_every_run_unreduced(self, acme_archive):
        results = _finder("$acme.results.customers/2025", acme_archive).query()
        assert results.uuids == ["run1-uuid", "run2-uuid"]


class TestNameRegexPathSegment:
    # :name(/regex/) as a template path segment -- added 2026-08-27, see
    # the "name_one path segment cannot be a regex" bucket-list entry.
    @pytest.fixture
    def two_year_archive(self, tmp_path):
        run_2025 = _make_run(
            tmp_path / "acme" / "customers" / "2025",
            "2026-01-01_00-00-00",
            "run-2025-uuid",
            {},
        )
        run_2026 = _make_run(
            tmp_path / "acme" / "customers" / "2026",
            "2026-02-01_00-00-00",
            "run-2026-uuid",
            {},
        )
        _write_archive_manifest(tmp_path, "acme", [run_2025, run_2026])
        return str(tmp_path)

    def test_regex_matches_only_the_one_year_it_searches(self, two_year_archive):
        results = _finder(
            "$acme.results.customers/:name(/2025/):first()", two_year_archive
        ).query()
        assert results.uuids == ["run-2025-uuid"]

    def test_regex_matching_neither_year_returns_empty(self, two_year_archive):
        results = _finder(
            "$acme.results.customers/:name(/2027/):first()", two_year_archive
        ).query()
        assert results.files == []

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
    # "segment" is itself a version-selecting function. A bare pointer
    # alone means zero-level only -- direct children of the group's own
    # root -- settled 2026-08-10; see :flatten() for the any-depth case
    # this used to cover. A bare ':all()' degenerates to the same
    # zero-level meaning (compendium 4.2b, settled 2026-09-21) -- it is
    # NOT the any-depth tool; that is still ':flatten()''s job.
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

    def test_bare_flatten_returns_every_run(self, flat_archive):
        # ':flatten()' -- every run regardless of depth, including flat
        # ones (same set ':all()' now also reaches, per the test below --
        # ':flatten()' remains the right tool once a deeper run is also
        # in the mix, since ':all()' stays zero-level-only).
        results = _finder("$flat.results.:flatten()", flat_archive).query()
        assert set(results.uuids) == {"run1-uuid", "run2-uuid"}

    def test_bare_all_includes_flat_runs_unreduced(self, flat_archive):
        # REVISED 2026-09-21 (was: "':all()' requires exactly one level,
        # so it finds neither" -- settled 2026-08-11, now superseded).
        # Per compendium 4.2b, ':all()' degenerates to the run_dir slot's
        # own zero-level meaning -- both of flat_archive's runs are
        # zero-level, so with no pointer, both come back unreduced, same
        # as a bare '*' or bare pointer-less query would give.
        results = _finder("$flat.results.:all()", flat_archive).query()
        assert set(results.uuids) == {"run1-uuid", "run2-uuid"}

    def test_bare_pointer_does_not_find_a_run_under_a_deep_template(
        self, acme_archive
    ):
        # bare :last() means zero-level only -- acme_archive's runs sit
        # under "customers/2025", two levels deep, so a bare pointer no
        # longer finds them at all (settled 2026-08-10). Reaching them
        # needs an explicit path prefix (customers/2025:last(), already
        # covered by TestVersionPointer) or :flatten().
        results = _finder("$acme.results.:last()", acme_archive).query()
        assert results.uuids == []

    def test_bare_pointer_finds_a_flat_run_alongside_a_deep_one(
        self, tmp_path
    ):
        # confirms the new restriction is specifically "zero levels",
        # not "broken entirely" -- a genuinely flat run for the same
        # group as a deep one is still found, and correctly preferred
        # over it even when the deep one is chronologically later.
        flat_base = tmp_path / "mixed"
        flat_run = _make_run(flat_base, "2026-01-01_00-00-00", "flat-uuid", {})
        deep_run = _make_run(
            flat_base / "customers" / "2025",
            "2026-01-02_00-00-00",
            "deep-uuid",
            {},
        )
        _write_archive_manifest(tmp_path, "mixed", [flat_run, deep_run])
        results = _finder("$mixed.results.:last()", str(tmp_path)).query()
        assert results.uuids == ["flat-uuid"]


class TestFlatten:
    # ':flatten()' is the any-depth pooling counterpart of what a bare
    # pointer used to do before it was redefined to zero-level-only
    # (settled 2026-08-10) -- unlike a bare pointer (zero levels) or
    # '*' (exactly one level), ':flatten()' matches any remaining depth.
    def test_bare_flatten_finds_the_true_latest_regardless_of_depth(
        self, tmp_path
    ):
        base = tmp_path / "mixed"
        flat_run = _make_run(base, "2026-01-01_00-00-00", "flat-uuid", {})
        deep_run = _make_run(
            base / "customers" / "2025", "2026-01-02_00-00-00", "deep-uuid", {}
        )
        _write_archive_manifest(tmp_path, "mixed", [flat_run, deep_run])
        results = _finder(
            "$mixed.results.:flatten():last()", str(tmp_path)
        ).query()
        assert results.uuids == ["deep-uuid"]

    def test_bare_flatten_still_finds_a_flat_run_when_it_is_latest(
        self, tmp_path
    ):
        base = tmp_path / "mixed2"
        flat_run = _make_run(base, "2026-01-02_00-00-00", "flat-uuid", {})
        deep_run = _make_run(
            base / "customers" / "2025", "2026-01-01_00-00-00", "deep-uuid", {}
        )
        _write_archive_manifest(tmp_path, "mixed2", [flat_run, deep_run])
        results = _finder(
            "$mixed2.results.:flatten():last()", str(tmp_path)
        ).query()
        assert results.uuids == ["flat-uuid"]

    def test_prefixed_flatten_matches_any_depth_beyond_the_prefix(
        self, tmp_path
    ):
        base = tmp_path / "beta_group"
        shallow_run = _make_run(
            base / "beta" / "x", "2026-01-01_00-00-00", "shallow-uuid", {}
        )
        deep_run = _make_run(
            base / "beta" / "y" / "z", "2026-01-02_00-00-00", "deep-uuid", {}
        )
        other_run = _make_run(
            base / "gamma", "2026-01-03_00-00-00", "other-uuid", {}
        )
        _write_archive_manifest(
            tmp_path, "beta_group", [shallow_run, deep_run, other_run]
        )
        results = _finder(
            "$beta_group.results.beta/:flatten():last()", str(tmp_path)
        ).query()
        assert results.uuids == ["deep-uuid"]

    def test_bare_flatten_rejects_an_argument(self, tmp_path):
        base = tmp_path / "acme"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1-uuid", {})
        _write_archive_manifest(tmp_path, "acme", [run1])
        with pytest.raises(ReferenceException3):
            _finder(
                '$acme.results.:flatten("x"):last()', str(tmp_path)
            ).query()

    def test_prefixed_flatten_rejects_an_argument(self, tmp_path):
        base = tmp_path / "acme"
        run1 = _make_run(base / "beta", "2026-01-01_00-00-00", "run1-uuid", {})
        _write_archive_manifest(tmp_path, "acme", [run1])
        with pytest.raises(ReferenceException3):
            _finder(
                '$acme.results.beta/:flatten("x"):last()', str(tmp_path)
            ).query()

    def test_flatten_combined_with_traversal_pools_any_depth_across_every_group(
        self, tmp_path
    ):
        # closes a real gap (fixed 2026-08-18, alongside CSVPATHS'
        # analogous ':having()' fix) -- unlike two_group_archive
        # (deliberately both-flat, to prove cross-group pooling by
        # time), this fixture has genuine depth variance -- acme's
        # latest run is nested, widgets' only run is flat -- proving
        # ':flatten()' finds the true global-latest regardless of depth
        # AND regardless of which group it belongs to.
        acme_base = tmp_path / "acme"
        acme_flat = _make_run(acme_base, "2026-01-01_00-00-00", "acme-flat", {})
        acme_deep = _make_run(
            acme_base / "customers" / "2025", "2026-01-05_00-00-00", "acme-deep", {}
        )
        widgets_base = tmp_path / "widgets"
        widgets_run = _make_run(
            widgets_base, "2026-01-03_00-00-00", "widgets-run", {}
        )
        _write_archive_manifest_multi(
            tmp_path,
            {"acme": [acme_flat, acme_deep], "widgets": [widgets_run]},
        )
        # a bare pointer (zero-level only) misses acme's own deep run
        # entirely and gives widgets' instead -- confirms ':flatten()'
        # below is doing real work, not just passing through unchanged.
        bare = _finder("$*.results.:last()", str(tmp_path)).query()
        assert bare.results[0].uuid == "widgets-run"

        flattened = _finder(
            "$*.results.:flatten():last()", str(tmp_path)
        ).query()
        assert flattened.results[0].uuid == "acme-deep"

    def test_flatten_combined_with_a_field_accessor_also_works(self, tmp_path):
        base = tmp_path / "acme"
        deep_run = _make_run(
            base / "customers" / "2025", "2026-01-01_00-00-00", "deep-uuid", {}
        )
        _write_json(
            Path(deep_run) / "manifest.json",
            {"run_uuid": "deep-uuid", "named_paths_name": "acme"},
        )
        _write_archive_manifest(tmp_path, "acme", [deep_run])
        results = _finder(
            "$*.results.:flatten():last():named_paths_name()", str(tmp_path)
        ).resolve()
        assert results.results[0].uuid == "deep-uuid"
        assert results.results[0].data == "acme"

    def test_manifest_combined_with_a_field_accessor_narrows_not_whole_entry(
        self, tmp_path
    ):
        # added 2026-08-28 -- David's own worked example ("get all the
        # most recent acme registration uuids used in runs"),
        # $*.results.:flatten():manifest():named_file_uuid(). Found by
        # tracing (not guessed): _extract_data()'s own has_manifest
        # branch used to return the WHOLE manifest.json entry the moment
        # ':manifest()' was present anywhere in name_one, even with a
        # field accessor ALSO chained alongside it -- it never checked
        # for one, so the narrowing silently never applied. No pointer
        # here (matches David's own syntax exactly) -- every matched run
        # comes back, each narrowed to its own named_file_uuid value.
        run1 = _make_run(
            tmp_path / "acme", "2026-01-01_00-00-00", "run1-uuid", {}
        )
        _write_json(
            Path(run1) / "manifest.json",
            {"run_uuid": "run1-uuid", "named_file_uuid": "file-uuid-1"},
        )
        run2 = _make_run(
            tmp_path / "acme", "2026-01-02_00-00-00", "run2-uuid", {}
        )
        _write_json(
            Path(run2) / "manifest.json",
            {"run_uuid": "run2-uuid", "named_file_uuid": "file-uuid-2"},
        )
        _write_archive_manifest(tmp_path, "acme", [run1, run2])
        results = _finder(
            "$*.results.:flatten():manifest():named_file_uuid()", str(tmp_path)
        ).resolve()
        assert {r.data for r in results.results} == {"file-uuid-1", "file-uuid-2"}
        # not the whole dict -- confirms narrowing actually happened,
        # not just that no error was raised.
        assert all(isinstance(r.data, str) for r in results.results)

    def test_manifest_alone_with_no_field_accessor_still_gives_the_whole_entry(
        self, tmp_path
    ):
        # regression check -- ':manifest()' bare (no field accessor
        # chained) must keep its own pre-existing, already-shipped
        # behavior unchanged.
        run1 = _make_run(
            tmp_path / "acme", "2026-01-01_00-00-00", "run1-uuid", {}
        )
        _write_json(
            Path(run1) / "manifest.json",
            {"run_uuid": "run1-uuid", "named_file_uuid": "file-uuid-1"},
        )
        _write_archive_manifest(tmp_path, "acme", [run1])
        results = _finder(
            "$*.results.:flatten():manifest()", str(tmp_path)
        ).resolve()
        assert results.results[0].data == {
            "run_uuid": "run1-uuid",
            "named_file_uuid": "file-uuid-1",
        }

    def test_field_accessor_order_before_manifest_also_works(self, tmp_path):
        # order-independence, same as the ordinary pointer+field-
        # accessor position already has -- ':named_file_uuid():manifest()'
        # means the same thing as ':manifest():named_file_uuid()'.
        run1 = _make_run(
            tmp_path / "acme", "2026-01-01_00-00-00", "run1-uuid", {}
        )
        _write_json(
            Path(run1) / "manifest.json",
            {"run_uuid": "run1-uuid", "named_file_uuid": "file-uuid-1"},
        )
        _write_archive_manifest(tmp_path, "acme", [run1])
        results = _finder(
            "$*.results.:flatten():named_file_uuid():manifest()", str(tmp_path)
        ).resolve()
        assert results.results[0].data == "file-uuid-1"

    def test_literal_root_also_gets_the_narrowing_fix(self, tmp_path):
        # confirms this is not '*'-traversal-specific -- the bug lived
        # in _extract_data(), shared by every root_major shape.
        base = tmp_path / "acme" / "customers" / "2025"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1-uuid", {})
        _write_json(
            Path(run1) / "manifest.json",
            {"run_uuid": "run1-uuid", "named_file_uuid": "file-uuid-1"},
        )
        _write_archive_manifest(tmp_path, "acme", [run1])
        results = _finder(
            "$acme.results.customers/2025:first():manifest():named_file_uuid()",
            str(tmp_path),
        ).resolve()
        assert results.results[0].data == "file-uuid-1"

    def test_combined_with_name_three_is_not_supported(self, tmp_path):
        run1 = _make_run(
            tmp_path / "acme", "2026-01-01_00-00-00", "run1-uuid", {"orders": "o1"}
        )
        _write_json(
            Path(run1) / "manifest.json",
            {"run_uuid": "run1-uuid", "named_file_uuid": "file-uuid-1"},
        )
        _write_archive_manifest(tmp_path, "acme", [run1])
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.results.:flatten():manifest():named_file_uuid().orders",
                str(tmp_path),
            ).resolve()

    def test_all_partitions_by_group_at_star_traversal(self, tmp_path):
        # REVISED 2026-09-21 -- superseded a test that proved ':all()'
        # partitioned by a composite (group, template-value) key across
        # star traversal ("THE ':all()' MEANING COLLISION AT STAR
        # TRAVERSAL"). That scenario no longer applies: per compendium
        # 4.2b, bare ':all()' degenerates to the run_dir slot's own
        # zero-level meaning, so it no longer groups by template value
        # at all -- only by named-results group, which star traversal
        # already partitions by inherently. acme has two zero-level
        # runs, widgets has one -- one "last" per group is still the
        # right thing to prove, just without a template-value dimension.
        acme_1 = _make_run(tmp_path / "acme", "2026-01-01_00-00-00", "acme-1", {})
        acme_2 = _make_run(tmp_path / "acme", "2026-01-03_00-00-00", "acme-2", {})
        widgets_1 = _make_run(
            tmp_path / "widgets", "2026-01-02_00-00-00", "widgets-1", {}
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_1, acme_2], "widgets": [widgets_1]}
        )
        results = _finder("$*.results.:all():last()", str(tmp_path)).query()
        assert sorted(results.uuids) == ["acme-2", "widgets-1"]

    def test_all_combined_with_flatten_is_rejected(self, two_group_archive):
        # each is its own depth/grouping choice -- same mutual-exclusion
        # rule the literal-root case already enforces.
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.results.:all():flatten():last()", two_group_archive
            ).query()

    def test_all_combined_with_a_field_accessor_also_works(self, tmp_path):
        # REVISED 2026-09-21: ':all()' is zero-level now, not one-level
        # -- the run moved to a direct child of "acme" to match.
        acme_run = _make_run(
            tmp_path / "acme", "2026-01-01_00-00-00", "acme-flat", {}
        )
        _write_json(
            Path(acme_run) / "manifest.json",
            {"run_uuid": "acme-flat", "named_paths_name": "acme"},
        )
        _write_archive_manifest(tmp_path, "acme", [acme_run])
        results = _finder(
            "$*.results.:all():last():named_paths_name()", str(tmp_path)
        ).resolve()
        assert len(results.results) == 1
        assert results.results[0].uuid == "acme-flat"
        assert results.results[0].data == "acme"


class TestAllGrouping:
    # REVISED 2026-09-21 (was: "':all()' and '*' stay depth peers, exactly
    # one level; ':all()' additionally groups by whatever value occupies
    # that one wildcarded position" -- settled 2026-08-10, now superseded).
    # Per compendium 4.2b, ':all()' degenerates to '*'s zero-level meaning
    # whenever it occupies the run_dir slot -- which is every position the
    # current implementation recognizes it in (bare, or as the trailing
    # segment after a fixed literal/prefix). It never groups by a template
    # value; that is ':groups()'s job (any depth, see TestGroups below),
    # not ':all()'s.
    def test_bare_all_with_pointer_degenerates_to_single_zero_level_result(
        self, tmp_path
    ):
        # REVISED 2026-09-21 -- supersedes "David's three templates
        # example" (bare ':all()' used to group by whatever 1-level
        # template a run landed under; now degenerates to zero-level per
        # compendium 4.2b, so there is nothing left here to group by --
        # three flat runs, one pooled "last" among them).
        base = tmp_path / "alpha"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run-1", {})
        run2 = _make_run(base, "2026-01-02_00-00-00", "run-2", {})
        run3 = _make_run(base, "2026-01-03_00-00-00", "run-3", {})
        _write_archive_manifest(tmp_path, "alpha", [run1, run2, run3])
        results = _finder("$alpha.results.:all():last()", str(tmp_path)).query()
        assert results.uuids == ["run-3"]

    def test_all_with_first_gives_the_zero_level_earliest(self, tmp_path):
        base = tmp_path / "alpha"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run-1", {})
        run2 = _make_run(base, "2026-01-02_00-00-00", "run-2", {})
        _write_archive_manifest(tmp_path, "alpha", [run1, run2])
        results = _finder("$alpha.results.:all():first()", str(tmp_path)).query()
        assert results.uuids == ["run-1"]

    def test_all_with_no_pointer_includes_zero_level_only(self, tmp_path):
        # REVISED 2026-09-21 (was: "still requires exactly one level" --
        # superseded, see the 4.2b degenerate-grouping fix). The 1-level
        # "zero/" run is now excluded, and the flat run is included,
        # unreduced -- the opposite of the old expectation.
        base = tmp_path / "alpha"
        zero_run = _make_run(base / "zero", "2026-01-01_00-00-00", "zero-1", {})
        flat_run = _make_run(base, "2026-01-02_00-00-00", "flat-1", {})
        _write_archive_manifest(tmp_path, "alpha", [zero_run, flat_run])
        results = _finder("$alpha.results.:all()", str(tmp_path)).query()
        assert results.uuids == ["flat-1"]

    def test_prefixed_all_degenerates_to_pooled_result(self, tmp_path):
        # REVISED 2026-09-21 (was: "groups by the next level" --
        # superseded). ':all()' still sits at the run_dir slot despite
        # the fixed "beta/" prefix, so this pools every 1-level run
        # under "beta/" into one flat set and gives the single overall
        # latest, same as "beta/*" would -- not one result per distinct
        # next-level value. Runs moved to be direct children of "beta"
        # (previously "beta/x", "beta/y" -- a 2-level fixture that no
        # longer matches this 1-level pattern at all).
        base = tmp_path / "acme"
        run1 = _make_run(base / "beta", "2026-01-01_00-00-00", "beta-1", {})
        run2 = _make_run(base / "beta", "2026-01-02_00-00-00", "beta-2", {})
        other_run = _make_run(base / "gamma", "2026-01-03_00-00-00", "gamma-1", {})
        _write_archive_manifest(tmp_path, "acme", [run1, run2, other_run])
        results = _finder(
            "$acme.results.beta/:all():last()", str(tmp_path)
        ).query()
        assert results.uuids == ["beta-2"]

    def test_all_grouping_combined_with_manifest_is_not_yet_supported(
        self, tmp_path
    ):
        # REVISED 2026-09-21: the fixture run moved to zero-level (was
        # 1-level "zero/", which ':all()' no longer matches at all --
        # with no candidates, group_key_for would come back empty/falsy
        # and this exception would never trigger).
        base = tmp_path / "alpha"
        run1 = _make_run(base, "2026-01-01_00-00-00", "flat-1", {})
        _write_archive_manifest(tmp_path, "alpha", [run1])
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.results.:all():last():manifest()", str(tmp_path)
            ).query()


class TestAllGroupingAtAMiddlePosition:
    # added 2026-09-22, closing the deferred-work bucket list gap of the
    # same name. Genuinely different from every TestAllGrouping case
    # above: there, ':all()' always sits at the run_dir slot itself
    # (degenerate, per compendium 4.2b); here it occupies a real MIDDLE
    # template segment, grouping by whatever value is found there, with
    # required literal/wildcard structure after it before the implied
    # run_dir -- the normative doc's own worked example:
    # "$alpha.results.test/:all()/one:last()" -- "the set of last runs
    # for each group of runs with 3-level templates where the first
    # level is 'test' and the third level is 'one', grouped by the
    # values of the 2nd template level."
    def test_groups_by_the_middle_segment_last_within_each_group(self, tmp_path):
        base = tmp_path / "alpha" / "test"
        x1 = _make_run(base / "x" / "one", "2026-01-01_00-00-00", "x-1", {})
        x2 = _make_run(base / "x" / "one", "2026-01-02_00-00-00", "x-2", {})
        y1 = _make_run(base / "y" / "one", "2026-01-03_00-00-00", "y-1", {})
        _write_archive_manifest(tmp_path, "alpha", [x1, x2, y1])
        results = _finder(
            "$alpha.results.test/:all()/one:last()", str(tmp_path)
        ).query()
        assert set(results.uuids) == {"x-2", "y-1"}

    def test_non_matching_runs_are_excluded(self, tmp_path):
        # a run under a different first-level segment ("other", not
        # "test") and a run missing the required "one" suffix entirely
        # (2-level, "test/x") are both excluded -- only the exact
        # "test/<anything>/one" shape matches.
        base = tmp_path / "alpha"
        matching = _make_run(base / "test" / "x" / "one", "2026-01-01_00-00-00", "match-1", {})
        wrong_prefix = _make_run(base / "other" / "x" / "one", "2026-01-02_00-00-00", "wrong-1", {})
        too_shallow = _make_run(base / "test" / "x", "2026-01-03_00-00-00", "shallow-1", {})
        _write_archive_manifest(
            tmp_path, "alpha", [matching, wrong_prefix, too_shallow]
        )
        results = _finder(
            "$alpha.results.test/:all()/one:last()", str(tmp_path)
        ).query()
        assert results.uuids == ["match-1"]

    def test_no_pointer_gives_every_matching_run_unreduced(self, tmp_path):
        base = tmp_path / "alpha" / "test"
        x1 = _make_run(base / "x" / "one", "2026-01-01_00-00-00", "x-1", {})
        x2 = _make_run(base / "x" / "one", "2026-01-02_00-00-00", "x-2", {})
        _write_archive_manifest(tmp_path, "alpha", [x1, x2])
        results = _finder("$alpha.results.test/:all()/one", str(tmp_path)).query()
        assert set(results.uuids) == {"x-1", "x-2"}

    def test_all_with_an_argument_is_rejected(self, tmp_path):
        base = tmp_path / "alpha" / "test"
        x1 = _make_run(base / "x" / "one", "2026-01-01_00-00-00", "x-1", {})
        _write_archive_manifest(tmp_path, "alpha", [x1])
        with pytest.raises(ReferenceException3):
            _finder(
                '$alpha.results.test/:all("x")/one:last()', str(tmp_path)
            ).query()


class TestRegexPathSegment:
    # ':regex(...)' as a name_one path segment -- added 2026-09-23,
    # closing the deferred-work bucket list gap of the same name.
    # normative_reference_examples.txt's own worked example (corrected
    # 2026-09-23 twice: first to use '/' separators between path
    # segments, matching every other path segment; second to attach
    # ':last()' directly to "EMEA" with no separating '/', matching
    # every other RESULTS worked example's own pointer convention --
    # "$alpha.results.orders/:regex('202[6789]')/EMEA:last()". A '/'
    # before ':last()' would instead put it INTO name_one.path as its
    # own segment rather than the trailing pointer, per compendium
    # 3.9c/3.9d's own "a function following directly after a path
    # separator implies a '*' wildcard" rule -- confirmed unimplemented
    # anywhere in this codebase (David, 2026-09-23) and deliberately
    # NOT built here, see the dedicated bucket-list entry; this test
    # class only covers ':regex()' attached the ordinary way, without
    # relying on that still-open rule. Mechanically the same capability
    # ':name(/pattern/)' already has (matches a TEMPLATE segment by
    # pattern) -- confirmed by direct parsing that the grammar already
    # accepted ':regex(...)' as an ordinary path segment; only the
    # shared _compile_path_pattern() did not yet recognize it. NOT the
    # same as matching a run's own trailing directory name (a separate,
    # still-open question, see the bucket list) -- like ':name("x")', a
    # bare/prefixed ':regex(...)' here matches a TEMPLATE LEVEL, excluded
    # from the run's own trailing name the same way _prefix_segments()
    # always excludes it.
    def test_prefixed_regex_matches_the_template_segment(self, tmp_path):
        base = tmp_path / "alpha" / "orders"
        matching = _make_run(
            base / "2027" / "EMEA", "2026-01-01_00-00-00", "match-1", {}
        )
        also_matching = _make_run(
            base / "2028" / "EMEA", "2026-01-02_00-00-00", "match-2", {}
        )
        non_matching = _make_run(
            base / "1999" / "EMEA", "2026-01-03_00-00-00", "no-match-1", {}
        )
        _write_archive_manifest(
            tmp_path, "alpha", [matching, also_matching, non_matching]
        )
        results = _finder(
            '$alpha.results.orders/:regex("202[6789]")/EMEA:last()', str(tmp_path)
        ).query()
        # both "2027" and "2028" match the pattern, but this is a plain
        # literal/wildcard path (no ':all()'/':groups()' grouping), so
        # every matching version pools together and ':last()' reduces
        # to the single overall latest.
        assert results.uuids == ["match-2"]

    def test_prefixed_regex_with_no_pointer_gives_every_match_unreduced(
        self, tmp_path
    ):
        base = tmp_path / "alpha" / "orders"
        matching = _make_run(
            base / "2027" / "EMEA", "2026-01-01_00-00-00", "match-1", {}
        )
        non_matching = _make_run(
            base / "1999" / "EMEA", "2026-01-02_00-00-00", "no-match-1", {}
        )
        _write_archive_manifest(tmp_path, "alpha", [matching, non_matching])
        results = _finder(
            '$alpha.results.orders/:regex("202[6789]")/EMEA', str(tmp_path)
        ).query()
        assert results.uuids == ["match-1"]

    def test_bare_regex_matches_a_one_level_template(self, tmp_path):
        # consistent with ':name("x")'s own bare/sole-content precedent
        # -- matches a 1-level template value, not a flat/0-level run's
        # own trailing name.
        base = tmp_path / "alpha"
        matching = _make_run(
            base / "2027", "2026-01-01_00-00-00", "match-1", {}
        )
        non_matching = _make_run(
            base / "1999", "2026-01-02_00-00-00", "no-match-1", {}
        )
        _write_archive_manifest(tmp_path, "alpha", [matching, non_matching])
        results = _finder(
            '$alpha.results.:regex("202[6789]"):last()', str(tmp_path)
        ).query()
        assert results.uuids == ["match-1"]

    def test_invalid_pattern_is_rejected_eagerly(self, tmp_path):
        _write_archive_manifest(tmp_path, "alpha", [])
        with pytest.raises(ReferenceException3):
            _finder(
                '$alpha.results.orders/:regex("[unclosed")/EMEA:last()',
                str(tmp_path),
            ).query()


class TestImpliedStar:
    # compendium 3.9c/3.9d -- added 2026-09-24, surfaced while building
    # ':regex()' as a path segment. "A function starting name_one or
    # following directly after a path separator implies a '*' wildcard,"
    # unless it is itself a wildcard, fully occupies a path segment
    # (':name()'/':regex()'/':choice()'/a clock function), or does not
    # operate in a path segment at all (':manifest()'/':home()'/etc).
    # ':last()' is a plain pointer -- none of those exemptions apply, so
    # "beta/:last()" now means the same as "beta/*:last()" -- and, per
    # the SAME degenerate-run_dir-slot reasoning TestAllGrouping's own
    # "beta/:all():last()" already established (':all()'/'*' at the
    # run_dir-adjacent trailing position means zero MORE levels beyond
    # the prefix, not one extra wildcarded template level -- run_dir
    # names never repeat, so there is nothing to group/wildcard by
    # there), that means "the last run directly under beta," pooled
    # across every run at that exact one-level prefix -- fixture mirrors
    # TestAllGrouping.test_prefixed_all_degenerates_to_pooled_result's
    # own shape exactly.
    def test_prefixed_pointer_implies_a_wildcard_segment(self, tmp_path):
        base = tmp_path / "acme"
        run1 = _make_run(base / "beta", "2026-01-01_00-00-00", "beta-1", {})
        run2 = _make_run(base / "beta", "2026-01-02_00-00-00", "beta-2", {})
        other = _make_run(base / "gamma", "2026-01-03_00-00-00", "gamma-1", {})
        _write_archive_manifest(tmp_path, "acme", [run1, run2, other])
        implied = _finder("$acme.results.beta/:last()", str(tmp_path)).query()
        explicit = _finder(
            "$acme.results.beta/*:last()", str(tmp_path)
        ).query()
        assert implied.uuids == explicit.uuids == ["beta-2"]

    def test_prefixed_field_accessor_implies_a_wildcard_segment(self, tmp_path):
        base = tmp_path / "acme"
        run1 = _make_run(base / "beta", "2026-01-01_00-00-00", "beta-1", {})
        _write_archive_manifest(tmp_path, "acme", [run1])
        results = _finder(
            "$acme.results.beta/:uuid()", str(tmp_path)
        ).resolve()
        assert results.results[0].data == "beta-1"

    def test_bare_pointer_is_unaffected_stays_zero_level(self, tmp_path):
        # confirms the normalization does not change the already-settled
        # bare-pointer-alone outcome (see the 2026-09-21 degenerate-
        # grouping fix) -- just reaches the same zero-level result via a
        # more uniform path (a normalized bare '*', not a special case).
        base = tmp_path / "acme"
        flat = _make_run(base, "2026-01-01_00-00-00", "flat-1", {})
        one_level = _make_run(base / "beta", "2026-01-02_00-00-00", "beta-1", {})
        _write_archive_manifest(tmp_path, "acme", [flat, one_level])
        results = _finder("$acme.results.:last()", str(tmp_path)).query()
        assert results.uuids == ["flat-1"]

    def test_home_is_exempt_prefixed_still_raises(self, tmp_path):
        # ':home()' is a zero-level PLACEHOLDER marker, not an ordinary
        # field accessor -- David deliberately rejected "beta/:home()"
        # on UX grounds (see TestHomeAsAZeroLevelSelector), a decision
        # this normalization must not silently resurrect.
        base = tmp_path / "acme"
        beta1 = _make_run(base / "beta", "2026-01-01_00-00-00", "beta-1", {})
        _write_archive_manifest(tmp_path, "acme", [beta1])
        with pytest.raises(ReferenceException3):
            _finder("$acme.results.beta/:home()", str(tmp_path)).query()

    def test_all_flatten_groups_are_exempt_unaffected(self, tmp_path):
        # sanity check -- these are wildcards themselves, already
        # excluded by name, confirming the exemption list did not
        # accidentally widen to catch them too.
        base = tmp_path / "acme"
        run1 = _make_run(base / "beta", "2026-01-01_00-00-00", "beta-1", {})
        _write_archive_manifest(tmp_path, "acme", [run1])
        results = _finder("$acme.results.beta/:all():last()", str(tmp_path)).query()
        assert results.uuids == ["beta-1"]

    def test_manifest_is_exempt_prefixed_selects_directly_not_via_a_pool(
        self, tmp_path
    ):
        # ':manifest()' -- added 2026-10-15, David caught this live: per
        # 3.9c's own "doesn't operate in a path segment at all" category,
        # ':manifest()' riding alongside a pointer in a bare/prefixed
        # chain must never be re-routed through the pooled/grouped
        # path-matching implied-'*' exists for -- it always means
        # "whichever run the REST of the chain already selected, give
        # its manifest," not a second thing to match against a
        # wildcarded path. Was previously exempt only by accident (never
        # actually tested against a case where it would matter): two
        # DIFFERENT prefixes ("beta", "gamma") each with their own run,
        # "gamma" chronologically LATEST overall -- if ':manifest()'
        # ever got pooled across both prefixes by a wildcard the way a
        # genuine implied-'*' candidate would, ':last()' would wrongly
        # pick gamma's run instead of staying scoped to "beta" alone.
        base = tmp_path / "acme"
        beta1 = _make_run(base / "beta", "2026-01-01_00-00-00", "beta-1", {})
        gamma1 = _make_run(base / "gamma", "2026-01-02_00-00-00", "gamma-1", {})
        _write_archive_manifest(tmp_path, "acme", [beta1, gamma1])
        results = _finder(
            "$acme.results.beta/:last():manifest()", str(tmp_path)
        ).resolve()
        assert results.results[0].uuid == "beta-1"
        assert results.results[0].data["run_uuid"] == "beta-1"


class TestGroups:
    # ':groups()' -- added 2026-08-12, the any-depth GROUP peer of
    # ':all()' (one-level GROUP)/':flatten()' (any-depth POOL), built
    # alongside FILES' own ':groups()' in the same pass (David: keep
    # functions meaning the same thing across datatypes). Same any-depth
    # candidate set as ':flatten()', but partitioned by _group_key
    # (each run's FULL relative path, not just its last segment -- see
    # that method's own docstring for why: two runs at different depths
    # sharing a common trailing segment, e.g. "beta/x" vs. "gamma/x",
    # must never be conflated into one group).
    def test_groups_reaches_every_depth_independently_no_collisions(
        self, tmp_path
    ):
        base = tmp_path / "alpha"
        flat_run = _make_run(base, "2026-01-01_00-00-00", "flat-uuid", {})
        beta_x_1 = _make_run(base / "beta" / "x", "2026-01-02_00-00-00", "beta-x-1", {})
        beta_x_2 = _make_run(base / "beta" / "x", "2026-01-03_00-00-00", "beta-x-2", {})
        gamma_x = _make_run(base / "gamma" / "x", "2026-01-04_00-00-00", "gamma-x-1", {})
        _write_archive_manifest(
            tmp_path, "alpha", [flat_run, beta_x_1, beta_x_2, gamma_x]
        )
        results = _finder("$alpha.results.:groups():last()", str(tmp_path)).query()
        # three distinct groups: zero-level (flat), "beta/x", "gamma/x" --
        # "beta/x" and "gamma/x" both end in "x" but are NOT conflated.
        assert len(results.results) == 3
        assert set(results.uuids) == {"flat-uuid", "beta-x-2", "gamma-x-1"}

    def test_groups_with_first_gives_each_groups_earliest_at_any_depth(
        self, tmp_path
    ):
        base = tmp_path / "alpha"
        flat_run = _make_run(base, "2026-01-01_00-00-00", "flat-uuid", {})
        beta_x_1 = _make_run(base / "beta" / "x", "2026-01-02_00-00-00", "beta-x-1", {})
        beta_x_2 = _make_run(base / "beta" / "x", "2026-01-03_00-00-00", "beta-x-2", {})
        _write_archive_manifest(tmp_path, "alpha", [flat_run, beta_x_1, beta_x_2])
        results = _finder("$alpha.results.:groups():first()", str(tmp_path)).query()
        assert set(results.uuids) == {"flat-uuid", "beta-x-1"}

    def test_groups_with_no_pointer_is_the_same_as_flatten(self, tmp_path):
        # with no pointer, grouped/pooled candidate sets are identical --
        # same reasoning already documented for ':all()' vs. '*'.
        base = tmp_path / "alpha"
        flat_run = _make_run(base, "2026-01-01_00-00-00", "flat-uuid", {})
        deep_run = _make_run(
            base / "beta" / "x", "2026-01-02_00-00-00", "deep-uuid", {}
        )
        _write_archive_manifest(tmp_path, "alpha", [flat_run, deep_run])
        groups_results = _finder("$alpha.results.:groups()", str(tmp_path)).query()
        flatten_results = _finder("$alpha.results.:flatten()", str(tmp_path)).query()
        assert set(groups_results.uuids) == set(flatten_results.uuids)

    def test_prefixed_groups_reaches_every_depth_beyond_the_prefix(
        self, tmp_path
    ):
        base = tmp_path / "acme"
        beta_only = _make_run(base / "beta", "2026-01-01_00-00-00", "beta-only", {})
        beta_x_1 = _make_run(base / "beta" / "x", "2026-01-02_00-00-00", "beta-x-1", {})
        beta_x_2 = _make_run(base / "beta" / "x", "2026-01-03_00-00-00", "beta-x-2", {})
        other = _make_run(base / "gamma", "2026-01-04_00-00-00", "other", {})
        _write_archive_manifest(
            tmp_path, "acme", [beta_only, beta_x_1, beta_x_2, other]
        )
        results = _finder(
            "$acme.results.beta/:groups():last()", str(tmp_path)
        ).query()
        # zero additional segments beyond "beta/" is its own group too.
        assert set(results.uuids) == {"beta-only", "beta-x-2"}

    def test_bare_groups_rejects_an_argument(self, tmp_path):
        base = tmp_path / "alpha"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1-uuid", {})
        _write_archive_manifest(tmp_path, "alpha", [run1])
        with pytest.raises(ReferenceException3):
            _finder('$alpha.results.:groups("x"):last()', str(tmp_path)).query()

    def test_prefixed_groups_rejects_an_argument(self, tmp_path):
        base = tmp_path / "acme"
        run1 = _make_run(base / "beta", "2026-01-01_00-00-00", "run1-uuid", {})
        _write_archive_manifest(tmp_path, "acme", [run1])
        with pytest.raises(ReferenceException3):
            _finder(
                '$acme.results.beta/:groups("x"):last()', str(tmp_path)
            ).query()

    def test_groups_combined_with_all_is_rejected(self, tmp_path):
        base = tmp_path / "alpha"
        run1 = _make_run(base / "zero", "2026-01-01_00-00-00", "zero-1", {})
        _write_archive_manifest(tmp_path, "alpha", [run1])
        with pytest.raises(ReferenceException3):
            _finder("$alpha.results.:all():groups():last()", str(tmp_path)).query()

    def test_groups_combined_with_flatten_is_rejected(self, tmp_path):
        base = tmp_path / "alpha"
        run1 = _make_run(base / "zero", "2026-01-01_00-00-00", "zero-1", {})
        _write_archive_manifest(tmp_path, "alpha", [run1])
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.results.:flatten():groups():last()", str(tmp_path)
            ).query()

    def test_groups_combined_with_manifest_is_not_yet_supported(self, tmp_path):
        base = tmp_path / "alpha"
        run1 = _make_run(base / "zero", "2026-01-01_00-00-00", "zero-1", {})
        _write_archive_manifest(tmp_path, "alpha", [run1])
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.results.:groups():last():manifest()", str(tmp_path)
            ).query()


class TestRunLevelRange:
    # ':from()'/':to()' as a run-level index range -- added 2026-08-13,
    # David: "our version of BETWEEN in SQL or range() in Python," built
    # together since both slice the same already-ordered candidate list
    # (no implementation reason to split them). ':to()' is INCLUSIVE of
    # its own position. Index-mode only for this pass -- date-mode
    # (":from(:date(...))"/":from(:yesterday())") is deliberately
    # deferred, needs :date()/:yesterday() first.
    @pytest.fixture
    def five_runs(self, tmp_path):
        base = tmp_path / "acme" / "customers"
        runs = [
            _make_run(base, f"2026-01-0{i}_00-00-00", f"run-{i}", {})
            for i in range(1, 6)
        ]
        _write_archive_manifest(tmp_path, "acme", runs)
        return str(tmp_path)

    def test_from_index_negative_gives_the_last_n(self, five_runs):
        results = _finder(
            "$acme.results.customers:from(:index(-3))", five_runs
        ).query()
        assert results.uuids == ["run-3", "run-4", "run-5"]

    def test_from_bare_int_is_identical_to_from_index(self, five_runs):
        # doc's own NOTES block: ":from(:index(-3))" is identical to
        # ":from(-3))" -- both legal, both must give the same answer.
        via_index = _finder(
            "$acme.results.customers:from(:index(-3))", five_runs
        ).query()
        via_int = _finder("$acme.results.customers:from(-3)", five_runs).query()
        assert via_index.uuids == via_int.uuids == ["run-3", "run-4", "run-5"]

    def test_from_and_to_together_is_an_inclusive_range(self, five_runs):
        results = _finder(
            "$acme.results.customers:from(1):to(3)", five_runs
        ).query()
        assert results.uuids == ["run-2", "run-3", "run-4"]

    def test_to_alone_is_open_at_the_start(self, five_runs):
        results = _finder("$acme.results.customers:to(1)", five_runs).query()
        assert results.uuids == ["run-1", "run-2"]

    def test_to_with_negative_one_reaches_the_true_end(self, five_runs):
        # the one edge case _apply_range's own docstring calls out: a
        # naive "end + 1" would wrap -1 to 0 and give an empty slice.
        results = _finder(
            "$acme.results.customers:from(1):to(-1)", five_runs
        ).query()
        assert results.uuids == ["run-2", "run-3", "run-4", "run-5"]

    def test_a_pointer_reduces_the_slice_not_the_full_candidate_set(
        self, five_runs
    ):
        results = _finder(
            "$acme.results.customers:from(-3):last()", five_runs
        ).query()
        assert results.uuids == ["run-5"]

    def test_from_rejects_a_malformed_date_string_argument(self, five_runs):
        # settled 2026-08-13: a bare str arg is now date-mode's leaf
        # shape (":from('2025-01-01')" == ":from(:date('2025-01-01'))"),
        # not simply rejected -- but its CONTENT must be a real calendar
        # date, see TestRunLevelDateRange for the date-mode cases
        # themselves.
        with pytest.raises(ReferenceException3):
            _finder('$acme.results.customers:from("x")', five_runs).query()

    def test_from_rejects_an_unrelated_nested_function_argument(
        self, five_runs
    ):
        # ':uuid()' is a real, registered function, so this parses fine
        # -- but it is neither Index3 nor Date3, so ARG_TYPES rejects it.
        with pytest.raises(ReferenceException3):
            _finder("$acme.results.customers:from(:uuid())", five_runs).query()

    def test_from_combined_with_all_grouping_is_not_yet_supported(
        self, tmp_path
    ):
        # REVISED 2026-09-21: uses its own zero-level fixture -- bare
        # ':all()' no longer matches five_runs' 1-level "customers/"
        # runs at all (per the 4.2b degenerate-grouping fix), which
        # would leave group_key_for empty/falsy and never trigger this
        # exception in the first place.
        base = tmp_path / "acme"
        runs = [
            _make_run(base, f"2026-01-0{i}_00-00-00", f"run-{i}", {})
            for i in range(1, 6)
        ]
        _write_archive_manifest(tmp_path, "acme", runs)
        with pytest.raises(ReferenceException3):
            _finder(
                "$acme.results.:all():from(1):last()", str(tmp_path)
            ).query()

    def test_from_with_manifest_and_more_than_one_run_requires_a_pointer(
        self, five_runs
    ):
        # query() itself succeeds (moved 2026-08-26, see the ":path()"
        # retirement/Rule 1 bucket-list entry) -- only resolve() raises,
        # once something actually tries to read the content.
        finder = _finder("$acme.results.customers:from(-3):manifest()", five_runs)
        assert len(finder.query()) > 1
        with pytest.raises(ReferenceException3):
            finder.resolve()


class TestRunLevelDateRange:
    # ':from()'/':to()' date-mode -- added 2026-08-13, David: "arrival
    # and run order is even more important than indexing." A FILTER by
    # each run's own arrival date (parsed from its directory name's own
    # timestamp prefix), not a positional slice -- ':to()' is INCLUSIVE
    # of its own date, same convention as index-mode. A bare date string
    # (no ':date(...)' wrapper) must give identical results to the
    # wrapped form, same "wrapper optional but must be possible" pattern
    # already established for index-mode.
    @pytest.fixture
    def dated_runs(self, tmp_path):
        base = tmp_path / "acme" / "customers"
        runs = {
            "run-before": _make_run(
                base, "2024-12-31_00-00-00", "run-before", {}
            ),
            "run-jan1": _make_run(base, "2025-01-01_00-00-00", "run-jan1", {}),
            "run-jan15": _make_run(
                base, "2025-01-15_00-00-00", "run-jan15", {}
            ),
            "run-feb1": _make_run(base, "2025-02-01_00-00-00", "run-feb1", {}),
        }
        _write_archive_manifest(tmp_path, "acme", list(runs.values()))
        return str(tmp_path)

    def test_from_date_is_inclusive_and_open_ended(self, dated_runs):
        results = _finder(
            '$acme.results.customers:from(:date("2025-01-01"))', dated_runs
        ).query()
        assert set(results.uuids) == {"run-jan1", "run-jan15", "run-feb1"}

    def test_to_date_is_inclusive_and_open_started(self, dated_runs):
        results = _finder(
            '$acme.results.customers:to(:date("2025-01-15"))', dated_runs
        ).query()
        assert set(results.uuids) == {"run-before", "run-jan1", "run-jan15"}

    def test_from_and_to_date_together_is_an_inclusive_range(self, dated_runs):
        results = _finder(
            '$acme.results.customers:from(:date("2025-01-01")):to(:date("2025-01-15"))',
            dated_runs,
        ).query()
        assert set(results.uuids) == {"run-jan1", "run-jan15"}

    def test_bare_date_string_is_identical_to_wrapped(self, dated_runs):
        wrapped = _finder(
            '$acme.results.customers:from(:date("2025-01-01"))', dated_runs
        ).query()
        bare = _finder(
            '$acme.results.customers:from("2025-01-01")', dated_runs
        ).query()
        assert set(wrapped.uuids) == set(bare.uuids) == {
            "run-jan1",
            "run-jan15",
            "run-feb1",
        }

    def test_a_pointer_reduces_the_dated_range_not_the_full_set(
        self, dated_runs
    ):
        results = _finder(
            '$acme.results.customers:from(:date("2025-01-01")):last()',
            dated_runs,
        ).query()
        assert results.uuids == ["run-feb1"]

    def test_malformed_date_raises_clearly(self, dated_runs):
        with pytest.raises(ReferenceException3):
            _finder(
                '$acme.results.customers:from("not-a-date")', dated_runs
            ).query()

    def test_mixing_index_and_date_modes_is_rejected(self, dated_runs):
        with pytest.raises(ReferenceException3):
            _finder(
                '$acme.results.customers:from(1):to(:date("2025-01-01"))',
                dated_runs,
            ).query()


class TestTimeWindowFunctionAnchors:
    # Gap 2 of compendium 6.27/TimeWindowFunction3 (added 2026-10-17) --
    # a time-component function (":year()"/":yesterday()"/etc) nested
    # as :from()'s/:to()'s/:before()'s/:after()'s own argument, not
    # just the previously-only-supported literal ":date(...)". Pins
    # DateUtility's own "now" to a known, fixed calendar date (via
    # OFFSET_DAYS, computed relative to the real moment the test
    # actually runs) so every assertion is deterministic regardless of
    # when the suite runs -- the clock functions themselves, and
    # ResultsReferenceFinder3's own date-range filtering, both read
    # DateUtility.now() exclusively (confirmed against the real code,
    # not assumed).
    @pytest.fixture
    def pinned_now(self):
        from datetime import date

        from csvpath.util.date_util import DateUtility as daut

        target = date(2026, 6, 15)  # safely mid-month, mid-year
        real_now = daut.now()
        daut.OFFSET_DAYS = (target - real_now.date()).days
        daut.OFFSET_MONTHS = 0
        daut.OFFSET_YEARS = 0
        try:
            yield target
        finally:
            daut.OFFSET_DAYS = 0
            daut.OFFSET_MONTHS = 0
            daut.OFFSET_YEARS = 0

    @pytest.fixture
    def dated_runs(self, tmp_path, pinned_now):
        # "now" is pinned to 2026-06-15 -- these runs straddle every
        # boundary this class's tests check (prior year, this year's
        # own first day, mid-year, yesterday, today).
        base = tmp_path / "acme" / "customers"
        runs = {
            "run-2025": _make_run(base, "2025-12-31_00-00-00", "run-2025", {}),
            "run-jan1": _make_run(base, "2026-01-01_00-00-00", "run-jan1", {}),
            "run-may1": _make_run(base, "2026-05-01_00-00-00", "run-may1", {}),
            "run-jun1": _make_run(base, "2026-06-01_00-00-00", "run-jun1", {}),
            "run-yesterday": _make_run(
                base, "2026-06-14_00-00-00", "run-yesterday", {}
            ),
            "run-today": _make_run(base, "2026-06-15_00-00-00", "run-today", {}),
        }
        _write_archive_manifest(tmp_path, "acme", list(runs.values()))
        return str(tmp_path)

    def test_from_year_keeps_this_years_runs_onward(self, dated_runs):
        # :year() -> [2026-01-01, 2026-12-31] -- :from() uses its start.
        results = _finder(
            "$acme.results.customers:from(:year())", dated_runs
        ).query()
        assert set(results.uuids) == {
            "run-jan1",
            "run-may1",
            "run-jun1",
            "run-yesterday",
            "run-today",
        }

    def test_to_month_keeps_up_through_this_months_own_end(self, dated_runs):
        # :month() -> [2026-06-01, 2026-06-30] -- :to() uses its end,
        # so everything through the end of June is kept (not just up
        # to June 1st).
        results = _finder(
            "$acme.results.customers:to(:month())", dated_runs
        ).query()
        assert set(results.uuids) == {
            "run-2025",
            "run-jan1",
            "run-may1",
            "run-jun1",
            "run-yesterday",
            "run-today",
        }

    def test_before_today_excludes_the_whole_of_today(self, dated_runs):
        # :before(:today()) -> exclusive upper, excludes the WHOLE
        # named day, not just one instant within it -- same "excludes
        # the whole period it names" rule the already-shipped
        # :before(:date(...)) shape uses.
        results = _finder(
            "$acme.results.customers:before(:today())", dated_runs
        ).query()
        assert set(results.uuids) == {
            "run-2025",
            "run-jan1",
            "run-may1",
            "run-jun1",
            "run-yesterday",
        }

    def test_after_yesterday_excludes_yesterday_and_earlier(self, dated_runs):
        # :after(:yesterday()) -> exclusive lower, excludes the whole
        # of yesterday (and earlier) -- only strictly later survives.
        results = _finder(
            "$acme.results.customers:after(:yesterday())", dated_runs
        ).query()
        assert set(results.uuids) == {"run-today"}

    def test_compendium_6_27f_flagship_example(self, dated_runs):
        # compendium 6.27f's own confirmed worked example:
        # ":from(:yesterday()):before(:today())" == "yesterday, the
        # whole day" -- the one example this entire mechanism was
        # designed against.
        results = _finder(
            "$acme.results.customers:from(:yesterday()):before(:today())",
            dated_runs,
        ).query()
        assert set(results.uuids) == {"run-yesterday"}

    def test_mixing_index_and_time_window_modes_is_rejected(self, dated_runs):
        with pytest.raises(ReferenceException3):
            _finder(
                "$acme.results.customers:from(1):to(:year())", dated_runs
            ).query()

    def test_bare_yesterday_is_a_range_matching_6_27f_exactly(self, dated_runs):
        # Gap 1 of compendium 6.27/TimeWindowFunction3, added
        # 2026-10-17 -- a BARE time-component function riding in the
        # chain (no explicit :from()/:to()), the compendium's own
        # flagship worked example (6.27e's first bullet, 6.27f's own
        # confirmed answer: "every file home with changes within
        # yesterday's window").
        results = _finder(
            "$acme.results.customers:yesterday()", dated_runs
        ).query()
        assert set(results.uuids) == {"run-yesterday"}

    def test_bare_today_is_inclusive_both_ends(self, dated_runs):
        results = _finder(
            "$acme.results.customers:today()", dated_runs
        ).query()
        assert set(results.uuids) == {"run-today"}

    def test_bare_year_pools_the_whole_year(self, dated_runs):
        results = _finder(
            "$acme.results.customers:year()", dated_runs
        ).query()
        assert set(results.uuids) == {
            "run-jan1",
            "run-may1",
            "run-jun1",
            "run-yesterday",
            "run-today",
        }

    def test_bare_time_window_as_context_for_a_pointer(self, dated_runs):
        # 6.27e's second bullet -- "use as a context for a pointer":
        # ":yesterday():last()" finds the last registration within
        # yesterday's own window (here, the only one).
        results = _finder(
            "$acme.results.customers:yesterday():last()", dated_runs
        ).query()
        assert results.uuids == ["run-yesterday"]

    def test_bare_time_window_combined_with_explicit_range_is_rejected(
        self, dated_runs
    ):
        with pytest.raises(ReferenceException3):
            _finder(
                "$acme.results.customers:yesterday():from(1)", dated_runs
            ).query()

    def test_two_bare_time_window_functions_is_rejected(self, dated_runs):
        with pytest.raises(ReferenceException3):
            _finder(
                "$acme.results.customers:yesterday():today()", dated_runs
            ).query()


class TestRunLevelDirectionFunctions:
    # ':before()'/':after()' as a run-level range -- compendium 6.28/
    # 6.28b/6.28c, built 2026-10-16, the EXCLUSIVE siblings of ':to()'/
    # ':from()'. Reuses TestRunLevelRange's own five_runs fixture
    # (run-1..run-5, positions 0-4) and TestRunLevelDateRange's own
    # dated_runs fixture.
    @pytest.fixture
    def five_runs(self, tmp_path):
        base = tmp_path / "acme" / "customers"
        runs = [
            _make_run(base, f"2026-01-0{i}_00-00-00", f"run-{i}", {})
            for i in range(1, 6)
        ]
        _write_archive_manifest(tmp_path, "acme", runs)
        return str(tmp_path)

    @pytest.fixture
    def dated_runs(self, tmp_path):
        base = tmp_path / "acme" / "customers"
        runs = {
            "run-before": _make_run(base, "2024-12-31_00-00-00", "run-before", {}),
            "run-jan1": _make_run(base, "2025-01-01_00-00-00", "run-jan1", {}),
            "run-jan15": _make_run(base, "2025-01-15_00-00-00", "run-jan15", {}),
            "run-feb1": _make_run(base, "2025-02-01_00-00-00", "run-feb1", {}),
        }
        _write_archive_manifest(tmp_path, "acme", list(runs.values()))
        return str(tmp_path)

    def test_after_excludes_its_own_position(self, five_runs):
        results = _finder("$acme.results.customers:after(1)", five_runs).query()
        assert results.uuids == ["run-3", "run-4", "run-5"]

    def test_before_excludes_its_own_position(self, five_runs):
        results = _finder("$acme.results.customers:before(3)", five_runs).query()
        assert results.uuids == ["run-1", "run-2", "run-3"]

    def test_after_and_before_together_is_an_exclusive_range(self, five_runs):
        results = _finder(
            "$acme.results.customers:after(1):before(4)", five_runs
        ).query()
        assert results.uuids == ["run-3", "run-4"]

    def test_after_date_excludes_its_own_date(self, dated_runs):
        results = _finder(
            '$acme.results.customers:after(:date("2025-01-01"))', dated_runs
        ).query()
        assert set(results.uuids) == {"run-jan15", "run-feb1"}

    def test_before_date_excludes_its_own_date(self, dated_runs):
        results = _finder(
            '$acme.results.customers:before(:date("2025-01-15"))', dated_runs
        ).query()
        assert set(results.uuids) == {"run-before", "run-jan1"}

    def test_combining_two_lower_bounds_is_illegal(self, five_runs):
        with pytest.raises(ReferenceException3):
            _finder("$acme.results.customers:from(1):after(2)", five_runs).query()

    def test_combining_two_upper_bounds_is_illegal(self, five_runs):
        with pytest.raises(ReferenceException3):
            _finder("$acme.results.customers:to(3):before(1)", five_runs).query()

    def test_gt_and_lt_aliases_work(self, five_runs):
        results = _finder("$acme.results.customers:gt(1):lt(4)", five_runs).query()
        assert results.uuids == ["run-3", "run-4"]


class TestStatementLevelRange:
    # ':from()'/':to()' as a name_three statement-level range -- added
    # 2026-08-13. David: ":from(:index(2)):unmatched() should definitely
    # not work" -- a range is "more than one entity" the same way
    # ':all()' already is, so it gets the same restriction combined with
    # a content accessor -- but count-DEPENDENT (checked per run), not
    # ':all()'s own blanket rejection, mirroring the run-level "more
    # than one candidate" check this file already uses elsewhere.
    #
    # Fixture deliberately writes instances in a NON-declaration-order
    # sequence (both dict order and directory-write order scrambled) --
    # this exercises the 2026-08-13 ordering fix to
    # _list_instance_identities (it used to trust raw filesystem
    # listdir() order, which is NOT declaration order; now sorts by
    # each instance's own "instance_index", confirmed via
    # csvpaths.py -> Result -> ResultRegistrar -> ResultMetadata to be
    # the real, written declaration-order field). Without that fix this
    # whole class would be testing filesystem-dependent noise instead
    # of real statement position.
    @pytest.fixture
    def one_run_five_statements(self, tmp_path):
        base = tmp_path / "acme" / "customers" / "2025"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        # identity -> (uuid, instance_index); written out of order on
        # purpose.
        scrambled = {
            "four": ("f-uuid", 4),
            "zero": ("z-uuid", 0),
            "two": ("t-uuid", 2),
            "one": ("o-uuid", 1),
            "three": ("th-uuid", 3),
        }
        for identity, (uuid, idx) in scrambled.items():
            _write_json(
                run_dir / identity / "manifest.json",
                {"uuid": uuid, "instance_index": idx},
            )
        _write_archive_manifest(tmp_path, "acme", [str(run_dir)])
        return str(tmp_path)

    def test_from_gives_statements_in_true_declaration_order(
        self, one_run_five_statements
    ):
        results = _finder(
            "$acme.results.customers/2025:first().:from(2)",
            one_run_five_statements,
        ).query()
        assert results.uuids == ["t-uuid", "th-uuid", "f-uuid"]

    def test_from_and_to_together_is_an_inclusive_range(
        self, one_run_five_statements
    ):
        results = _finder(
            "$acme.results.customers/2025:first().:from(1):to(3)",
            one_run_five_statements,
        ).query()
        assert results.uuids == ["o-uuid", "t-uuid", "th-uuid"]

    def test_open_ended_range_combined_with_content_accessor_raises(
        self, one_run_five_statements
    ):
        # the exact case David flagged: ":from(2):unmatched()" matches
        # 3 statements here, "more than one entity" -- must raise, the
        # doc's own original example describing this as working was
        # wrong.
        finder = _finder(
            "$acme.results.customers/2025:first().:from(2):unmatched()",
            one_run_five_statements,
        )
        with pytest.raises(ReferenceException3):
            finder.resolve()

    def test_range_narrowed_to_exactly_one_with_accessor_is_fine(
        self, one_run_five_statements
    ):
        # a degenerate single-item range is fine with a content
        # accessor, same as a pointer narrowing a run-list to one
        # already is -- count-dependent, not a blanket rejection.
        results = _finder(
            "$acme.results.customers/2025:first().:from(2):to(2):unmatched()",
            one_run_five_statements,
        ).resolve()
        assert results.results[0].data is None  # never written, not an error

    def test_range_combined_with_a_field_accessor_is_poolable(
        self, one_run_five_statements
    ):
        # field accessors are exempt from the single-entity rule, same
        # exemption ':all()' + a field accessor already gets.
        results = _finder(
            "$acme.results.customers/2025:first().:from(2):uuid()",
            one_run_five_statements,
        ).resolve()
        assert [r.data for r in results.results] == ["t-uuid", "th-uuid", "f-uuid"]

    def test_range_alone_with_no_accessor_lists_unreduced(
        self, one_run_five_statements
    ):
        results = _finder(
            "$acme.results.customers/2025:first().:from(2)",
            one_run_five_statements,
        ).query()
        assert len(results.results) == 3

    def test_range_cannot_combine_with_a_literal_identity(
        self, one_run_five_statements
    ):
        with pytest.raises(ReferenceException3):
            _finder(
                "$acme.results.customers/2025:first().two:from(2)",
                one_run_five_statements,
            ).query()

    def test_range_cannot_combine_with_all(self, one_run_five_statements):
        with pytest.raises(ReferenceException3):
            _finder(
                "$acme.results.customers/2025:first().:all():from(2)",
                one_run_five_statements,
            ).query()

    def test_after_excludes_its_own_position(self, one_run_five_statements):
        # ':after()' as a name_three statement-level range -- compendium
        # 6.28, built 2026-10-16. identities zero..four, instance_index
        # 0-4 (see this class's own scrambled fixture comment).
        results = _finder(
            "$acme.results.customers/2025:first().:after(1)",
            one_run_five_statements,
        ).query()
        assert results.uuids == ["t-uuid", "th-uuid", "f-uuid"]

    def test_before_excludes_its_own_position(self, one_run_five_statements):
        results = _finder(
            "$acme.results.customers/2025:first().:before(3)",
            one_run_five_statements,
        ).query()
        assert results.uuids == ["z-uuid", "o-uuid", "t-uuid"]


class TestHomeAsAZeroLevelSelector:
    # settled 2026-08-11: bare ':home()' (David's own framing --
    # "everything that has its home here") fills the one real gap left
    # in the depth model -- there was no way to ask for "every zero-
    # level run, unreduced" (bare pointer always reduces to one, ':all()'
    # is one-level not zero, ':flatten()' is any depth not zero). Needed
    # no code change at all -- ':home()' is VALUE-role, never a pointer,
    # so when it is the only function in the bare chain, nothing reduces
    # the candidate set and every zero-level run comes back unreduced
    # for free.
    #
    # settled 2026-08-12: there is NO prefixed equivalent
    # ("beta/:home()") -- a plain literal prefix segment with nothing
    # trailing already means "every run under this exact prefix,
    # unreduced" (confirmed identical results to a prefixed ':home()'
    # in every case tested), so a prefixed ':home()' would just be a
    # second, more confusing spelling of something that already has
    # one. ':home()' is only load-bearing at the bare/root position,
    # where the grammar has no other way to say "zero segments."
    def test_bare_home_lists_every_zero_level_run_unreduced(self, tmp_path):
        base = tmp_path / "alpha"
        flat1 = _make_run(base, "2026-01-01_00-00-00", "flat-1", {})
        flat2 = _make_run(base, "2026-01-02_00-00-00", "flat-2", {})
        one_level = _make_run(base / "zero", "2026-01-03_00-00-00", "one-level", {})
        _write_archive_manifest(tmp_path, "alpha", [flat1, flat2, one_level])
        results = _finder("$alpha.results.:home()", str(tmp_path)).query()
        assert set(results.uuids) == {"flat-1", "flat-2"}

    def test_home_then_pointer_reduces_to_one(self, tmp_path):
        base = tmp_path / "alpha"
        flat1 = _make_run(base, "2026-01-01_00-00-00", "flat-1", {})
        flat2 = _make_run(base, "2026-01-02_00-00-00", "flat-2", {})
        _write_archive_manifest(tmp_path, "alpha", [flat1, flat2])
        results = _finder("$alpha.results.:home():last()", str(tmp_path)).query()
        assert results.uuids == ["flat-2"]

    def test_pointer_then_home_gives_the_same_result_either_order(
        self, tmp_path
    ):
        # order-independence: ':home()' is not a pointer, so its own
        # presence never competes with a real pointer for which one
        # "wins" -- both orders mean the same thing.
        base = tmp_path / "alpha"
        flat1 = _make_run(base, "2026-01-01_00-00-00", "flat-1", {})
        flat2 = _make_run(base, "2026-01-02_00-00-00", "flat-2", {})
        _write_archive_manifest(tmp_path, "alpha", [flat1, flat2])
        home_then_pointer = _finder(
            "$alpha.results.:home():last()", str(tmp_path)
        ).query()
        pointer_then_home = _finder(
            "$alpha.results.:last():home()", str(tmp_path)
        ).query()
        assert home_then_pointer.uuids == pointer_then_home.uuids == ["flat-2"]

    def test_bare_home_rejects_an_argument(self, tmp_path):
        base = tmp_path / "alpha"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1", {})
        _write_archive_manifest(tmp_path, "alpha", [run1])
        with pytest.raises(ReferenceException3):
            _finder('$alpha.results.:home("x")', str(tmp_path)).query()

    def test_prefixed_home_is_not_a_thing_use_the_literal_prefix_alone(
        self, tmp_path
    ):
        # a literal prefix segment with nothing trailing already means
        # "every run under this exact prefix, unreduced" -- confirmed
        # this gives identical results to a would-be prefixed ':home()'
        # in every case tested, so ':home()' was never wired up as a
        # legal non-first path segment. This locks in that "beta/
        # :home()" is simply unsupported syntax, not a silent no-op.
        base = tmp_path / "acme"
        beta1 = _make_run(base / "beta", "2026-01-01_00-00-00", "beta-1", {})
        beta2 = _make_run(base / "beta", "2026-01-02_00-00-00", "beta-2", {})
        _write_archive_manifest(tmp_path, "acme", [beta1, beta2])
        plain_prefix = _finder("$acme.results.beta", str(tmp_path)).query()
        assert set(plain_prefix.uuids) == {"beta-1", "beta-2"}
        with pytest.raises(ReferenceException3):
            _finder("$acme.results.beta/:home()", str(tmp_path)).query()


class TestDiscoveryFromArchiveManifest:
    def test_dedupes_multiple_entries_sharing_one_run_home(self, tmp_path):
        # a real run_home is written once per csvpath-statement
        # execution -- several entries in the archive manifest can share
        # the same run_home for one run with multiple statements. Uses
        # ':flatten()' rather than ':all()' -- run1 here is flat/zero-
        # level, and this test is about discovery/dedup, not depth
        # semantics.
        base = tmp_path / "acme"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1-uuid", {})
        _write_archive_manifest(tmp_path, "acme", [run1, run1, run1])
        results = _finder("$acme.results.:flatten()", str(tmp_path)).query()
        assert results.uuids == ["run1-uuid"]

    def test_stale_entry_for_a_deleted_run_is_dropped(self, tmp_path):
        base = tmp_path / "acme"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1-uuid", {})
        deleted_run_home = str(base / "2025-06-06_00-00-00")
        _write_archive_manifest(tmp_path, "acme", [run1, deleted_run_home])
        results = _finder("$acme.results.:flatten()", str(tmp_path)).query()
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
        results = _finder("$acme.results.:flatten()", str(tmp_path)).query()
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
            pathu.resep(
                f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00/company_names"
            )
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

    def test_manifest_beside_a_pointer_in_the_bare_shape(self, tmp_path):
        # a bare pointer now means zero-level only (settled 2026-08-10)
        # -- acme_archive's runs are nested under "customers/2025", so
        # this needs its own flat fixture rather than reusing acme_archive
        # the way the literal-path sibling test above does.
        base = tmp_path / "flatgroup"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1-uuid", {})
        run2 = _make_run(base, "2026-01-02_00-00-00", "run2-uuid", {})
        _write_archive_manifest(tmp_path, "flatgroup", [run1, run2])
        results = _finder(
            "$flatgroup.results.:last():manifest()", str(tmp_path)
        ).resolve()
        assert results.results[0].data == {"run_uuid": "run2-uuid"}

    def test_manifest_with_no_pointer_and_more_than_one_matching_run_raises(
        self, acme_archive
    ):
        # "customers/2025" matches both run1 and run2. Resolving full
        # manifest content always touches exactly one entity (settled
        # 2026-08-07), so this is illegal -- a pointer is required to
        # pick one run. query() itself succeeds (moved 2026-08-26, see
        # the ":path()" retirement/Rule 1 bucket-list entry) -- only
        # resolve() raises, once something actually tries to read the
        # content.
        finder = _finder("$acme.results.customers/2025:manifest()", acme_archive)
        assert len(finder.query()) > 1
        with pytest.raises(ReferenceException3):
            finder.resolve()

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
        base = tmp_path / "widgets"  # direct child of the groups own home
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

    def test_run_home_at_run_scope_reads_run_home(self, tmp_path):
        # :home() split 2026-08-26 -- run scope's own field-read job is
        # now :run_home() (:home() itself keeps only the zero-level
        # placeholder role). Confirmed against results_registrar.py that
        # "run_home" is a real, written field, not just documented.
        base = tmp_path / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(
            run_dir / "manifest.json",
            {"run_uuid": "run1-uuid", "run_home": str(run_dir)},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])
        results = _finder(
            "$widgets.results.:first():run_home()", str(tmp_path)
        ).resolve()
        assert results.results[0].data == str(run_dir)

    def test_instance_home_at_instance_scope_reads_instance_home(self, tmp_path):
        # :home() split 2026-08-26 -- instance scope's own field-read
        # job is now :instance_home(). Confirmed against
        # result_registrar.py that "instance_home" is a real field.
        base = tmp_path / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        instance_dir = run_dir / "company_names"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        _write_json(
            instance_dir / "manifest.json",
            {"uuid": "inst1-uuid", "instance_home": str(instance_dir)},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])
        results = _finder(
            "$widgets.results.:first().company_names:instance_home()",
            str(tmp_path),
        ).resolve()
        assert results.results[0].data == str(instance_dir)

    def test_uuid_at_instance_scope(self, acme_archive):
        results = _finder(
            "$acme.results.customers/2025:first().company_names:uuid()",
            acme_archive,
        ).resolve()
        assert results.results[0].data == "inst1-uuid"

    def test_uuid_at_run_scope_mirrors_run_uuid_not_the_deprecated_field(
        self, acme_archive
    ):
        # settled 2026-08-11: :uuid()'s KEY reads "run_uuid" at RESULTS
        # run scope, not the run's own bare "uuid" field (deprecated,
        # see #225-adjacent findings) -- this must give the same value
        # :run_uuid() gives, not None and not the deprecated field.
        results = _finder(
            "$acme.results.customers/2025:first():uuid()", acme_archive
        ).resolve()
        assert results.results[0].data == "run1-uuid"

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
        base = tmp_path / "widgets"  # direct child of the groups own home
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
        # status/method/host/username/time_completed/manifest_path/
        # named_paths_name -- run scope only, confirmed real keys in
        # results_registrar.py.
        base = tmp_path / "widgets"  # direct child of the groups own home
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
        assert resolve("host") == "box1"
        assert resolve("username") == "auser"
        assert resolve("time_completed") == "2026-08-09T00:00:00"
        assert resolve("manifest_path") == str(run_dir / "manifest.json")
        assert resolve("named_paths_name") == "widgets"

    def test_completed_and_files_complete_scope_dependent_keys(self, tmp_path):
        base = tmp_path / "widgets"  # direct child of the groups own home
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
        base = tmp_path / "widgets"  # direct child of the groups own home
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
        base = tmp_path / "widgets"  # direct child of the groups own home
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

    def test_named_results_name_shared_key_both_scopes(self, tmp_path):
        # same literal key ("named_results_name") at both scopes -- see
        # run_uuid_3.py's own docstring for why a shared value still
        # needs two KEY entries, one per scope the finder dispatches on.
        base = tmp_path / "widgets"  # direct child of the group's own home
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(
            run_dir / "manifest.json",
            {"run_uuid": "run-uuid", "named_results_name": "widgets"},
        )
        _write_json(
            run_dir / "company_names" / "manifest.json",
            {"uuid": "inst-uuid", "named_results_name": "widgets"},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        run_name = _finder(
            "$widgets.results.:first():named_results_name()", str(tmp_path)
        ).resolve()
        assert run_name.results[0].data == "widgets"

        instance_name = _finder(
            "$widgets.results.:first().company_names:named_results_name()",
            str(tmp_path),
        ).resolve()
        assert instance_name.results[0].data == "widgets"

    def test_time_at_run_and_instance_scope(self, tmp_path):
        # same literal key ("time") at both scopes -- confirmed real,
        # written fields in results_registrar.py/result_registrar.py:
        # run start time, and this one statement's own start time.
        base = tmp_path / "widgets"  # direct child of the group's own home
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(
            run_dir / "manifest.json",
            {"run_uuid": "run-uuid", "time": "2026-01-01T00:00:00+00:00"},
        )
        _write_json(
            run_dir / "company_names" / "manifest.json",
            {"uuid": "inst-uuid", "time": "2026-01-01T00:00:05+00:00"},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        run_time = _finder(
            "$widgets.results.:first():time()", str(tmp_path)
        ).resolve()
        assert run_time.results[0].data == "2026-01-01T00:00:00+00:00"

        instance_time = _finder(
            "$widgets.results.:first().company_names:time()", str(tmp_path)
        ).resolve()
        assert instance_time.results[0].data == "2026-01-01T00:00:05+00:00"

    def test_run_scope_fields_added_2026_08_25(self, tmp_path):
        base = tmp_path / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(
            run_dir / "manifest.json",
            {
                "run_uuid": "run1-uuid",
                "error_count": 3,
                "named_paths_uuid": "paths-uuid-1",
                "named_paths_fingerprint": "cafef00d",
                "named_file_uuid": "file-uuid-1",
                "named_file_path": "/inputs/named_files/widgets/data.csv",
                "named_file_size": 1024,
                "named_file_last_change": "2026-01-01T00:00:00+00:00",
                "named_file_fingerprint": "deadbeef",
            },
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        def _val(fn):
            return _finder(
                f"$widgets.results.:first():{fn}()", str(tmp_path)
            ).resolve().results[0].data

        assert _val("error_count") == 3
        assert _val("named_paths_uuid") == "paths-uuid-1"
        assert _val("named_paths_fingerprint") == "cafef00d"
        assert _val("named_file_uuid") == "file-uuid-1"
        assert _val("named_file_path") == "/inputs/named_files/widgets/data.csv"
        assert _val("named_file_size") == 1024
        assert _val("named_file_last_change") == "2026-01-01T00:00:00+00:00"
        assert _val("named_file_fingerprint") == "deadbeef"

    def test_instance_scope_fields_added_2026_08_25(self, tmp_path):
        base = tmp_path / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        _write_json(
            run_dir / "company_names" / "manifest.json",
            {
                "uuid": "inst1-uuid",
                "run": "2026-01-01_00-00-00",
                "instance_index": 2,
                "named_paths_uuid": "paths-uuid-1",
                "archive_name": "archive-2026",
            },
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        def _val(fn):
            return (
                _finder(
                    f"$widgets.results.:first().company_names:{fn}()",
                    str(tmp_path),
                )
                .resolve()
                .results[0]
                .data
            )

        assert _val("run_dir") == "2026-01-01_00-00-00"
        assert _val("instance_index") == 2
        assert _val("named_paths_uuid") == "paths-uuid-1"
        assert _val("archive") == "archive-2026"

    def test_error_count_and_has_errors_at_run_and_instance_scope(
        self, tmp_path
    ):
        # ErrorCount3's own KEY widened 2026-10-18 to include instance
        # scope -- the field was already being written by
        # result_registrar.py, confirmed directly against that file,
        # just never exposed; the earlier code comment claiming no
        # per-instance field existed was wrong. :has_errors() (also
        # added 2026-10-18) mirrors Result.has_errors() -- the same
        # "error_count" field, reduced to a bool.
        base = tmp_path / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(
            run_dir / "manifest.json",
            {"run_uuid": "run1-uuid", "error_count": 3},
        )
        _write_json(
            run_dir / "company_names" / "manifest.json",
            {"uuid": "inst1-uuid", "error_count": 0},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        run_count = _finder(
            "$widgets.results.:first():error_count()", str(tmp_path)
        ).resolve()
        assert run_count.results[0].data == 3

        run_has_errors = _finder(
            "$widgets.results.:first():has_errors()", str(tmp_path)
        ).resolve()
        assert run_has_errors.results[0].data is True

        instance_count = _finder(
            "$widgets.results.:first().company_names:error_count()",
            str(tmp_path),
        ).resolve()
        assert instance_count.results[0].data == 0

        instance_has_errors = _finder(
            "$widgets.results.:first().company_names:has_errors()",
            str(tmp_path),
        ).resolve()
        assert instance_has_errors.results[0].data is False

    def test_has_errors_with_no_error_count_recorded_is_false(self, tmp_path):
        # genuinely optional, same treatment every other well-known
        # manifest field gets -- missing is not an error.
        base = tmp_path / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])

        results = _finder(
            "$widgets.results.:first():has_errors()", str(tmp_path)
        ).resolve()
        assert results.results[0].data is False

    def test_error_count_and_has_errors_pooled_across_all_instances(
        self, tmp_path
    ):
        # normative_reference_examples.txt's own worked example --
        # "$alpha.results.:flatten():first().:all():error_count()" --
        # this exact shape was UNRELATED to :has_errors() but
        # previously unsatisfiable: error_count()'s own POSITIONS only
        # allowed name_one before this same fix (2026-10-18), so a
        # name_three ':all():error_count()' would have raised
        # "error_count() is not legal at name_three for results."
        # Confirmed by reading the old POSITIONS dict directly, not
        # assumed.
        base = tmp_path / "alpha"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        _write_json(
            run_dir / "stmt1" / "manifest.json",
            {"uuid": "inst1-uuid", "error_count": 2},
        )
        _write_json(
            run_dir / "stmt2" / "manifest.json",
            {"uuid": "inst2-uuid", "error_count": 0},
        )
        _write_archive_manifest(tmp_path, "alpha", [str(run_dir)])

        counts = _finder(
            "$alpha.results.:flatten():first().:all():error_count()",
            str(tmp_path),
        ).resolve()
        assert sorted(r.data for r in counts.results) == [0, 2]

        has_errors = _finder(
            "$alpha.results.:flatten():first().:all():has_errors()",
            str(tmp_path),
        ).resolve()
        assert sorted(r.data for r in has_errors.results) == [False, True]

    def test_template_at_run_scope(self, tmp_path):
        # :template() (built 2026-08-26) is simple at RESULTS run scope
        # -- no bare/definition duality the way FILES/CSVPATHS have,
        # since a run is not a versioned, editable config artifact.
        # Ordinary SOURCE == "manifest" read, direct from the run's own
        # manifest.json.
        base = tmp_path / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(
            run_dir / "manifest.json",
            {"run_uuid": "run1-uuid", "template": "run-template"},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])
        results = _finder(
            "$widgets.results.:first():template()", str(tmp_path)
        ).resolve()
        assert results.results[0].data == "run-template"


class TestMatchesFieldPredicate:
    # the generic, shared test _star_pool_and_reduce()/
    # _star_group_and_reduce()/query() all use for a field-accessor's
    # own predicate/exact-match argument -- added 2026-10-18.
    def test_predicate_arg_delegates_to_its_own_matches(self):
        from csvpath.references.functions.selectors.after_3 import After3

        assert ResultsReferenceFinder3._matches_field_predicate(5, After3(arg=3))
        assert not ResultsReferenceFinder3._matches_field_predicate(
            2, After3(arg=3)
        )

    def test_bare_value_is_an_exact_match_test(self):
        assert ResultsReferenceFinder3._matches_field_predicate(0, 0)
        assert not ResultsReferenceFinder3._matches_field_predicate(1, 0)


class TestErrorCountPredicateGate:
    # normative_reference_examples.txt's own worked examples, added
    # 2026-10-18 -- ":error_count()" GATEs a pooled '*'/':flatten()'
    # candidate list by its own field value, same mechanism :count()'s
    # own GATE already uses, just reading a manifest field directly
    # instead of opening errors.json:
    #   $*.results.:flatten():error_count(:above(3))   -- more than 3
    #   $*.results.:flatten():error_count(:below(1))   -- none
    #   $*.results.:flatten():error_count(0)            -- none, exact
    @pytest.fixture
    def three_runs(self, tmp_path):
        # _write_json OVERWRITES rather than merging -- each run's own
        # manifest.json is written once, complete, not patched after
        # _make_run's own initial write (which would otherwise lose the
        # "run_uuid" _make_run already wrote).
        base = tmp_path / "acme"
        runs = {}
        for name, run_name, count in (
            ("many-errors", "2026-01-01_00-00-00", 5),
            ("few-errors", "2026-01-02_00-00-00", 2),
            ("no-errors", "2026-01-03_00-00-00", 0),
        ):
            run_dir = base / run_name
            _write_json(
                run_dir / "manifest.json",
                {"run_uuid": name, "error_count": count},
            )
            runs[name] = str(run_dir)
        _write_archive_manifest(tmp_path, "acme", list(runs.values()))
        return str(tmp_path)

    def test_star_root_above_gate(self, three_runs):
        results = _finder(
            "$*.results.:flatten():error_count(:above(3))", three_runs
        ).query()
        assert set(results.uuids) == {"many-errors"}

    def test_star_root_below_gate(self, three_runs):
        results = _finder(
            "$*.results.:flatten():error_count(:below(1))", three_runs
        ).query()
        assert set(results.uuids) == {"no-errors"}

    def test_star_root_exact_int_gate(self, three_runs):
        # "two ways of selecting runs without errors" -- declared
        # equivalent to :below(1) in the normative doc.
        below = _finder(
            "$*.results.:flatten():error_count(:below(1))", three_runs
        ).query()
        exact = _finder(
            "$*.results.:flatten():error_count(0)", three_runs
        ).query()
        assert set(below.uuids) == set(exact.uuids) == {"no-errors"}

    def test_literal_root_gate_is_the_same_mechanism(self, three_runs):
        # the literal-root equivalent -- query()'s own copy of the same
        # filter, not just the '*'-traversal shape the normative doc
        # happens to show.
        results = _finder(
            "$acme.results.:flatten():error_count(:above(3))", three_runs
        ).query()
        assert set(results.uuids) == {"many-errors"}

    def test_bare_field_read_without_a_predicate_is_unaffected(self, three_runs):
        # a no-op when the field accessor carries no argument at all --
        # every run still comes back, each resolving to its own count.
        results = _finder(
            "$*.results.:flatten():error_count()", three_runs
        ).resolve()
        assert sorted(r.data for r in results.results) == [0, 2, 5]


class TestUuidGate:
    # normative_reference_examples.txt's own worked examples, added
    # 2026-10-18 alongside Uuid3/RunUuid3's own ARG_TYPES widening --
    # a side effect of building the bare SELECTOR_WHEN_ARGUED mechanism
    # for FILES/CSVPATHS (see test_uuid_3.py/test_csvpaths_reference_
    # finder_3.py), confirmed live to ALSO correctly GATE RESULTS'
    # pooled candidate lists for free, via the exact same generic
    # field_call/_matches_field_predicate mechanism :error_count() uses
    # (see TestErrorCountPredicateGate just above) -- no RESULTS-side
    # finder code needed, since that mechanism keys on "does this chain
    # member carry an arg," never on which function it is:
    #   $*.results.:flatten():run_uuid("789a..."):template()
    #   $*.results.:flatten():uuid("...")
    @pytest.fixture
    def two_runs(self, tmp_path):
        base = tmp_path / "acme"
        runs = {}
        for name, run_name in (
            ("run-a", "2026-01-01_00-00-00"),
            ("run-b", "2026-01-02_00-00-00"),
        ):
            run_dir = base / run_name
            _write_json(run_dir / "manifest.json", {"run_uuid": name})
            runs[name] = str(run_dir)
        _write_archive_manifest(tmp_path, "acme", list(runs.values()))
        return str(tmp_path)

    def test_run_uuid_gate(self, two_runs):
        results = _finder(
            '$*.results.:flatten():run_uuid("run-b")', two_runs
        ).query()
        assert set(results.uuids) == {"run-b"}

    def test_uuid_gate_is_the_same_mechanism(self, two_runs):
        # ":uuid()" reads "run_uuid" at run scope too (same value as
        # ":run_uuid()", per Uuid3's own docstring) -- confirms the
        # widening applies to both uuid-KIND functions, not just one.
        results = _finder('$*.results.:flatten():uuid("run-a")', two_runs).query()
        assert set(results.uuids) == {"run-a"}

    def test_no_match_gives_empty(self, two_runs):
        results = _finder(
            '$*.results.:flatten():run_uuid("nope")', two_runs
        ).query()
        assert results.results == []

    def test_literal_root_gate_is_the_same_mechanism(self, two_runs):
        results = _finder(
            '$acme.results.:flatten():run_uuid("run-b")', two_runs
        ).query()
        assert set(results.uuids) == {"run-b"}


class TestStatusGate:
    # ':status()' widened 2026-10-18 to also cover FILES (its own
    # dedicated GATE build, PR #398) -- confirmed live at the time, but
    # never committed as a test, that this ALSO GATEs RESULTS' own
    # pooled candidate lists for free, via the exact same generic
    # field_call/_matches_field_predicate mechanism every other
    # widening this week used. RESULTS' own bare, no-arg usage
    # (reading "started"/"complete" off an already-selected run) is
    # unchanged and untouched by this.
    @pytest.fixture
    def two_runs(self, tmp_path):
        base = tmp_path / "acme"
        runs = {}
        for name, run_name, status in (
            ("run-a", "2026-01-01_00-00-00", "started"),
            ("run-b", "2026-01-02_00-00-00", "complete"),
        ):
            run_dir = base / run_name
            _write_json(run_dir / "manifest.json", {"run_uuid": name, "status": status})
            runs[name] = str(run_dir)
        _write_archive_manifest(tmp_path, "acme", list(runs.values()))
        return str(tmp_path)

    def test_status_gate(self, two_runs):
        results = _finder('$*.results.:flatten():status("complete")', two_runs).query()
        assert set(results.uuids) == {"run-b"}

    def test_no_match_gives_empty(self, two_runs):
        results = _finder('$*.results.:flatten():status("nope")', two_runs).query()
        assert results.results == []

    def test_literal_root_gate_is_the_same_mechanism(self, two_runs):
        results = _finder('$acme.results.:flatten():status("started")', two_runs).query()
        assert set(results.uuids) == {"run-a"}

    def test_bare_no_arg_read_is_unaffected(self, two_runs):
        # the original, unchanged shape -- reads the value off an
        # already-selected run, no filtering.
        results = _finder('$acme.results.:last():status()', two_runs).resolve()
        assert results.results[0].data == "complete"


class TestNameAndFingerprintGroupGates:
    # David asked for a list of every function in compendium 6.7's
    # closed "functional taxonomy" that could plausibly need this same
    # retrieve/select duality as :uuid()/:fingerprint()/:named_file_
    # name() but didn't have it yet -- this confirms the remaining
    # five, added 2026-10-18 alongside their own ARG_TYPES widening
    # (same generic field_call/_matches_field_predicate mechanism, no
    # new finder code for any of them):
    #   :named_paths_name() -- "name" group
    #   :named_results_name() -- "name" group
    #   :named_file_uuid() -- "uuid" group
    #   :named_paths_uuid() -- "uuid" group
    #   :named_file_fingerprint() -- "fingerprint" group (also directly
    #     cited: normative_reference_examples.txt's own "select all
    #     runs that used a specific version of a named-file")
    #   :named_paths_fingerprint() -- "fingerprint" group
    @pytest.fixture
    def two_runs(self, tmp_path):
        base = tmp_path / "acme"
        runs = {}
        for name, run_name, named_results_name, nf_uuid, np_uuid, nf_fp, np_fp in (
            ("run-a", "2026-01-01_00-00-00", "resA", "fileA", "pathsA", "fpA", "fpB"),
            ("run-b", "2026-01-02_00-00-00", "resB", "fileB", "pathsB", "fpC", "fpD"),
        ):
            run_dir = base / run_name
            _write_json(
                run_dir / "manifest.json",
                {
                    "run_uuid": name,
                    "named_paths_name": "acme",
                    "named_results_name": named_results_name,
                    "named_file_uuid": nf_uuid,
                    "named_paths_uuid": np_uuid,
                    "named_file_fingerprint": nf_fp,
                    "named_paths_fingerprint": np_fp,
                },
            )
            runs[name] = str(run_dir)
        _write_archive_manifest(tmp_path, "acme", list(runs.values()))
        return str(tmp_path)

    def test_named_paths_name_gate(self, two_runs):
        results = _finder(
            '$*.results.:flatten():named_paths_name("acme")', two_runs
        ).query()
        assert set(results.uuids) == {"run-a", "run-b"}

    def test_named_paths_name_gate_no_match(self, two_runs):
        results = _finder(
            '$*.results.:flatten():named_paths_name("nope")', two_runs
        ).query()
        assert results.results == []

    def test_named_results_name_gate(self, two_runs):
        results = _finder(
            '$*.results.:flatten():named_results_name("resB")', two_runs
        ).query()
        assert set(results.uuids) == {"run-b"}

    def test_named_file_uuid_gate(self, two_runs):
        results = _finder(
            '$*.results.:flatten():named_file_uuid("fileA")', two_runs
        ).query()
        assert set(results.uuids) == {"run-a"}

    def test_named_paths_uuid_gate(self, two_runs):
        results = _finder(
            '$*.results.:flatten():named_paths_uuid("pathsB")', two_runs
        ).query()
        assert set(results.uuids) == {"run-b"}

    def test_named_file_fingerprint_gate(self, two_runs):
        results = _finder(
            '$*.results.:flatten():named_file_fingerprint("fpC")', two_runs
        ).query()
        assert set(results.uuids) == {"run-b"}

    def test_named_paths_fingerprint_gate(self, two_runs):
        results = _finder(
            '$*.results.:flatten():named_paths_fingerprint("fpB")', two_runs
        ).query()
        assert set(results.uuids) == {"run-a"}

    def test_literal_root_gate_is_the_same_mechanism(self, two_runs):
        results = _finder(
            '$acme.results.:flatten():named_results_name("resA")', two_runs
        ).query()
        assert set(results.uuids) == {"run-a"}


class TestHavingNestedFieldAccessor:
    # ':having()' widened 2026-10-18 to accept a nested field-accessor
    # function, not just a plain identity string -- David: "scoping it
    # more broadly fits the brief, and the intent." Closes the layered
    # gap in normative_reference_examples.txt's own "two ways to get
    # the run dir of a run containing a csvpath instance with a
    # certain UUID": "$*.results.:manifest():uuid(\"a381...\"):
    # run_home()" (built in #395, the archive-ledger route) and
    # "$*.results.:flatten():having(:uuid(\"a381...\")):run_home()"
    # (built here, the direct-access route) -- "functionally
    # identical," per the doc's own framing.
    @pytest.fixture
    def two_runs_with_instances(self, tmp_path):
        base = tmp_path / "acme"
        run1 = _make_run(
            base, "2026-01-01_00-00-00", "run1", {"invoices": "a381-match"}
        )
        run2 = _make_run(base, "2026-01-02_00-00-00", "run2", {"invoices": "other"})
        _write_archive_manifest(tmp_path, "acme", [run1, run2])
        return str(tmp_path)

    def test_matches_the_run_containing_an_instance_with_that_uuid(
        self, two_runs_with_instances
    ):
        results = _finder(
            '$*.results.:flatten():having(:uuid("a381-match")):run_home()',
            two_runs_with_instances,
        ).query()
        assert sorted(results.uuids) == ["run1"]

    def test_no_matching_instance_gives_empty(self, two_runs_with_instances):
        results = _finder(
            '$*.results.:flatten():having(:uuid("no-such-uuid")):run_home()',
            two_runs_with_instances,
        ).query()
        assert results.results == []

    def test_plain_identity_string_form_is_unaffected(
        self, two_runs_with_instances
    ):
        # the original, unchanged shape -- matches by instance IDENTITY
        # NAME, not by a field's VALUE. Both runs have an "invoices"
        # instance, so both come back.
        results = _finder(
            '$*.results.:flatten():having("invoices"):run_home()',
            two_runs_with_instances,
        ).query()
        assert sorted(results.uuids) == ["run1", "run2"]

    def test_field_with_no_instance_scope_key_raises_clearly(
        self, two_runs_with_instances
    ):
        # :named_paths_name() has no Reference3.RESULT (instance-scope)
        # KEY entry -- run scope only -- so matching by it per-instance
        # is meaningless; raises clearly rather than silently matching
        # nothing.
        with pytest.raises(ReferenceException3):
            _finder(
                '$*.results.:flatten():having(:named_paths_name("x")):run_home()',
                two_runs_with_instances,
            ).query()


class TestHavingListArgument:
    # ':having()' widened again 2026-10-18 (same day) to also accept a
    # `list` -- confirmed live that a variable resolving to a list used
    # to raise ReferenceRuntimeException3 outright. David confirmed the
    # normative doc genuinely needs "does this run have an instance
    # matching ANY of these identities," distinct from (and simpler
    # than) the nested-field-accessor case above -- a list is only ever
    # reachable via an `@variable`, the grammar has no literal list
    # syntax.
    @pytest.fixture
    def three_runs_with_instances(self, tmp_path):
        base = tmp_path / "acme"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1", {"invoices": "x"})
        run2 = _make_run(base, "2026-01-02_00-00-00", "run2", {"receipts": "y"})
        run3 = _make_run(base, "2026-01-03_00-00-00", "run3", {"other": "z"})
        _write_archive_manifest(tmp_path, "acme", [run1, run2, run3])
        return str(tmp_path)

    def test_matches_any_run_with_an_instance_in_the_list(
        self, three_runs_with_instances
    ):
        results = _finder(
            "$*.results.:flatten():having(@identities)",
            three_runs_with_instances,
            variables={"identities": ["invoices", "receipts"]},
        ).query()
        assert sorted(results.uuids) == ["run1", "run2"]

    def test_no_matching_identity_in_the_list_gives_empty(
        self, three_runs_with_instances
    ):
        results = _finder(
            "$*.results.:flatten():having(@identities)",
            three_runs_with_instances,
            variables={"identities": ["nope", "also-nope"]},
        ).query()
        assert results.results == []

    def test_literal_root_list_having_is_the_same_mechanism(
        self, three_runs_with_instances
    ):
        results = _finder(
            "$acme.results.:flatten():having(@identities)",
            three_runs_with_instances,
            variables={"identities": ["other"]},
        ).query()
        assert sorted(results.uuids) == ["run3"]


class TestArchiveLedgerFallback:
    # Table 7 (the Archive Run Manifest, RESULTS' own global ledger) is
    # per-statement-execution, keyed by "run_uuid" + "identity", not a
    # single "uuid" the way FILES/CSVPATHS ledgers are -- wired in
    # 2026-08-26 via ResultsReferenceFinder3._find_archive_ledger_entry(),
    # closing the last open gap in the field-accessor ledger-fallback
    # mechanism (see FILES'/CSVPATHS' own :file_manifest()/:group_
    # manifest() precedent). archive_name/archive_path/named_files_root/
    # named_paths_root are run-level facts (same value across every
    # statement in one run, confirmed against run_registrar.py), so a
    # run-scope lookup only needs to match run_uuid, not identity too.
    def test_run_scope_archive_falls_back_to_the_ledger_entry(self, tmp_path):
        # the run's own manifest (table 5, written by results_registrar.py)
        # never has "archive_name" -- only the ledger entry (table 7,
        # written by run_registrar.py) does.
        base = tmp_path / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        _write_json(
            tmp_path / "manifest.json",
            [
                {
                    "run_uuid": "run1-uuid",
                    "identity": "company_names",
                    "named_paths_name": "widgets",
                    "run_home": str(run_dir),
                    "archive_name": "archive-2026",
                }
            ],
        )
        results = _finder(
            "$widgets.results.:first():archive()", str(tmp_path)
        ).resolve()
        assert results.results[0].data == "archive-2026"

    def test_run_scope_ledger_only_fields_resolve(self, tmp_path):
        base = tmp_path / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        _write_json(
            tmp_path / "manifest.json",
            [
                {
                    "run_uuid": "run1-uuid",
                    "identity": "company_names",
                    "named_paths_name": "widgets",
                    "run_home": str(run_dir),
                    "archive_path": "/archives/archive-2026",
                    "named_files_root": "/inputs/named_files",
                    "named_paths_root": "/inputs/named_paths",
                }
            ],
        )

        def _val(fn):
            return (
                _finder(f"$widgets.results.:first():{fn}()", str(tmp_path))
                .resolve()
                .results[0]
                .data
            )

        assert _val("archive_path") == "/archives/archive-2026"
        assert _val("named_files_root") == "/inputs/named_files"
        assert _val("named_paths_root") == "/inputs/named_paths"

    def test_run_scope_ledger_only_field_with_no_matching_entry_gives_none(
        self, tmp_path
    ):
        # the run's own uuid genuinely has no ledger entry at all (e.g.
        # a stale/hand-built fixture) -- falls through to None, same as
        # any other missing field, rather than raising.
        base = tmp_path / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        _write_json(
            tmp_path / "manifest.json",
            [
                {
                    # discovery still needs named_paths_name/run_home to
                    # find this run at all -- but run_uuid deliberately
                    # does not match "run1-uuid", so the fallback lookup
                    # itself finds nothing.
                    "run_uuid": "some-other-run-uuid",
                    "identity": "company_names",
                    "named_paths_name": "widgets",
                    "run_home": str(run_dir),
                }
            ],
        )
        results = _finder(
            "$widgets.results.:first():archive_path()", str(tmp_path)
        ).resolve()
        assert results.results[0].data is None

    def test_instance_scope_archive_still_reads_its_own_manifest_directly(
        self, tmp_path
    ):
        # regression guard: instance scope (table 6) already has its own
        # "archive_name" field (confirmed against result_registrar.py) --
        # this must keep resolving directly, never touching the ledger.
        base = tmp_path / "widgets"
        run_dir = base / "2026-01-01_00-00-00"
        instance_dir = run_dir / "company_names"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        _write_json(
            instance_dir / "manifest.json",
            {"uuid": "inst1-uuid", "archive_name": "instance-own-archive"},
        )
        _write_archive_manifest(tmp_path, "widgets", [str(run_dir)])
        results = _finder(
            "$widgets.results.:first().company_names:archive()", str(tmp_path)
        ).resolve()
        assert results.results[0].data == "instance-own-archive"


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

    def test_errors_with_idchain_not_none_filters_to_entries_that_have_any_source(
        self, acme_archive, instance_dir
    ):
        # compendium 5.31/5.36/4.13's own settled worked example --
        # :not_none() (built 2026-08-26) nested inside :idchain() means
        # "any idchain at all", not one specific value/pattern.
        errors = [
            {"source": "add[0]string[2]", "message": "bad add"},
            {"message": "no source recorded for this one"},
        ]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            "$acme.results.customers/2025:first().company_names"
            ":errors(:idchain(:not_none()))",
            acme_archive,
        ).resolve()
        assert results.results[0].data == [errors[0]]

    def test_errors_with_message_filters_to_matching_message(
        self, acme_archive, instance_dir
    ):
        # :message() -- added 2026-10-17, the direct sibling of
        # :idchain() (normative_reference_examples.txt places them right
        # next to each other) -- filters errors.json entries by their
        # own "message" field instead of "source".
        errors = [
            {"source": "add[0]string[2]", "message": "customer: 319 not found"},
            {"source": "name[1]", "message": "bad name"},
        ]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':errors(:message(/customer: 319/))',
            acme_archive,
        ).resolve()
        assert results.results[0].data == [errors[0]]

    def test_errors_with_message_no_match_returns_empty_list(
        self, acme_archive, instance_dir
    ):
        errors = [{"source": "name[1]", "message": "bad name"}]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':errors(:message(/customer: 319/))',
            acme_archive,
        ).resolve()
        assert results.results[0].data == []

    def test_errors_with_message_exact_string_match(
        self, acme_archive, instance_dir
    ):
        errors = [
            {"source": "add[0]", "message": "bad add"},
            {"source": "name[1]", "message": "bad name"},
        ]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':errors(:message("bad name"))',
            acme_archive,
        ).resolve()
        assert results.results[0].data == [errors[1]]

    def test_errors_with_message_not_none_filters_to_entries_that_have_any_message(
        self, acme_archive, instance_dir
    ):
        errors = [
            {"source": "add[0]", "message": "bad add"},
            {"source": "name[1]"},
        ]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            "$acme.results.customers/2025:first().company_names"
            ":errors(:message(:not_none()))",
            acme_archive,
        ).resolve()
        assert results.results[0].data == [errors[0]]

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

    def test_printouts_resolves_raw_bytes(self, acme_archive, instance_dir):
        content = b"---- PRINTOUT: line 1 ----\nhello\n"
        with open(os.path.join(instance_dir, "printouts.txt"), "wb") as f:
            f.write(content)
        results = _finder(
            "$acme.results.customers/2025:first().company_names:printouts()",
            acme_archive,
        ).resolve()
        assert results.results[0].data == content

    def test_printouts_resolves_none_when_never_written(
        self, acme_archive, instance_dir
    ):
        # printouts.txt is only written if the csvpath statement printed
        # something -- genuinely optional, same as data.csv/unmatched.csv.
        results = _finder(
            "$acme.results.customers/2025:first().company_names:printouts()",
            acme_archive,
        ).resolve()
        assert results.results[0].data is None

    def test_printouts_with_a_name_reads_that_streams_own_file(
        self, acme_archive, instance_dir
    ):
        # named stream under print-mode:separate, added 2026-09-21 --
        # ":printouts('greetings')" reads "greetings.txt", not the fixed
        # combined-output "printouts.txt".
        content = b"---- PRINTOUT: greetings ----\nhello world\n"
        with open(os.path.join(instance_dir, "greetings.txt"), "wb") as f:
            f.write(content)
        results = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':printouts("greetings")',
            acme_archive,
        ).resolve()
        assert results.results[0].data == content

    def test_printouts_with_a_name_is_equivalent_to_file(
        self, acme_archive, instance_dir
    ):
        # the normative doc's own declared equivalence:
        # ":printouts('greetings')" and ":file('greetings.txt')" resolve
        # to the same content.
        content = b"---- PRINTOUT: greetings ----\nhello world\n"
        with open(os.path.join(instance_dir, "greetings.txt"), "wb") as f:
            f.write(content)
        via_printouts = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':printouts("greetings")',
            acme_archive,
        ).resolve()
        via_file = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':file("greetings.txt")',
            acme_archive,
        ).resolve()
        assert via_printouts.results[0].data == via_file.results[0].data == content

    def test_original_resolves_raw_bytes_regardless_of_extension(
        self, acme_archive, instance_dir
    ):
        # added 2026-10-15, closing the deferred-work bucket list gap
        # for #350. Unlike every other well-known file here, original.
        # <ext>'s own extension varies by source type -- confirmed
        # against ResultRegistrar._original_file()'s real lookup
        # convention before building (list the instance dir, match the
        # "original."-prefix) rather than assuming a fixed name.
        content = b"a,b\n1,2\n"
        with open(os.path.join(instance_dir, "original.csv"), "wb") as f:
            f.write(content)
        results = _finder(
            "$acme.results.customers/2025:first().company_names:original()",
            acme_archive,
        ).resolve()
        assert results.results[0].data == content

    def test_original_resolves_raw_bytes_for_a_different_extension(
        self, acme_archive, instance_dir
    ):
        # same lookup, a different source type -- proves this is not
        # hard-coded to ".csv".
        content = b"<root><row/></root>"
        with open(os.path.join(instance_dir, "original.xml"), "wb") as f:
            f.write(content)
        results = _finder(
            "$acme.results.customers/2025:first().company_names:original()",
            acme_archive,
        ).resolve()
        assert results.results[0].data == content

    def test_original_resolves_none_when_never_collected(
        self, acme_archive, instance_dir
    ):
        # collect_original() is opt-in -- genuinely optional, same
        # treatment as data.csv/unmatched.csv/printouts.txt.
        results = _finder(
            "$acme.results.customers/2025:first().company_names:original()",
            acme_archive,
        ).resolve()
        assert results.results[0].data is None

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

    def test_accessor_combined_with_all_pools_and_resolve_raises_when_ambiguous(
        self, acme_archive
    ):
        # run1 has two instances: company_names and "1", each with its
        # own separate meta.json. :all() (every instance in the run)
        # combined with an accessor used to be an immediate, unconditional
        # rejection here -- relaxed 2026-10-17 alongside
        # ":errors(:count(:above(10)))" (normative examples 489-491),
        # which needs exactly this combination to pool candidates before
        # each one's own count is gated. query() now pools both instances
        # (flagged ambiguous_content_read); resolving full content for
        # both AT ONCE is still Rule 1 territory -- resolve() refuses,
        # same deferred pattern every other whole-resource accessor
        # already uses (see test_all_grouping_with_name_three_content_
        # accessor_resolve_raises_when_ambiguous just above's '*'-root
        # equivalent).
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
        results = finder.query()
        assert len(results.results) == 2
        assert results.ambiguous_content_read is True
        with pytest.raises(ReferenceException3):
            finder.resolve()

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


class TestErrorsIdchainGate:
    # the GATE half of "position decides meaning" (David, 2026-08-21;
    # settled compendium 4.13/4.14, built 2026-10-17) -- an :idchain(...)
    # CHAINED after :errors() in the same func_chain (NOT nested as its
    # own argument -- that is the pre-existing FILTER shape, untouched)
    # does not narrow errors.json's own entries; it decides whether the
    # WHOLE, unfiltered content is returned at all. The five settled
    # acceptance-criteria references from the compendium itself:
    #   :errors()                        -- full content
    #   :errors(:idchain(:not_none()))   -- filter: entries that HAVE an idchain
    #   :errors(:idchain("add[0]"))      -- filter: entries matching that idchain
    #   :errors():idchain(:not_none())   -- gate: full content, iff some idchain exists
    #   :errors():idchain("add[0]")      -- gate: full content, iff a matching idchain exists
    @pytest.fixture
    def instance_dir(self, acme_archive):
        path = (
            f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
            "/company_names"
        )
        os.makedirs(path, exist_ok=True)
        return path

    def test_gate_not_none_passes_when_any_entry_has_a_source(
        self, acme_archive, instance_dir
    ):
        errors = [
            {"source": "add[0]string[2]", "message": "bad add"},
            {"message": "no source recorded for this one"},
        ]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            "$acme.results.customers/2025:first().company_names"
            ":errors():idchain(:not_none())",
            acme_archive,
        ).resolve()
        # the WHOLE, UNFILTERED list -- not narrowed to just the
        # matching entry, unlike the filter shape.
        assert results.results[0].data == errors

    def test_gate_not_none_fails_when_no_entry_has_a_source(
        self, acme_archive, instance_dir
    ):
        errors = [{"message": "no source recorded for this one"}]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            "$acme.results.customers/2025:first().company_names"
            ":errors():idchain(:not_none())",
            acme_archive,
        ).resolve()
        assert results.results[0].data is None

    def test_gate_exact_string_passes_when_a_matching_entry_exists(
        self, acme_archive, instance_dir
    ):
        errors = [
            {"source": "add[0]string[2]", "message": "bad add"},
            {"source": "name[1]", "message": "bad name"},
        ]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':errors():idchain("add[0]string[2]")',
            acme_archive,
        ).resolve()
        assert results.results[0].data == errors

    def test_gate_exact_string_fails_when_no_entry_matches(
        self, acme_archive, instance_dir
    ):
        errors = [{"source": "name[1]", "message": "bad name"}]
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)
        results = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':errors():idchain("add[0]string[2]")',
            acme_archive,
        ).resolve()
        assert results.results[0].data is None

    def test_gate_with_no_errors_file_resolves_to_none(
        self, acme_archive, instance_dir
    ):
        # errors.json genuinely never written -- same "optional" miss
        # every other well-known file gets, not an error.
        results = _finder(
            "$acme.results.customers/2025:first().company_names"
            ":errors():idchain(:not_none())",
            acme_archive,
        ).resolve()
        assert results.results[0].data is None

    def test_idchain_alone_in_name_three_without_errors_is_rejected(
        self, acme_archive, instance_dir
    ):
        with pytest.raises(ReferenceException3):
            _finder(
                "$acme.results.customers/2025:first().company_names"
                ":idchain(:not_none())",
                acme_archive,
            ).query()

    def test_filter_shape_is_unaffected_still_narrows_the_entries(
        self, acme_archive, instance_dir
    ):
        # the pre-existing, nested FILTER shape -- confirms the new GATE
        # dispatch did not disturb it.
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


class TestErrorsCountGate:
    # the third, EXPLICIT exception to nested=FILTER (see Errors3's own
    # comment and Count3's docstring) -- normative examples 489-491's
    # worked example, ":errors(:count(:above(10)))". Despite being
    # NESTED (normally the FILTER position), :count() cannot filter
    # entries -- it is an aggregate over the whole array -- so it gates
    # the whole, unfiltered content instead, same all-or-nothing
    # treatment as the chained :idchain() GATE above. Built 2026-10-17,
    # alongside the ":all()"/"'*'"-at-name_three and implied-'*' parsing
    # fixes this worked example also needed (see TestScopeLimits).

    def _write_errors(self, instance_dir: str, count: int) -> None:
        errors = [{"source": f"add[{i}]", "message": "bad add"} for i in range(count)]
        os.makedirs(instance_dir, exist_ok=True)
        with open(os.path.join(instance_dir, "errors.json"), "w") as f:
            json.dump(errors, f)

    def test_gate_passes_when_count_is_above_bound(self, acme_archive):
        base = f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
        self._write_errors(f"{base}/company_names", 11)
        results = _finder(
            "$acme.results.customers/2025:first().company_names"
            ":errors(:count(:above(10)))",
            acme_archive,
        ).resolve()
        assert len(results.results[0].data) == 11

    def test_gate_fails_when_count_is_at_or_below_bound(self, acme_archive):
        base = f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
        self._write_errors(f"{base}/company_names", 10)
        results = _finder(
            "$acme.results.customers/2025:first().company_names"
            ":errors(:count(:above(10)))",
            acme_archive,
        ).resolve()
        assert results.results[0].data is None

    def test_gate_with_no_errors_file_resolves_to_none(self, acme_archive):
        base = f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
        os.makedirs(f"{base}/company_names", exist_ok=True)
        results = _finder(
            "$acme.results.customers/2025:first().company_names"
            ":errors(:count(:above(10)))",
            acme_archive,
        ).resolve()
        assert results.results[0].data is None

    def test_explicit_star_pools_every_instance_and_each_gates_on_its_own(
        self, acme_archive
    ):
        # "$acme.results.customers/2025:first().*:errors(:count(
        # :above(10)))" -- normative examples 489-491's first form.
        # run1 (:first()) has two instances: company_names (11 errors,
        # qualifies) and "1" (3 errors, does not).
        base = f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
        self._write_errors(f"{base}/company_names", 11)
        self._write_errors(f"{base}/1", 3)
        finder = _finder(
            "$acme.results.customers/2025:first().*:errors(:count(:above(10)))",
            acme_archive,
        )
        results = finder.query()
        assert len(results.results) == 2
        assert results.ambiguous_content_read is True
        # resolving both pooled instances AT ONCE is still Rule 1
        # territory -- resolve() refuses, same as every other whole-
        # resource accessor's own pooled case.
        with pytest.raises(ReferenceException3):
            finder.resolve()
        # resolving each instance individually, though, works fine and
        # gates correctly per instance -- select()'s own
        # ambiguous_content_read is copied from the original (still
        # True), but resolve_from()'s raise is also conditioned on
        # len(results) > 1, so a single-path selection never raises.
        qualifying = []
        for r in results.results:
            resolved = finder.resolve_from([r.path])
            if resolved.results[0].data is not None:
                qualifying.append(resolved.results[0].data)
        assert len(qualifying) == 1
        assert len(qualifying[0]) == 11

    def test_implied_star_bare_form_is_equivalent_to_the_explicit_star_form(
        self, acme_archive
    ):
        # "$acme.results.customers/2025:first().:errors(:count(
        # :above(10)))" -- normative examples 489-491's second form,
        # declared equivalent to the first (compendium 3.19b's implied
        # '*' for a functions-only name_three).
        base = f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
        self._write_errors(f"{base}/company_names", 11)
        self._write_errors(f"{base}/1", 3)
        finder = _finder(
            "$acme.results.customers/2025:first().:errors(:count(:above(10)))",
            acme_archive,
        )
        results = finder.query()
        assert len(results.results) == 2
        assert results.ambiguous_content_read is True

    def test_filter_shape_is_unaffected_still_narrows_the_entries(
        self, acme_archive
    ):
        # confirms the new GATE dispatch did not disturb the pre-
        # existing, nested :idchain()/:message() FILTER shape (same
        # nested position, different mechanism -- see Errors3's own
        # comment for why :count() is the one documented exception).
        base = f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
        errors = [
            {"source": "add[0]string[2]", "message": "bad add"},
            {"source": "name[1]", "message": "bad name"},
        ]
        os.makedirs(f"{base}/company_names", exist_ok=True)
        with open(f"{base}/company_names/errors.json", "w") as f:
            json.dump(errors, f)
        results = _finder(
            '$acme.results.customers/2025:first().company_names'
            ':errors(:idchain("add[0]string[2]"))',
            acme_archive,
        ).resolve()
        assert results.results[0].data == [errors[0]]


class TestGlobalArchiveLedger:
    # Rule 1a: "*" at root_major combined with a bare :manifest() is the
    # one exception to root_major=="*" being unsupported -- it resolves
    # to the Archive Run Manifest, the single global ledger at the
    # archive root already used internally to discover runs.
    def test_query_returns_the_global_ledger_path_with_no_uuid(self, acme_archive):
        results = _finder("$*.results.:manifest()", acme_archive).query()
        assert results.files == [pathu.resep(f"{acme_archive}/manifest.json")]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_global_ledger_as_parsed_json(self, acme_archive):
        results = _finder("$*.results.:manifest()", acme_archive).resolve()
        data = results.results[0].data
        assert isinstance(data, list)
        assert {e["named_paths_name"] for e in data} == {"acme"}

    def test_star_with_a_bare_pointer_is_supported(self, tmp_path):
        # '*' traversal is supported now for the bare-pointer case (see
        # TestStarTraversal below) -- with only one named-results group,
        # its runs flat (zero-level, per the 2026-08-10 semantics),
        # this confirms it resolves to that group's own last run rather
        # than raising.
        base = tmp_path / "acme"
        run1 = _make_run(base, "2026-01-01_00-00-00", "run1-uuid", {})
        run2 = _make_run(base, "2026-01-02_00-00-00", "run2-uuid", {})
        _write_archive_manifest(tmp_path, "acme", [run1, run2])
        finder = _finder("$*.results.:last()", str(tmp_path))
        results = finder.query()
        assert len(results.results) == 1
        assert results.results[0].uuid == "run2-uuid"

    def test_star_with_a_bare_pointer_excludes_a_deep_templated_run(
        self, acme_archive
    ):
        # acme_archive's only group has its runs nested under
        # "customers/2025" -- with no zero-level runs anywhere, '*'
        # traversal correctly finds nothing, same restriction the
        # single-group case now applies.
        results = _finder("$*.results.:last()", acme_archive).query()
        assert results.results == []

    def test_star_with_a_literal_path_prefix_now_works(self, acme_archive):
        # closes the path-narrowing gap (2026-08-19) -- matches
        # acme_archive's own "customers/2025" template, relative to
        # acme's own group home, the same way the literal-root case
        # already does, just discovered via '*' traversal instead.
        results = _finder(
            "$*.results.customers/2025:last()", acme_archive
        ).query()
        assert results.results[0].uuid == "run2-uuid"

    def test_star_with_a_literal_path_prefix_excludes_non_matching_groups(
        self, two_group_archive
    ):
        # two_group_archive's runs are all flat (zero-level) -- a
        # literal "customers/2025" prefix matches neither group, so
        # this correctly finds nothing rather than falling back to
        # some other group's run.
        results = _finder(
            "$*.results.customers/2025:last()", two_group_archive
        ).query()
        assert results.results == []


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
        assert results.files == [pathu.resep(f"{archive}/manifest.json")]
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

    def test_bare_all_with_no_pointer_lists_every_flat_run(
        self, two_group_archive
    ):
        # REVISED 2026-09-21 (was: "gives empty on flat runs" -- ':all()'
        # used to require exactly one level; now degenerates to zero-
        # level per compendium 4.2b). A pointer is optional everywhere
        # in star traversal (settled 2026-08-19) -- absence means "every
        # matched run, unreduced." two_group_archive's runs are all flat
        # (zero-level), so ':all()' now matches every one of them.
        results = _finder("$*.results.:all()", two_group_archive).query()
        assert sorted(results.uuids) == [
            "acme-run1-uuid",
            "acme-run2-uuid",
            "widgets-run1-uuid",
        ]

    def test_bare_all_with_no_pointer_gives_empty_on_one_level_runs(
        self, tmp_path
    ):
        # REVISED 2026-09-21 (was: "lists every one-level run" -- the
        # opposite is now true, since ':all()' no longer matches beyond
        # zero-level at all).
        acme_x = _make_run(
            tmp_path / "acme" / "east", "2026-01-01_00-00-00", "acme-east", {}
        )
        acme_y = _make_run(
            tmp_path / "acme" / "west", "2026-01-02_00-00-00", "acme-west", {}
        )
        widgets_x = _make_run(
            tmp_path / "widgets" / "east",
            "2026-01-03_00-00-00",
            "widgets-east",
            {},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_x, acme_y], "widgets": [widgets_x]}
        )
        results = _finder("$*.results.:all()", str(tmp_path)).query()
        assert results.results == []

    def test_name_three_combined_with_traversal_now_works(self, tmp_path):
        # closes the name_three gap (2026-08-19) -- _results_for_run()
        # already does the identity selection entirely from a real run
        # directory, independent of group, so it composes with a bare
        # pointer here unchanged. widgets' run is the true global-
        # latest, so this proves the run-selection AND the instance
        # selection within it both resolved correctly, not just one.
        acme_run = _make_run(
            tmp_path / "acme",
            "2026-01-01_00-00-00",
            "acme-run",
            {"invoices": "acme-invoices-uuid"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets",
            "2026-01-03_00-00-00",
            "widgets-run",
            {"invoices": "widgets-invoices-uuid"},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_run], "widgets": [widgets_run]}
        )
        results = _finder(
            "$*.results.:last().invoices", str(tmp_path)
        ).query()
        assert results.results[0].uuid == "widgets-invoices-uuid"

    def test_name_three_with_no_matching_identity_is_empty_not_an_error(
        self, two_group_archive
    ):
        # two_group_archive's runs have no instances at all -- a
        # literal identity that matches nothing correctly gives an
        # empty result, not an error.
        results = _finder("$*.results.:last().0", two_group_archive).query()
        assert results.results == []

    def test_field_accessor_combined_with_star_traversal_now_works(self, tmp_path):
        # closes the gap ReferenceExpression3 needed -- a run-level
        # field accessor can now ride alongside the pointer in '*'
        # traversal, resolving from whichever real run matched,
        # regardless of which group it came from (see _extract_data's
        # own comment on why no group-name context is needed for
        # RESULTS, unlike CSVPATHS' equivalent fix).
        acme_base = tmp_path / "acme"
        acme_run1 = _make_run(acme_base, "2026-01-01_00-00-00", "acme-run1-uuid", {})
        _write_json(
            Path(acme_run1) / "manifest.json",
            {"run_uuid": "acme-run1-uuid", "named_paths_name": "acme"},
        )
        widgets_base = tmp_path / "widgets"
        widgets_run1 = _make_run(
            widgets_base, "2026-01-03_00-00-00", "widgets-run1-uuid", {}
        )
        _write_json(
            Path(widgets_run1) / "manifest.json",
            {"run_uuid": "widgets-run1-uuid", "named_paths_name": "widgets"},
        )
        _write_archive_manifest_multi(
            tmp_path,
            {"widgets": [widgets_run1], "acme": [acme_run1]},
        )
        results = _finder(
            "$*.results.:last():named_paths_name()", str(tmp_path)
        ).resolve()
        assert len(results.results) == 1
        assert results.results[0].uuid == "widgets-run1-uuid"
        assert results.results[0].data == "widgets"

    def test_field_accessor_exemption_does_not_let_a_second_extra_through(
        self, two_group_archive
    ):
        # a field accessor is now exempt from the non-pointer rejection,
        # but a genuinely unsupported extra riding alongside it is
        # still rejected -- proves the exemption is narrowly scoped to
        # the one matched field call, not "anything goes once one
        # field accessor is present". :groups() used to be this test's
        # own example of "genuinely unsupported" -- it got its own '*'-
        # traversal support 2026-10-18, so :webhooks() (registered for
        # a different datatype entirely, not even results-relevant)
        # takes its place here instead.
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.results.:last():named_paths_name():webhooks()",
                two_group_archive,
            ).query()

    def test_bare_pointer_resolve_with_no_manifest_and_no_field_accessor_gives_none(
        self, two_group_archive
    ):
        # previously-latent bug: _extract_data's star-traversal branch
        # checked isinstance(root_major, Star3) unconditionally, so a
        # plain resolve() with no :manifest() and no field accessor
        # incorrectly took the global-ledger-by-uuid path (Rule 1b)
        # instead of falling through to "no single unambiguous payload"
        # -- confirmed via grep that no existing test called resolve()
        # on a bare star-traversal reference before this fix.
        result = _finder("$*.results.:last()", two_group_archive).resolve()
        assert result.results[0].data is None


class TestStarTraversalHaving:
    # ':having("identity")' widened to RESULTS star traversal 2026-08-27
    # (same bucket-list entry as the literal-root case above) -- filters
    # the candidate run pool, across every group, down to runs
    # containing a matching instance, before the pointer/grouping
    # reduces. Exercises both shared-tail methods: _star_pool_and_reduce
    # (bare pointer/':flatten()') and _star_group_and_reduce (':all()').
    def test_bare_pointer_with_having_finds_the_qualifying_run(self, tmp_path):
        acme_run = _make_run(
            tmp_path / "acme",
            "2026-01-01_00-00-00",
            "acme-run-uuid",
            {"orders": "acme-orders-uuid"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets",
            "2026-01-02_00-00-00",
            "widgets-run-uuid",
            {"other": "widgets-other-uuid"},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_run], "widgets": [widgets_run]}
        )
        # widgets is chronologically later, but only acme "has" orders --
        # proves the pool is filtered before :last() reduces it.
        results = _finder(
            '$*.results.:having("orders"):last()', str(tmp_path)
        ).query()
        assert results.uuids == ["acme-run-uuid"]

    def test_no_pointer_returns_every_qualifying_run_unreduced(self, tmp_path):
        acme_run = _make_run(
            tmp_path / "acme",
            "2026-01-01_00-00-00",
            "acme-run-uuid",
            {"orders": "acme-orders-uuid"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets",
            "2026-01-02_00-00-00",
            "widgets-run-uuid",
            {"other": "widgets-other-uuid"},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_run], "widgets": [widgets_run]}
        )
        results = _finder('$*.results.:having("orders")', str(tmp_path)).query()
        assert results.uuids == ["acme-run-uuid"]

    def test_no_matching_run_gives_empty(self, tmp_path):
        acme_run = _make_run(
            tmp_path / "acme",
            "2026-01-01_00-00-00",
            "acme-run-uuid",
            {"orders": "acme-orders-uuid"},
        )
        _write_archive_manifest_multi(tmp_path, {"acme": [acme_run]})
        results = _finder(
            '$*.results.:having("nonexistent"):last()', str(tmp_path)
        ).query()
        assert results.uuids == []

    def test_flatten_with_having_finds_the_qualifying_run_at_any_depth(
        self, tmp_path
    ):
        acme_run = _make_run(
            tmp_path / "acme" / "east",
            "2026-01-01_00-00-00",
            "acme-run-uuid",
            {"orders": "acme-orders-uuid"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets",
            "2026-01-02_00-00-00",
            "widgets-run-uuid",
            {"other": "widgets-other-uuid"},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_run], "widgets": [widgets_run]}
        )
        results = _finder(
            '$*.results.:flatten():having("orders")', str(tmp_path)
        ).query()
        assert results.uuids == ["acme-run-uuid"]

    def test_all_grouping_with_having_filters_before_partitioning(self, tmp_path):
        # REVISED 2026-09-21: both runs moved to zero-level (were 1-level
        # "acme/east"/"widgets/west", which ':all()' no longer matches
        # at all per the 4.2b degenerate-grouping fix). widgets is still
        # filtered out by ':having()' entirely, so only acme's own group
        # survives to be reduced.
        acme_run = _make_run(
            tmp_path / "acme",
            "2026-01-01_00-00-00",
            "acme-run-uuid",
            {"orders": "acme-orders-uuid"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets",
            "2026-01-02_00-00-00",
            "widgets-run-uuid",
            {"other": "widgets-other-uuid"},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_run], "widgets": [widgets_run]}
        )
        results = _finder(
            '$*.results.:all():having("orders"):last()', str(tmp_path)
        ).query()
        assert results.uuids == ["acme-run-uuid"]


class TestStarTraversalPathNarrowingAndNameThree:
    # closes the "literal/'*' path narrowing" and "name_three" gaps in
    # _query_star_traversal -- added 2026-08-19, alongside the ':all()'
    # meaning-collision fix. Thorough coverage of the literal/'*'-
    # prefixed shapes (prefix+':flatten()', prefix+':all()') and of
    # name_three (an instance selector) composing with every run-
    # selection shape, since _results_for_run() already did the
    # identity/':all()'/range selection entirely group-independently.
    def test_prefixed_flatten_pools_any_depth_beyond_prefix_across_groups(
        self, tmp_path
    ):
        acme_shallow = _make_run(
            tmp_path / "acme" / "beta", "2026-01-01_00-00-00", "acme-shallow", {}
        )
        acme_deep = _make_run(
            tmp_path / "acme" / "beta" / "x" / "y",
            "2026-01-02_00-00-00",
            "acme-deep",
            {},
        )
        widgets_deep = _make_run(
            tmp_path / "widgets" / "beta" / "z",
            "2026-01-03_00-00-00",
            "widgets-deep",
            {},
        )
        widgets_other = _make_run(
            tmp_path / "widgets" / "gamma",
            "2026-01-04_00-00-00",
            "widgets-other",
            {},
        )
        _write_archive_manifest_multi(
            tmp_path,
            {
                "acme": [acme_shallow, acme_deep],
                "widgets": [widgets_deep, widgets_other],
            },
        )
        # widgets-other (gamma) is chronologically latest overall, but
        # does not match the "beta" prefix -- proves the prefix is
        # actually filtering, not just falling back to global latest.
        results = _finder(
            "$*.results.beta/:flatten():last()", str(tmp_path)
        ).query()
        assert results.results[0].uuid == "widgets-deep"

    def test_prefixed_all_pools_within_each_group_beyond_prefix(
        self, tmp_path
    ):
        # REVISED 2026-09-21 -- supersedes a test proving the prefixed
        # shape partitioned by a composite (group, value) key. That no
        # longer applies: "beta/:all()" now degenerates to "beta/*"'s
        # pooled meaning (compendium 4.2b), so there is no value
        # dimension left to partition by -- only the group dimension
        # star traversal already provides inherently. Runs moved to be
        # direct children of "beta" (previously "beta/x"/"beta/y", a
        # 2-level fixture this 1-level pattern no longer matches at all).
        acme_1 = _make_run(
            tmp_path / "acme" / "beta", "2026-01-01_00-00-00", "acme-1", {}
        )
        acme_2 = _make_run(
            tmp_path / "acme" / "beta", "2026-01-02_00-00-00", "acme-2", {}
        )
        widgets_1 = _make_run(
            tmp_path / "widgets" / "beta",
            "2026-01-03_00-00-00",
            "widgets-1",
            {},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_1, acme_2], "widgets": [widgets_1]}
        )
        results = _finder(
            "$*.results.beta/:all():last()", str(tmp_path)
        ).query()
        assert sorted(results.uuids) == ["acme-2", "widgets-1"]

    def test_all_grouping_with_name_three_content_accessor_query_succeeds_one_group(
        self, tmp_path
    ):
        # REVISED 2026-09-28 (was: "...is_rejected", an unconditional
        # query()-time raise) -- converted to the deferred Rule 1
        # pattern, re-auditing against the exact trap the literal-root
        # ':path()'-retirement fix already caught once (see
        # _star_group_and_reduce()'s own docstring): each GROUP's own
        # pointer already reduces it to at most one candidate, so a
        # SINGLE matching group is not ambiguous at all -- query() (and
        # resolve(), once the underlying file exists) both succeed.
        # Zero-level fixture (run directly under the group's own home,
        # not a nested prefix) -- bare ':all()' only matches zero-level
        # runs, per the 2026-09-21 degenerate-grouping fix (see
        # test_all_grouping_with_name_three_field_accessor_is_poolable
        # just below, already using this same shape).
        acme_run = _make_run(
            tmp_path / "acme",
            "2026-01-01_00-00-00",
            "acme-run",
            {"invoices": "acme-invoices"},
        )
        _write_archive_manifest(tmp_path, "acme", [acme_run])
        results = _finder(
            "$*.results.:all():last().invoices:errors()", str(tmp_path)
        ).query()
        assert len(results.results) == 1
        assert results.ambiguous_content_read is False

    def test_all_grouping_with_name_three_content_accessor_resolve_raises_when_ambiguous(
        self, tmp_path
    ):
        # two DIFFERENT named-results groups, each with their own
        # "invoices" instance -- ':all():last()' reduces EACH group to
        # its own single winner (never ambiguous per-group), but
        # resolving ':errors()' content for both groups' winners AT ONCE
        # is still Rule 1 territory -- query() returns both (flagged),
        # resolve() refuses.
        acme_run = _make_run(
            tmp_path / "acme",
            "2026-01-01_00-00-00",
            "acme-run",
            {"invoices": "acme-invoices"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets",
            "2026-01-02_00-00-00",
            "widgets-run",
            {"invoices": "widgets-invoices"},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_run], "widgets": [widgets_run]}
        )
        results = _finder(
            "$*.results.:all():last().invoices:errors()", str(tmp_path)
        ).query()
        assert len(results.results) == 2
        assert results.ambiguous_content_read is True
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.results.:all():last().invoices:errors()", str(tmp_path)
            ).resolve()

    def test_all_grouping_with_name_three_field_accessor_is_poolable(
        self, tmp_path
    ):
        # David's own confirmed example: "$*.results.:all():last()
        # .invoices:uuid()" can find multiple runs, each contributing
        # its own "invoices" statement's uuid -- a list of zero or more
        # UUIDs, one per matched run that actually has that identity.
        # REVISED 2026-09-21: runs moved to zero-level (were 1-level
        # "acme/east" etc., which bare ':all()' no longer matches).
        acme_run = _make_run(
            tmp_path / "acme",
            "2026-01-01_00-00-00",
            "acme-run",
            {"invoices": "acme-invoices"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets",
            "2026-01-02_00-00-00",
            "widgets-run",
            {"invoices": "widgets-invoices"},
        )
        # gamma has no "invoices" statement at all -- contributes
        # nothing, not an error/None placeholder.
        gamma_run = _make_run(
            tmp_path / "gamma",
            "2026-01-03_00-00-00",
            "gamma-run",
            {"other": "gamma-other"},
        )
        _write_archive_manifest_multi(
            tmp_path,
            {"acme": [acme_run], "widgets": [widgets_run], "gamma": [gamma_run]},
        )
        results = _finder(
            "$*.results.:all():last().invoices:uuid()", str(tmp_path)
        ).resolve()
        assert sorted(r.data for r in results.results) == [
            "acme-invoices",
            "widgets-invoices",
        ]

    def test_all_at_both_name_one_and_name_three_multiplies_correctly(
        self, tmp_path
    ):
        # "$*.results.:all():last().:all():uuid()" -- :all() at name_one
        # selects one run per named-results group (degenerate/zero-level
        # per the 2026-09-21 fix, since there is no template value left
        # to partition by), :all() at name_three then pools every
        # instance WITHIN each of those -- a real two-level fan-out, not
        # a single flat list. Runs moved to zero-level (were 1-level
        # "acme/east" etc., which bare ':all()' no longer matches).
        acme_run = _make_run(
            tmp_path / "acme",
            "2026-01-01_00-00-00",
            "acme-run",
            {"invoices": "acme-invoices", "receipts": "acme-receipts"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets",
            "2026-01-02_00-00-00",
            "widgets-run",
            {"invoices": "widgets-invoices"},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_run], "widgets": [widgets_run]}
        )
        results = _finder(
            "$*.results.:all():last().:all():uuid()", str(tmp_path)
        ).resolve()
        assert sorted(r.data for r in results.results) == [
            "acme-invoices",
            "acme-receipts",
            "widgets-invoices",
        ]

    def test_flatten_with_a_specific_name_three_identity_works(self, tmp_path):
        acme_deep = _make_run(
            tmp_path / "acme" / "customers" / "2025",
            "2026-01-01_00-00-00",
            "acme-deep",
            {"invoices": "acme-invoices"},
        )
        _write_archive_manifest(tmp_path, "acme", [acme_deep])
        results = _finder(
            "$*.results.:flatten():last().invoices", str(tmp_path)
        ).query()
        assert results.results[0].uuid == "acme-invoices"


class TestStarTraversalGroups:
    # BUILT 2026-10-18 -- closes the one remaining unconditional
    # rejection _query_star_traversal had, confirmed as a real gap via
    # normative_reference_examples.txt's own "$*.results.:groups():
    # named_file_name(\"orders\"):first()" worked example ("select the
    # first run for each template for runs having the named-file name
    # orders"). Mirrors the literal-root query()'s own bare/prefixed
    # ':groups()' branches (compendium 4.2/4.2b: the n-level form of
    # ':all()', grouping by EVERY segment beyond a fixed prefix, any
    # depth) -- just partitioned PER named-results group first (the one
    # dimension star traversal always adds), then by each run's own
    # relative-path tuple within that group.
    def test_bare_groups_with_pointer_partitions_by_full_template_any_depth(
        self, tmp_path
    ):
        # two runs sharing the SAME template ("beta/x") merge into one
        # partition (pointer picks the latest); a run one level up
        # ("beta/y") does not merge with them despite being in the same
        # named-results group; a run in a DIFFERENT group ("gamma/x")
        # does not merge with "beta/x" despite sharing a trailing
        # segment -- proves the key is the group AND the full tuple,
        # not just the last segment (see _group_key's own docstring).
        acme_beta_x_1 = _make_run(
            tmp_path / "acme" / "beta" / "x",
            "2026-01-01_00-00-00",
            "acme-beta-x-1",
            {},
        )
        acme_beta_x_2 = _make_run(
            tmp_path / "acme" / "beta" / "x",
            "2026-01-02_00-00-00",
            "acme-beta-x-2",
            {},
        )
        acme_beta_y = _make_run(
            tmp_path / "acme" / "beta" / "y",
            "2026-01-03_00-00-00",
            "acme-beta-y",
            {},
        )
        gamma_x = _make_run(
            tmp_path / "gamma" / "x", "2026-01-04_00-00-00", "gamma-x", {}
        )
        _write_archive_manifest_multi(
            tmp_path,
            {
                "acme": [acme_beta_x_1, acme_beta_x_2, acme_beta_y],
                "gamma": [gamma_x],
            },
        )
        results = _finder("$*.results.:groups():last()", str(tmp_path)).query()
        assert sorted(results.uuids) == [
            "acme-beta-x-2",
            "acme-beta-y",
            "gamma-x",
        ]

    def test_bare_groups_with_no_pointer_returns_every_run_unreduced(
        self, tmp_path
    ):
        # a pointer is optional everywhere in star traversal (settled
        # 2026-08-19) -- absence means every matched run, not just one
        # winner per partition.
        acme_beta_x_1 = _make_run(
            tmp_path / "acme" / "beta" / "x",
            "2026-01-01_00-00-00",
            "acme-beta-x-1",
            {},
        )
        acme_beta_x_2 = _make_run(
            tmp_path / "acme" / "beta" / "x",
            "2026-01-02_00-00-00",
            "acme-beta-x-2",
            {},
        )
        _write_archive_manifest(
            tmp_path, "acme", [acme_beta_x_1, acme_beta_x_2]
        )
        results = _finder("$*.results.:groups()", str(tmp_path)).query()
        assert sorted(results.uuids) == ["acme-beta-x-1", "acme-beta-x-2"]

    def test_prefixed_groups_partitions_beyond_the_fixed_prefix(
        self, tmp_path
    ):
        # "beta/:groups():last()" -- same partitioning as the bare
        # shape, but only among runs matching the literal "beta" prefix
        # first; "gamma/x" never even reaches grouping since it fails
        # the prefix match outright, unlike the bare test above where
        # it formed its own separate partition.
        acme_beta_x_1 = _make_run(
            tmp_path / "acme" / "beta" / "x",
            "2026-01-01_00-00-00",
            "acme-beta-x-1",
            {},
        )
        acme_beta_x_2 = _make_run(
            tmp_path / "acme" / "beta" / "x",
            "2026-01-02_00-00-00",
            "acme-beta-x-2",
            {},
        )
        acme_beta_y = _make_run(
            tmp_path / "acme" / "beta" / "y",
            "2026-01-03_00-00-00",
            "acme-beta-y",
            {},
        )
        gamma_x = _make_run(
            tmp_path / "gamma" / "x", "2026-01-04_00-00-00", "gamma-x", {}
        )
        _write_archive_manifest_multi(
            tmp_path,
            {
                "acme": [acme_beta_x_1, acme_beta_x_2, acme_beta_y],
                "gamma": [gamma_x],
            },
        )
        results = _finder(
            "$*.results.beta/:groups():last()", str(tmp_path)
        ).query()
        assert sorted(results.uuids) == ["acme-beta-x-2", "acme-beta-y"]

    def test_prefixed_groups_rejects_an_argument(self, tmp_path):
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.results.beta/:groups(1):last()", str(tmp_path)
            ).query()

    def test_bare_and_prefixed_groups_combine_with_two_grouping_markers_illegally(
        self, two_group_archive
    ):
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.results.:groups():all():last()", two_group_archive
            ).query()

    def test_groups_combined_with_named_file_name_filter_matches_the_normative_example(
        self, tmp_path
    ):
        # the EXACT normative_reference_examples.txt worked example
        # ("select the first run for each template for runs having the
        # named-file name orders"): "$*.results.:groups():named_file_
        # name(\"orders\"):first()" -- the layered gap this whole
        # branch and NamedFileName3's own ARG_TYPES widening close
        # together. Two groups each have a "beta" template with TWO
        # runs sharing that template but different named_file_name
        # values -- proves the filter is actually reading
        # named_file_name per-run, not just piggybacking on the
        # template/group key, and that ':first()' picks the earliest
        # SURVIVING run, not just the earliest in the template.
        acme_orders_1 = _make_run(
            tmp_path / "acme" / "beta", "2026-01-01_00-00-00", "acme-orders-1", {}
        )
        acme_orders_2 = _make_run(
            tmp_path / "acme" / "beta", "2026-01-02_00-00-00", "acme-orders-2", {}
        )
        acme_invoices = _make_run(
            tmp_path / "acme" / "beta",
            "2026-01-03_00-00-00",
            "acme-invoices",
            {},
        )
        widgets_orders = _make_run(
            tmp_path / "widgets" / "beta",
            "2026-01-04_00-00-00",
            "widgets-orders",
            {},
        )
        for run_home, run_uuid, name in (
            (acme_orders_1, "acme-orders-1", "orders"),
            (acme_orders_2, "acme-orders-2", "orders"),
            (acme_invoices, "acme-invoices", "invoices"),
            (widgets_orders, "widgets-orders", "orders"),
        ):
            _write_json(
                Path(run_home) / "manifest.json",
                {"run_uuid": run_uuid, "named_file_name": name},
            )
        _write_archive_manifest_multi(
            tmp_path,
            {
                "acme": [acme_orders_1, acme_orders_2, acme_invoices],
                "widgets": [widgets_orders],
            },
        )
        results = _finder(
            '$*.results.:groups():named_file_name("orders"):first()',
            str(tmp_path),
        ).query()
        assert sorted(results.uuids) == ["acme-orders-1", "widgets-orders"]


class TestStarTraversalPointerIsOptional:
    # a pointer is optional in EVERY '*' traversal shape now (settled
    # 2026-08-19) -- absence means every matched run comes back,
    # unreduced, mirroring RESULTS' own literal-root precedent (no
    # shape there ever required one) and FilesReferenceFinder3's star
    # traversal (also never requires one, in any of its four modes).
    # CsvpathsReferenceFinder3's own narrower precedent (pointer
    # required in POOL/flatten mode, optional only in GROUP/':all()')
    # was deliberately NOT copied -- confirmed via reading its code
    # that it is the outlier among the three, not the target.
    def test_zero_level_bare_with_no_pointer_lists_every_flat_run(
        self, tmp_path
    ):
        acme_run = _make_run(
            tmp_path / "acme", "2026-01-01_00-00-00", "acme-run", {}
        )
        widgets_run = _make_run(
            tmp_path / "widgets", "2026-01-02_00-00-00", "widgets-run", {}
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_run], "widgets": [widgets_run]}
        )
        # ':home()' is the only legal spelling of "bare, zero-level,
        # nothing else" -- a totally empty name_one ("$*.results.") is
        # not valid grammar (confirmed live: Lark rejects it outright).
        results = _finder("$*.results.:home()", str(tmp_path)).query()
        assert sorted(results.uuids) == ["acme-run", "widgets-run"]

    def test_prefixed_flatten_with_no_pointer_lists_everything_beyond_prefix(
        self, tmp_path
    ):
        acme_run = _make_run(
            tmp_path / "acme" / "beta" / "x",
            "2026-01-01_00-00-00",
            "acme-run",
            {},
        )
        widgets_run = _make_run(
            tmp_path / "widgets" / "beta" / "y" / "z",
            "2026-01-02_00-00-00",
            "widgets-run",
            {},
        )
        other_run = _make_run(
            tmp_path / "widgets" / "gamma", "2026-01-03_00-00-00", "other-run", {}
        )
        _write_archive_manifest_multi(
            tmp_path,
            {"acme": [acme_run], "widgets": [widgets_run, other_run]},
        )
        results = _finder("$*.results.beta/:flatten()", str(tmp_path)).query()
        assert sorted(results.uuids) == ["acme-run", "widgets-run"]

    def test_plain_literal_path_with_no_pointer_lists_everything_matching(
        self, tmp_path
    ):
        acme_run = _make_run(
            tmp_path / "acme" / "customers" / "2025",
            "2026-01-01_00-00-00",
            "acme-run",
            {},
        )
        widgets_run = _make_run(
            tmp_path / "widgets" / "customers" / "2025",
            "2026-01-02_00-00-00",
            "widgets-run",
            {},
        )
        other_run = _make_run(
            tmp_path / "widgets" / "customers" / "2026",
            "2026-01-03_00-00-00",
            "other-run",
            {},
        )
        _write_archive_manifest_multi(
            tmp_path,
            {"acme": [acme_run], "widgets": [widgets_run, other_run]},
        )
        results = _finder(
            "$*.results.customers/2025", str(tmp_path)
        ).query()
        assert sorted(results.uuids) == ["acme-run", "widgets-run"]

    def test_no_pointer_pool_with_content_accessor_and_multiple_runs_is_rejected(
        self, tmp_path
    ):
        # query() itself succeeds now (moved 2026-08-27, see the
        # "'*'-traversal content-accessor guards" bucket-list entry --
        # this is the one item explicitly marked a safe, count-based
        # conversion candidate) -- only resolve() raises, once something
        # actually tries to read more than one run's own content at once.
        acme_run = _make_run(
            tmp_path / "acme",
            "2026-01-01_00-00-00",
            "acme-run",
            {"invoices": "acme-invoices"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets",
            "2026-01-02_00-00-00",
            "widgets-run",
            {"invoices": "widgets-invoices"},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_run], "widgets": [widgets_run]}
        )
        finder = _finder("$*.results.:home().invoices:errors()", str(tmp_path))
        assert len(finder.query()) > 1
        with pytest.raises(ReferenceException3):
            finder.resolve()

    def test_no_pointer_pool_with_content_accessor_and_one_run_still_works(
        self, tmp_path
    ):
        # the positive counterpart to the test above -- exactly one run
        # matches (a single named-results group here, rather than a
        # pointer picking one out of several), so reading its own
        # content is unambiguous and must not raise.
        acme_run = _make_run(
            tmp_path / "acme",
            "2026-01-01_00-00-00",
            "acme-run",
            {"invoices": "acme-invoices"},
        )
        _write_archive_manifest_multi(tmp_path, {"acme": [acme_run]})
        errors = [{"error": "bad row", "line": 3}]
        with open(
            os.path.join(acme_run, "invoices", "errors.json"), "w"
        ) as f:
            json.dump(errors, f)
        results = _finder(
            "$*.results.:home().invoices:errors()", str(tmp_path)
        ).resolve()
        assert len(results) == 1
        assert results.results[0].data == errors

    def test_no_pointer_with_a_field_accessor_is_poolable(self, tmp_path):
        acme_run = _make_run(
            tmp_path / "acme", "2026-01-01_00-00-00", "acme-run", {}
        )
        _write_json(
            Path(acme_run) / "manifest.json",
            {"run_uuid": "acme-run", "named_paths_name": "acme"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets", "2026-01-02_00-00-00", "widgets-run", {}
        )
        _write_json(
            Path(widgets_run) / "manifest.json",
            {"run_uuid": "widgets-run", "named_paths_name": "widgets"},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_run], "widgets": [widgets_run]}
        )
        results = _finder(
            "$*.results.:named_paths_name()", str(tmp_path)
        ).resolve()
        assert sorted((r.uuid, r.data) for r in results.results) == [
            ("acme-run", "acme"),
            ("widgets-run", "widgets"),
        ]


class TestPositionEnforcement:
    # ReferenceFinder3._check_position() -- added 2026-08-14, the
    # enforced replacement for the scattered "is this recognized"
    # guards each Finder used to hand-write on its own. RESULTS is the
    # third and last Finder retrofitted to call it, after CSVPATHS and
    # FILES.
    def test_an_unregistered_for_this_datatype_function_on_name_one_is_rejected(
        self, acme_archive
    ):
        # the actual bug this closes: name_one's own handling only ever
        # looked for SPECIFIC recognized names (all/flatten/groups/from/
        # to/manifest/a field function) -- it never rejected an
        # unrecognized extra riding alongside a legitimate pointer.
        # Confirmed via direct testing before this fix that
        # ":last():webhooks()" (a function registered for a DIFFERENT
        # datatype entirely, not even results-relevant) silently
        # no-opped instead of raising.
        with pytest.raises(ReferenceException3):
            _finder("$acme.results.customers/2025:last():webhooks()", acme_archive).query()

    def test_a_legal_function_is_unaffected(self, acme_archive):
        # sanity check that the new check does not over-reject.
        results = _finder("$acme.results.customers/2025:last()", acme_archive).query()
        assert results.results[0].uuid == "run2-uuid"

    def test_star_traversal_groups_with_a_pointer_now_works(self, two_group_archive):
        # RENAMED/REWRITTEN 2026-10-18 (was:
        # "...rejects_groups_not_just_all_flatten_manifest" -- at the time
        # ':groups()' had no explicit handling in '*' traversal at all and
        # fell into the generic non-pointer rejection; this test proved
        # that rejection actually caught it, not just "all"/"flatten"/
        # "manifest"). ':groups()' got its own '*'-traversal support this
        # same day (normative_reference_examples.txt's own worked
        # example), so the correct assertion is now the opposite: one
        # winner PER named-results group (acme's own latest run, not
        # pooled against widgets' single run), proving a pointer composes
        # with grouping instead of being silently dropped.
        results = _finder("$*.results.:last():groups()", two_group_archive).query()
        assert sorted(results.uuids) == ["acme-run2-uuid", "widgets-run1-uuid"]

    def test_star_traversal_rejects_a_range_function_too(self, two_group_archive):
        with pytest.raises(ReferenceException3):
            _finder("$*.results.:last():from(1)", two_group_archive).query()

    def test_star_traversal_bare_pointer_is_unaffected(self, two_group_archive):
        results = _finder("$*.results.:last()", two_group_archive).query()
        assert results.results[0].uuid == "widgets-run1-uuid"


class TestScopeLimits:
    def test_manifest_combined_with_traversal_now_works(self, tmp_path):
        # previously a real, open gap -- fixed 2026-08-26. Once
        # _query_star_traversal's own combining-guard exempted
        # ':manifest()' (alongside the field accessor/':all()'/
        # ':flatten()' exemptions already in place), a genuine
        # traversal-selected run also carries a real, non-None uuid --
        # identical in shape to what Rule 1a/1b's own bare-pointer-plus-
        # manifest result carries. _extract_data() now disambiguates by
        # comparing result.path against the archive ledger's own known,
        # fixed path (manifest.json directly under the archive root)
        # rather than checking uuid presence, so this correctly reads
        # each matched group's own run manifest.json, not the ledger.
        # REVISED 2026-09-21: ':all()' now degenerates to zero-level
        # (compendium 4.2b) -- this fixture is zero-level accordingly
        # (previously deliberately 1-level, back when ':all()' required
        # exactly one level of nesting; two_group_archive would now work
        # here too, but this stays self-contained to keep the uuids
        # matching the assertions below unambiguous).
        acme_run = _make_run(
            tmp_path / "acme", "2026-01-01_00-00-00", "acme-east", {}
        )
        widgets_run = _make_run(
            tmp_path / "widgets", "2026-01-02_00-00-00", "widgets-east", {}
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_run], "widgets": [widgets_run]}
        )
        results = _finder(
            "$*.results.:all():last():manifest()", str(tmp_path)
        ).resolve()
        assert len(results.results) == 2
        data_by_uuid = {r.uuid: r.data for r in results.results}
        assert data_by_uuid == {
            "acme-east": {"run_uuid": "acme-east"},
            "widgets-east": {"run_uuid": "widgets-east"},
        }

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

    def test_star_body_on_name_three_is_the_same_wildcard_as_all(
        self, acme_archive
    ):
        # compendium 4.2b/4.3a: ":all() devolves to the same meaning as
        # '*' in name_three" -- normative examples 393-404 declare them
        # flatly equivalent. Relaxed 2026-10-17 (was: an unconditional
        # rejection here) alongside :count()'s own worked example
        # (normative examples 489-491), which needed this to even
        # parse. run1 (selected by :first()) has two instances --
        # "*" pools both, same as ":all()" would.
        finder = _finder("$acme.results.customers/2025:first().*", acme_archive)
        results = finder.query()
        assert len(results.results) == 2

    def test_star_body_combined_with_all_raises(self, acme_archive):
        # both are the same wildcard -- combining them is "two wildcards
        # in name_three," still illegal.
        finder = _finder(
            "$acme.results.customers/2025:first().*:all()", acme_archive
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_truly_unregistered_function_on_name_three_raises(self, acme_archive):
        finder = _finder(
            "$acme.results.customers/2025:first().:quarter()", acme_archive
        )
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_bare_accessor_implies_star_and_pools_every_instance(
        self, acme_archive
    ):
        # compendium 3.19b: "When name_three is solely one or more
        # functions, a '*' is implied, in the same way as in name_one."
        # :data() is registered and meaningful for results, but does not
        # itself select which instance it applies to -- it used to be an
        # unconditional rejection without an explicit identity/:all()
        # riding alongside it; relaxed 2026-10-17 (the same worked
        # example as test_star_body_on_name_three_is_the_same_wildcard_
        # as_all above) to imply '*' instead, pooling every instance in
        # the run, same as an explicit ":all():data()" would.
        finder = _finder(
            "$acme.results.customers/2025:first().:data()", acme_archive
        )
        results = finder.query()
        assert len(results.results) == 2
        assert results.ambiguous_content_read is True
        with pytest.raises(ReferenceException3):
            finder.resolve()

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


class TestClockFunctionInPathSegments:
    # see test_files_reference_finder_3.py's own
    # TestClockFunctionInPathSegments for the full design (
    # ReferenceFinder3._compile_path_pattern()/_resolve_value(), shared
    # by FILES and RESULTS). Proven here against the real current year,
    # not a mocked clock.
    def test_bare_clock_function_as_a_path_segment(self, tmp_path):
        year = str(daut.now().year)
        base = tmp_path / "acme" / "customers" / year
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        _write_archive_manifest(tmp_path, "acme", [str(run_dir)])
        results = _finder(
            "$acme.results.customers/:year():first()", str(tmp_path)
        ).query()
        assert results.uuids == ["run1-uuid"]

    def test_interpolated_name_containing_a_clock_function(self, tmp_path):
        year = str(daut.now().year)
        base = tmp_path / "acme" / f"orders-{year}"
        run_dir = base / "2026-01-01_00-00-00"
        _write_json(run_dir / "manifest.json", {"run_uuid": "run1-uuid"})
        _write_archive_manifest(tmp_path, "acme", [str(run_dir)])
        results = _finder(
            '$acme.results.:name("orders-{:year()}"):first()', str(tmp_path)
        ).query()
        assert results.uuids == ["run1-uuid"]


class TestLog:
    # compendium 5.16(b) -- see test_csvpaths_reference_finder_3.py's
    # own TestLog for the full scenario set (shared ABC mechanism,
    # ReferenceFinder3._bare_log_call()/_query_log_call()/
    # _read_log_file()); this just confirms it composes correctly with
    # ResultsReferenceFinder3's own query()/_extract_data() dispatch
    # too, and that it takes priority over the archive-ledger '*'
    # handling that would otherwise apply to a bare '*' root_major.
    def test_bare_log_resolves_the_whole_file(self, tmp_path, acme_archive):
        log_path = tmp_path / "csvpath.log"
        log_path.write_text("line1\nline2\n")
        results = _finder(
            "$*.results.:log()", acme_archive, log_file=str(log_path)
        ).resolve()
        assert results.results[0].data == "line1\nline2\n"


class TestRegexRootMajor:
    # :regex() at root_major -- added 2026-08-27, the crowded-namespace
    # motivating case (David): "acme_group"/"abba_group" are more
    # manageable when a reference can target "/abba_.*/" directly.
    # Reuses ResultsReferenceFinder3's own '*'-traversal machinery, just
    # pre-filtered by pattern before _discover_run_homes() enumerates.
    @pytest.fixture
    def regex_archive(self, tmp_path):
        acme_run = _make_run(
            tmp_path / "acme_group", "2026-01-01_00-00-00", "acme-run-uuid", {}
        )
        abba_run = _make_run(
            tmp_path / "abba_group", "2026-01-02_00-00-00", "abba-run-uuid", {}
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme_group": [acme_run], "abba_group": [abba_run]}
        )
        return str(tmp_path)

    def test_regex_filters_to_matching_groups(self, regex_archive):
        results = _finder("$:regex(/^abba_.*/).results.:last()", regex_archive).query()
        assert results.uuids == ["abba-run-uuid"]

    def test_regex_excludes_non_matching_groups(self, regex_archive):
        results = _finder("$:regex(/^abba_.*/).results.:last()", regex_archive).query()
        assert "acme-run-uuid" not in results.uuids

    def test_regex_with_no_matches_gives_empty(self, regex_archive):
        results = _finder("$:regex(/^zzz_.*/).results.:last()", regex_archive).query()
        assert results.uuids == []

    def test_wrong_root_major_function_is_rejected(self, regex_archive):
        with pytest.raises(ReferenceException3):
            _finder('$:having("x").results.:last()', regex_archive).query()

    def test_regex_accepts_a_registered_variable(self, regex_archive):
        results = _finder(
            "$:regex(@aregex).results.:last()",
            regex_archive,
            variables={"aregex": "^abba_.*"},
        ).query()
        assert results.uuids == ["abba-run-uuid"]
