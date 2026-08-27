import json
import os
from pathlib import Path

import pytest

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.results_reference_finder_3 import ResultsReferenceFinder3
from csvpath.util.date_util import DateUtility as daut

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
    reference: str, archive: str, log_file: str | None = None
) -> ResultsReferenceFinder3:
    csvpaths = _FakeCsvPaths(archive, log_file=log_file)
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
            f"{acme_archive}/acme/customers/2025/2026-01-01_00-00-00"
        ]


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
    # alone (no ':all()') means zero-level only -- direct children of
    # the group's own root -- settled 2026-08-10; see :flatten() for
    # the any-depth case this used to cover. A bare ':all()' is
    # unaffected: still every run for the group, any depth.
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
        # ':all()' now requires exactly one level (settled 2026-08-11,
        # same restriction '*' has) -- ':flatten()' is the right tool
        # for "every run regardless of depth", including flat ones.
        results = _finder("$flat.results.:flatten()", flat_archive).query()
        assert set(results.uuids) == {"run1-uuid", "run2-uuid"}

    def test_bare_all_excludes_flat_runs(self, flat_archive):
        # both of flat_archive's runs are zero-level (direct children) --
        # ':all()' requires exactly one level, so it finds neither.
        results = _finder("$flat.results.:all()", flat_archive).query()
        assert results.uuids == []

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

    def test_all_grouping_partitions_by_composite_group_and_template_key(
        self, tmp_path
    ):
        # closes the ':all()' meaning-collision (settled 2026-08-19 with
        # David via a worked example -- see "THE ':all()' MEANING
        # COLLISION AT STAR TRAVERSAL" in references_notes/notes/
        # normative_reference_examples.txt) -- mirrors
        # FilesReferenceFinder3's own already-built ':all()' star-
        # traversal precedent: partition by the COMPOSITE (group,
        # template-value) key, not group alone or template alone.
        # acme has two "east" runs and one "west" run; widgets has one
        # "east" run -- "east" is reused across BOTH groups on purpose,
        # the crux of the ambiguity this fixture proves is resolved
        # correctly (neither collapsed into the other).
        acme_east_1 = _make_run(
            tmp_path / "acme" / "east", "2026-01-01_00-00-00", "acme-east-1", {}
        )
        acme_east_2 = _make_run(
            tmp_path / "acme" / "east", "2026-01-03_00-00-00", "acme-east-2", {}
        )
        acme_west_1 = _make_run(
            tmp_path / "acme" / "west", "2026-01-02_00-00-00", "acme-west-1", {}
        )
        widgets_east_1 = _make_run(
            tmp_path / "widgets" / "east",
            "2026-01-04_00-00-00",
            "widgets-east-1",
            {},
        )
        _write_archive_manifest_multi(
            tmp_path,
            {
                "acme": [acme_east_1, acme_east_2, acme_west_1],
                "widgets": [widgets_east_1],
            },
        )
        results = _finder("$*.results.:all():last()", str(tmp_path)).query()
        # 3 results, not 2 -- pooling by template value alone would have
        # conflated acme's and widgets' "east" runs into one group
        # (giving widgets-east-1, the true latest, and losing acme-
        # east-2 entirely); grouping by named-results-group alone would
        # have lost the east/west distinction within acme (giving
        # acme-east-2 as acme's one "last", never surfacing acme-west-1
        # at all).
        assert sorted(results.uuids) == [
            "acme-east-2",
            "acme-west-1",
            "widgets-east-1",
        ]

    def test_all_combined_with_flatten_is_rejected(self, two_group_archive):
        # each is its own depth/grouping choice -- same mutual-exclusion
        # rule the literal-root case already enforces.
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.results.:all():flatten():last()", two_group_archive
            ).query()

    def test_all_combined_with_a_field_accessor_also_works(self, tmp_path):
        acme_run = _make_run(
            tmp_path / "acme" / "east", "2026-01-01_00-00-00", "acme-east", {}
        )
        _write_json(
            Path(acme_run) / "manifest.json",
            {"run_uuid": "acme-east", "named_paths_name": "acme"},
        )
        _write_archive_manifest(tmp_path, "acme", [acme_run])
        results = _finder(
            "$*.results.:all():last():named_paths_name()", str(tmp_path)
        ).resolve()
        assert len(results.results) == 1
        assert results.results[0].uuid == "acme-east"
        assert results.results[0].data == "acme"


class TestAllGrouping:
    # ':all()' and '*' stay depth peers (exactly one level) --
    # ':all()' additionally groups by whatever value actually occupies
    # that one wildcarded position, unlike '*' (which pools). Settled
    # 2026-08-10, directly from David's own example: three different
    # one-level templates, each nesting runs one level deep via a
    # different substitution source, still group correctly by whatever
    # directory each run actually landed in -- not by which template
    # produced it.
    def test_davids_three_templates_example(self, tmp_path):
        base = tmp_path / "alpha"
        zero_run1 = _make_run(base / "zero", "2026-01-01_00-00-00", "zero-1", {})
        zero_run2 = _make_run(base / "zero", "2026-01-02_00-00-00", "zero-2", {})
        one_run1 = _make_run(base / "one", "2026-01-03_00-00-00", "one-1", {})
        one_run2 = _make_run(base / "one", "2026-01-04_00-00-00", "one-2", {})
        two_run1 = _make_run(base / "two", "2026-01-05_00-00-00", "two-1", {})
        two_run2 = _make_run(base / "two", "2026-01-06_00-00-00", "two-2", {})
        _write_archive_manifest(
            tmp_path,
            "alpha",
            [zero_run1, zero_run2, one_run1, one_run2, two_run1, two_run2],
        )
        results = _finder("$alpha.results.:all():last()", str(tmp_path)).query()
        assert len(results.results) == 3
        assert set(results.uuids) == {"zero-2", "one-2", "two-2"}

    def test_all_with_first_gives_each_groups_earliest(self, tmp_path):
        base = tmp_path / "alpha"
        zero_run1 = _make_run(base / "zero", "2026-01-01_00-00-00", "zero-1", {})
        zero_run2 = _make_run(base / "zero", "2026-01-02_00-00-00", "zero-2", {})
        one_run1 = _make_run(base / "one", "2026-01-03_00-00-00", "one-1", {})
        _write_archive_manifest(tmp_path, "alpha", [zero_run1, zero_run2, one_run1])
        results = _finder("$alpha.results.:all():first()", str(tmp_path)).query()
        assert set(results.uuids) == {"zero-1", "one-1"}

    def test_all_with_no_pointer_still_requires_exactly_one_level(
        self, tmp_path
    ):
        # settled 2026-08-11: ':all()' stays '*'s one-level peer whether
        # or not a pointer follows it -- the flat run is excluded here,
        # same as it would be for "*" (illegal on its own, but this is
        # the same restriction), unreduced since there is no pointer.
        base = tmp_path / "alpha"
        zero_run = _make_run(base / "zero", "2026-01-01_00-00-00", "zero-1", {})
        flat_run = _make_run(base, "2026-01-02_00-00-00", "flat-1", {})
        _write_archive_manifest(tmp_path, "alpha", [zero_run, flat_run])
        results = _finder("$alpha.results.:all()", str(tmp_path)).query()
        assert results.uuids == ["zero-1"]

    def test_prefixed_all_groups_by_the_next_level(self, tmp_path):
        base = tmp_path / "acme"
        x_run1 = _make_run(base / "beta" / "x", "2026-01-01_00-00-00", "x-1", {})
        x_run2 = _make_run(base / "beta" / "x", "2026-01-02_00-00-00", "x-2", {})
        y_run1 = _make_run(base / "beta" / "y", "2026-01-03_00-00-00", "y-1", {})
        other_run = _make_run(base / "gamma" / "z", "2026-01-04_00-00-00", "z-1", {})
        _write_archive_manifest(
            tmp_path, "acme", [x_run1, x_run2, y_run1, other_run]
        )
        results = _finder(
            "$acme.results.beta/:all():last()", str(tmp_path)
        ).query()
        assert len(results.results) == 2
        assert set(results.uuids) == {"x-2", "y-1"}

    def test_all_grouping_combined_with_manifest_is_not_yet_supported(
        self, tmp_path
    ):
        base = tmp_path / "alpha"
        run1 = _make_run(base / "zero", "2026-01-01_00-00-00", "zero-1", {})
        _write_archive_manifest(tmp_path, "alpha", [run1])
        with pytest.raises(ReferenceException3):
            _finder(
                "$alpha.results.:all():last():manifest()", str(tmp_path)
            ).query()


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
        self, five_runs
    ):
        with pytest.raises(ReferenceException3):
            _finder("$acme.results.:all():from(1):last()", five_runs).query()

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
        # status/method/hostname/username/time_completed/manifest_path/
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
        assert resolve("hostname") == "box1"
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

    def test_bare_all_with_no_pointer_gives_empty_on_flat_runs(
        self, two_group_archive
    ):
        # a pointer is optional everywhere in star traversal now
        # (settled 2026-08-19, matching RESULTS' own literal-root
        # precedent and FilesReferenceFinder3, neither of which ever
        # required one) -- absence means "every matched run, unreduced"
        # rather than an error. two_group_archive's runs are all flat
        # (zero-level), so ':all()' (which requires exactly one level)
        # correctly matches nothing here -- empty, not a raise.
        results = _finder("$*.results.:all()", two_group_archive).query()
        assert results.results == []

    def test_bare_all_with_no_pointer_lists_every_one_level_run(
        self, tmp_path
    ):
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
        # every one-level run across every group, unreduced -- NOT one
        # per (group, template) partition, since grouping only matters
        # once there is a pointer to reduce a partition to one.
        assert sorted(results.uuids) == ["acme-east", "acme-west", "widgets-east"]

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
        # but a genuinely unsupported extra (e.g. :groups()) riding
        # alongside it is still rejected -- proves the exemption is
        # narrowly scoped to the one matched field call, not "anything
        # goes once one field accessor is present".
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.results.:last():named_paths_name():groups()",
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

    def test_prefixed_all_partitions_by_composite_key_beyond_prefix(
        self, tmp_path
    ):
        acme_x = _make_run(
            tmp_path / "acme" / "beta" / "x", "2026-01-01_00-00-00", "acme-x", {}
        )
        acme_y = _make_run(
            tmp_path / "acme" / "beta" / "y", "2026-01-02_00-00-00", "acme-y", {}
        )
        widgets_x = _make_run(
            tmp_path / "widgets" / "beta" / "x",
            "2026-01-03_00-00-00",
            "widgets-x",
            {},
        )
        _write_archive_manifest_multi(
            tmp_path, {"acme": [acme_x, acme_y], "widgets": [widgets_x]}
        )
        # "x" is reused by both groups on purpose -- same crux as the
        # bare ':all()' meaning-collision fixture, proving the prefixed
        # shape ALSO partitions by (group, value), not value alone.
        results = _finder(
            "$*.results.beta/:all():last()", str(tmp_path)
        ).query()
        assert sorted(results.uuids) == ["acme-x", "acme-y", "widgets-x"]

    def test_all_grouping_with_name_three_content_accessor_is_rejected(
        self, tmp_path
    ):
        acme_run = _make_run(
            tmp_path / "acme" / "east",
            "2026-01-01_00-00-00",
            "acme-run",
            {"invoices": "acme-invoices"},
        )
        _write_archive_manifest(tmp_path, "acme", [acme_run])
        with pytest.raises(ReferenceException3):
            _finder(
                "$*.results.:all():last().invoices:errors()", str(tmp_path)
            ).query()

    def test_all_grouping_with_name_three_field_accessor_is_poolable(
        self, tmp_path
    ):
        # David's own confirmed example: "$*.results.:all():last()
        # .invoices:uuid()" can find multiple runs, each contributing
        # its own "invoices" statement's uuid -- a list of zero or more
        # UUIDs, one per matched run that actually has that identity.
        acme_run = _make_run(
            tmp_path / "acme" / "east",
            "2026-01-01_00-00-00",
            "acme-run",
            {"invoices": "acme-invoices"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets" / "east",
            "2026-01-02_00-00-00",
            "widgets-run",
            {"invoices": "widgets-invoices"},
        )
        # gamma has no "invoices" statement at all -- contributes
        # nothing, not an error/None placeholder.
        gamma_run = _make_run(
            tmp_path / "gamma" / "east",
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
        # selects one run per (group, template) partition, :all() at
        # name_three then pools every instance WITHIN each of those --
        # a real two-level fan-out, not a single flat list.
        acme_run = _make_run(
            tmp_path / "acme" / "east",
            "2026-01-01_00-00-00",
            "acme-run",
            {"invoices": "acme-invoices", "receipts": "acme-receipts"},
        )
        widgets_run = _make_run(
            tmp_path / "widgets" / "east",
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

    def test_star_traversal_rejects_groups_not_just_all_flatten_manifest(
        self, two_group_archive
    ):
        # the old star-traversal guard only named-checked
        # "all"/"flatten"/"manifest" plus a separate field-function
        # check -- neither caught ':groups()', confirmed via direct
        # testing before this fix that it silently no-opped instead of
        # raising. Replaced with one check covering everything that is
        # not a bare pointer, matching the method's own documented
        # restriction.
        with pytest.raises(ReferenceException3):
            _finder("$*.results.:last():groups()", two_group_archive).query()

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
        # ':all()' needs exactly one level of nesting -- two_group_
        # archive's runs are deliberately flat (zero-level), so this
        # uses its own one-level fixture instead, mirroring
        # test_all_combined_with_a_field_accessor_also_works above.
        acme_run = _make_run(
            tmp_path / "acme" / "east", "2026-01-01_00-00-00", "acme-east", {}
        )
        widgets_run = _make_run(
            tmp_path / "widgets" / "east", "2026-01-02_00-00-00", "widgets-east", {}
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
