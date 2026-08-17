import json
import os

import pytest

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_expression_3 import ReferenceExpression3
from csvpath.references.reference_results_3 import ReferenceResult3, ReferenceResults3


#
# ---- pure operation-logic tests (synthetic ReferenceResults3, no real
# Finders) -- fast, and exercise the set-operation semantics themselves in
# isolation from any parsing/dispatch concerns.
#
class TestUnion:
    def test_concatenates_both_sides(self):
        left = ReferenceResults3(
            results=[ReferenceResult3(path="p1", uuid="u1", data="a")]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="p2", uuid="u2", data="b")]
        )
        result = ReferenceExpression3._union(left, right)
        assert result.files == ["p1", "p2"]

    def test_collapses_true_duplicates(self):
        item = ReferenceResult3(path="p1", uuid="u1", data="a")
        left = ReferenceResults3(results=[item])
        right = ReferenceResults3(
            results=[ReferenceResult3(path="p1", uuid="u1", data="a")]
        )
        result = ReferenceExpression3._union(left, right)
        assert len(result) == 1

    def test_does_not_collapse_items_that_merely_share_a_key(self):
        # UNION never looks at .data as a key at all -- two DIFFERENT
        # items (different path/uuid) with the same .data value both
        # survive, same as if .data were not even resolved.
        left = ReferenceResults3(
            results=[ReferenceResult3(path="p1", uuid="u1", data="same")]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="p2", uuid="u2", data="same")]
        )
        result = ReferenceExpression3._union(left, right)
        assert len(result) == 2

    def test_both_sides_empty_gives_empty(self):
        result = ReferenceExpression3._union(ReferenceResults3(), ReferenceResults3())
        assert result.results == []


class TestIntersect:
    def test_keeps_every_matching_left_item_not_just_one_per_key(self):
        # the actual bug caught while building this: an earlier draft
        # deduplicated the LEFT side by key before filtering, which
        # silently collapsed multiple runs sharing one group name down
        # to one. "give me all the runs where the group had 'orders'"
        # must return every matching run, not one exemplar per group.
        left = ReferenceResults3(
            results=[
                ReferenceResult3(path="a-run1", uuid="u1", data="groupA"),
                ReferenceResult3(path="a-run2", uuid="u2", data="groupA"),
                ReferenceResult3(path="b-run1", uuid="u3", data="groupB"),
                ReferenceResult3(path="b-run2", uuid="u4", data="groupB"),
                ReferenceResult3(path="b-run3", uuid="u5", data="groupB"),
            ]
        )
        right = ReferenceResults3(
            results=[
                ReferenceResult3(path="groupA/g.csvpath", uuid="gva", data="groupA"),
                ReferenceResult3(path="groupB/g.csvpath", uuid="gvb", data="groupB"),
            ]
        )
        result = ReferenceExpression3._intersect(left, right)
        assert result.files == ["a-run1", "a-run2", "b-run1", "b-run2", "b-run3"]

    def test_only_keeps_left_items_whose_key_matches(self):
        left = ReferenceResults3(
            results=[
                ReferenceResult3(path="a-run1", uuid="u1", data="groupA"),
                ReferenceResult3(path="b-run1", uuid="u3", data="groupB"),
            ]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="groupA/g.csvpath", uuid="gva", data="groupA")]
        )
        result = ReferenceExpression3._intersect(left, right)
        assert result.files == ["a-run1"]

    def test_no_matches_gives_empty(self):
        left = ReferenceResults3(
            results=[ReferenceResult3(path="p1", uuid="u1", data="x")]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="p2", uuid="u2", data="y")]
        )
        assert ReferenceExpression3._intersect(left, right).results == []

    def test_none_keyed_left_items_never_survive(self):
        left = ReferenceResults3(
            results=[
                ReferenceResult3(path="a-run1", uuid="u1", data="groupA"),
                ReferenceResult3(path="x-run1", uuid="u9", data=None),
            ]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="groupA/g.csvpath", uuid="gva", data="groupA")]
        )
        result = ReferenceExpression3._intersect(left, right)
        assert result.files == ["a-run1"]

    def test_true_duplicate_left_items_collapse_to_one(self):
        left = ReferenceResults3(
            results=[
                ReferenceResult3(path="a-run1", uuid="u1", data="groupA"),
                ReferenceResult3(path="a-run1", uuid="u1", data="groupA"),
            ]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="groupA/g.csvpath", uuid="gva", data="groupA")]
        )
        assert len(ReferenceExpression3._intersect(left, right)) == 1

    def test_unhashable_left_key_raises(self):
        left = ReferenceResults3(
            results=[ReferenceResult3(path="p1", uuid="u1", data=["not", "hashable"])]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="p2", uuid="u2", data="x")]
        )
        with pytest.raises(ReferenceException3):
            ReferenceExpression3._intersect(left, right)

    def test_unhashable_right_key_raises(self):
        left = ReferenceResults3(
            results=[ReferenceResult3(path="p1", uuid="u1", data="x")]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="p2", uuid="u2", data={"not": "hashable"})]
        )
        with pytest.raises(ReferenceException3):
            ReferenceExpression3._intersect(left, right)


class TestSubtract:
    def test_removes_left_items_whose_key_matches_the_right(self):
        left = ReferenceResults3(
            results=[
                ReferenceResult3(path="a-run1", uuid="u1", data="groupA"),
                ReferenceResult3(path="b-run1", uuid="u3", data="groupB"),
            ]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="groupA/g.csvpath", uuid="gva", data="groupA")]
        )
        result = ReferenceExpression3._subtract(left, right)
        assert result.files == ["b-run1"]

    def test_none_keyed_left_items_always_survive(self):
        # a None key can never be matched away -- it never establishes
        # a match in the first place.
        left = ReferenceResults3(
            results=[
                ReferenceResult3(path="a-run1", uuid="u1", data="groupA"),
                ReferenceResult3(path="x-run1", uuid="u9", data=None),
            ]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="groupA/g.csvpath", uuid="gva", data="groupA")]
        )
        result = ReferenceExpression3._subtract(left, right)
        assert result.files == ["x-run1"]

    def test_removes_every_matching_left_item_not_just_one(self):
        left = ReferenceResults3(
            results=[
                ReferenceResult3(path="a-run1", uuid="u1", data="groupA"),
                ReferenceResult3(path="a-run2", uuid="u2", data="groupA"),
                ReferenceResult3(path="b-run1", uuid="u3", data="groupB"),
            ]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="groupA/g.csvpath", uuid="gva", data="groupA")]
        )
        result = ReferenceExpression3._subtract(left, right)
        assert result.files == ["b-run1"]


#
# ---- constructor validation
#
class TestConstruction:
    def test_rejects_none_or_empty_left(self):
        with pytest.raises(ValueError):
            ReferenceExpression3(
                left="", op=ReferenceExpression3.UNION, right="$acme.results.:last()",
                csvpaths=object(),
            )

    def test_rejects_none_or_empty_right(self):
        with pytest.raises(ValueError):
            ReferenceExpression3(
                left="$acme.results.:last()", op=ReferenceExpression3.UNION, right="",
                csvpaths=object(),
            )

    def test_rejects_unrecognized_op(self):
        with pytest.raises(ValueError):
            ReferenceExpression3(
                left="$acme.results.:last()",
                op="xor",
                right="$acme.results.:last()",
                csvpaths=object(),
            )

    def test_rejects_none_csvpaths(self):
        with pytest.raises(ValueError):
            ReferenceExpression3(
                left="$acme.results.:last()",
                op=ReferenceExpression3.UNION,
                right="$acme.results.:last()",
                csvpaths=None,
            )


#
# ---- end-to-end, real Finder plumbing -- David's own "orders" example
# (references_notes/notes/reference_expressions_notes.txt), using literal
# (non-'*') root_major on both sides, via real on-disk fixtures matching
# test_results_reference_finder_3.py's own established pattern. '*'
# traversal combined with a trailing field accessor is not supported by
# either CsvpathsReferenceFinder3 or ResultsReferenceFinder3 today
# (confirmed via direct testing while building this -- see
# TestStarTraversalPlusFieldAccessorIsNotYetSupported below) -- a real,
# separate limitation on the Finders themselves, not something
# ReferenceExpression3 needs to work around. Sub-expressions (nested
# ReferenceExpression3, UNION-ing two literal per-group queries) stand in
# for "search every group" here instead -- exactly the shape a caller CAN
# write today when the candidate group names are already known.
#
GROUPA_MANIFEST = [
    {
        "group_file_path": "named_paths/groupa/group.csvpath",
        "uuid": "gva",
        "named_paths": ["stmt orders text"],
        "named_paths_identities": ["orders"],
        "named_paths_name": "groupa",
    }
]
GROUPB_MANIFEST = [
    {
        "group_file_path": "named_paths/groupb/group.csvpath",
        "uuid": "gvb",
        "named_paths": ["stmt orders text"],
        "named_paths_identities": ["orders"],
        "named_paths_name": "groupb",
    }
]


class _FakePathsManager:
    def __init__(self, by_name):
        self._by_name = by_name

    def get_manifest_for_name(self, name):
        return self._by_name.get(name, [])

    def named_paths_home(self, name):
        return f"named_paths/{name}"

    @property
    def named_paths_names(self):
        return list(self._by_name.keys())

    @property
    def paths_root_manifest(self):
        return []


class _FakeResultsManager:
    def __init__(self, archive: str):
        self._archive = archive

    def get_named_results_home(self, name):
        return os.path.join(self._archive, name)

    @property
    def results_root_manifest(self):
        with open(os.path.join(self._archive, "manifest.json")) as f:
            return json.load(f)


class _FakeConfig:
    def __init__(self, archive: str):
        self._archive = archive
        self.inputs_csvpaths_path = None

    def get(self, *, section, name):
        return self._archive


class _FakeCsvPaths:
    def __init__(self, archive: str, paths_by_name: dict):
        self.paths_manager = _FakePathsManager(paths_by_name)
        self.results_manager = _FakeResultsManager(archive)
        self.config = _FakeConfig(archive)


def _write_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _make_run(base, run_name: str, run_uuid: str, group_name: str) -> str:
    run_dir = base / run_name
    _write_json(
        run_dir / "manifest.json",
        {"run_uuid": run_uuid, "named_paths_name": group_name},
    )
    return str(run_dir)


def _write_archive_manifest_multi(archive, groups: dict) -> None:
    entries = []
    for group, run_homes in groups.items():
        entries.extend({"named_paths_name": group, "run_home": rh} for rh in run_homes)
    _write_json(archive / "manifest.json", entries)


@pytest.fixture
def orders_archive(tmp_path):
    # group A: 2 runs, group B: 3 runs, both groups have an "orders"
    # csvpath statement in their current version -- David's own worked
    # example (references_notes/notes/reference_expressions_notes.txt).
    archive = tmp_path / "archive"
    a_runs = [
        _make_run(archive / "groupa", "2026-01-01_00-00-00", "a1", "groupa"),
        _make_run(archive / "groupa", "2026-01-02_00-00-00", "a2", "groupa"),
    ]
    b_runs = [
        _make_run(archive / "groupb", "2026-01-01_00-00-00", "b1", "groupb"),
        _make_run(archive / "groupb", "2026-01-02_00-00-00", "b2", "groupb"),
        _make_run(archive / "groupb", "2026-01-03_00-00-00", "b3", "groupb"),
    ]
    _write_archive_manifest_multi(archive, {"groupa": a_runs, "groupb": b_runs})
    return _FakeCsvPaths(str(archive), {"groupa": GROUPA_MANIFEST, "groupb": GROUPB_MANIFEST})


def _left_side(csvpaths) -> ReferenceExpression3:
    # "every run" -- UNION of the two known groups' own runs.
    return ReferenceExpression3(
        left="$groupa.results.:flatten():named_paths_name()",
        op=ReferenceExpression3.UNION,
        right="$groupb.results.:flatten():named_paths_name()",
        csvpaths=csvpaths,
    )


def _right_side(csvpaths) -> ReferenceExpression3:
    # "every group with an 'orders' statement" -- UNION of the two known
    # groups' own :having() checks.
    return ReferenceExpression3(
        left='$groupa.csvpaths.:having("orders"):named_paths_name()',
        op=ReferenceExpression3.UNION,
        right='$groupb.csvpaths.:having("orders"):named_paths_name()',
        csvpaths=csvpaths,
    )


class TestOrdersExampleEndToEnd:
    def test_both_groups_have_orders_all_five_runs_come_back(self, orders_archive):
        expr = ReferenceExpression3(
            left=_left_side(orders_archive),
            op=ReferenceExpression3.INTERSECT,
            right=_right_side(orders_archive),
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert sorted(r.uuid for r in result.results) == ["a1", "a2", "b1", "b2", "b3"]

    def test_only_one_group_has_orders_only_its_runs_come_back(self, orders_archive):
        # groupB's version no longer has "orders" -- :having() only
        # matches groupA now.
        orders_archive.paths_manager._by_name["groupb"] = [
            {
                "group_file_path": "named_paths/groupb/group.csvpath",
                "uuid": "gvb",
                "named_paths": ["stmt other text"],
                "named_paths_identities": ["other"],
                "named_paths_name": "groupb",
            }
        ]
        expr = ReferenceExpression3(
            left=_left_side(orders_archive),
            op=ReferenceExpression3.INTERSECT,
            right=_right_side(orders_archive),
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert sorted(r.uuid for r in result.results) == ["a1", "a2"]

    def test_neither_group_has_orders_no_runs_come_back(self, orders_archive):
        for name in ("groupa", "groupb"):
            orders_archive.paths_manager._by_name[name] = [
                {
                    "group_file_path": f"named_paths/{name}/group.csvpath",
                    "uuid": f"gv-{name}",
                    "named_paths": ["stmt other text"],
                    "named_paths_identities": ["other"],
                    "named_paths_name": name,
                }
            ]
        expr = ReferenceExpression3(
            left=_left_side(orders_archive),
            op=ReferenceExpression3.INTERSECT,
            right=_right_side(orders_archive),
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert result.results == []

    def test_union_of_runs_and_groups_matches_the_documented_7_6_5(self, orders_archive):
        # the doc's own worked UNION variants -- 7 with both groups
        # matching, dropping to 6 and then 5 as groups stop matching.
        expr = ReferenceExpression3(
            left=_left_side(orders_archive),
            op=ReferenceExpression3.UNION,
            right=_right_side(orders_archive),
            csvpaths=orders_archive,
        )
        assert len(expr.resolve()) == 7

        orders_archive.paths_manager._by_name["groupb"] = [
            {
                "group_file_path": "named_paths/groupb/group.csvpath",
                "uuid": "gvb",
                "named_paths": ["stmt other text"],
                "named_paths_identities": ["other"],
                "named_paths_name": "groupb",
            }
        ]
        expr2 = ReferenceExpression3(
            left=_left_side(orders_archive),
            op=ReferenceExpression3.UNION,
            right=_right_side(orders_archive),
            csvpaths=orders_archive,
        )
        assert len(expr2.resolve()) == 6

        orders_archive.paths_manager._by_name["groupa"] = [
            {
                "group_file_path": "named_paths/groupa/group.csvpath",
                "uuid": "gva",
                "named_paths": ["stmt other text"],
                "named_paths_identities": ["other"],
                "named_paths_name": "groupa",
            }
        ]
        expr3 = ReferenceExpression3(
            left=_left_side(orders_archive),
            op=ReferenceExpression3.UNION,
            right=_right_side(orders_archive),
            csvpaths=orders_archive,
        )
        assert len(expr3.resolve()) == 5


class TestStarTraversalPlusFieldAccessorIsNotYetSupported:
    # a real, pre-existing limitation on BOTH Finders (not something
    # ReferenceExpression3 introduces or needs to fix) -- confirmed via
    # direct testing while building this class: neither
    # CsvpathsReferenceFinder3 nor ResultsReferenceFinder3 support '*'
    # traversal combined with a trailing field accessor yet, which blocks
    # the most literal phrasing of "every group"/"every run" without
    # already knowing the candidate names -- see the module docstring
    # above for how the "orders" tests work around it today.
    def test_csvpaths_star_traversal_with_field_accessor_raises(self, orders_archive):
        expr = ReferenceExpression3(
            left="$*.csvpaths.:having(\"orders\"):named_paths_name()",
            op=ReferenceExpression3.UNION,
            right="$groupa.csvpaths.:having(\"orders\"):named_paths_name()",
            csvpaths=orders_archive,
        )
        with pytest.raises(ReferenceException3):
            expr.resolve()

    def test_results_star_traversal_with_field_accessor_raises(self, orders_archive):
        expr = ReferenceExpression3(
            left="$*.results.:flatten():named_paths_name()",
            op=ReferenceExpression3.UNION,
            right="$groupa.results.:flatten():named_paths_name()",
            csvpaths=orders_archive,
        )
        with pytest.raises(ReferenceException3):
            expr.resolve()
