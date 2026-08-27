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


class TestFilterByIdentity:
    # paths/paths, or values(LHS)/paths(RHS) -- the comparison basis is
    # identity (path+uuid together), never .data. Built 2026-08-26, the
    # references_v3_expressions.md paths-vs-values compatibility matrix.
    def test_intersect_keeps_left_items_whose_identity_matches(self):
        left = ReferenceResults3(
            results=[
                ReferenceResult3(path="p1", uuid="u1", data="ignored"),
                ReferenceResult3(path="p2", uuid="u2"),
            ]
        )
        right = ReferenceResults3(results=[ReferenceResult3(path="p1", uuid="u1")])
        result = ReferenceExpression3._filter_by_identity(left, right, keep=True)
        assert result.files == ["p1"]
        # LHS's own .data survives intact -- the comparison basis
        # changed, the output shape did not.
        assert result.results[0].data == "ignored"

    def test_subtract_removes_left_items_whose_identity_matches(self):
        left = ReferenceResults3(
            results=[
                ReferenceResult3(path="p1", uuid="u1"),
                ReferenceResult3(path="p2", uuid="u2"),
            ]
        )
        right = ReferenceResults3(results=[ReferenceResult3(path="p1", uuid="u1")])
        result = ReferenceExpression3._filter_by_identity(left, right, keep=False)
        assert result.files == ["p2"]

    def test_same_path_different_uuid_does_not_match(self):
        # e.g. CSVPATHS shares one group.csvpath path across every
        # version -- path alone is not enough, uuid must agree too.
        left = ReferenceResults3(results=[ReferenceResult3(path="p1", uuid="u1")])
        right = ReferenceResults3(results=[ReferenceResult3(path="p1", uuid="u2")])
        result = ReferenceExpression3._filter_by_identity(left, right, keep=True)
        assert result.results == []


class TestFilterByNativeUuid:
    # paths(LHS)/values(RHS) where RHS's own accessor is uuid-valued --
    # LHS's own NATIVE uuid (no accessor needed) is compared directly
    # against RHS's .data.
    def test_intersect_keeps_left_items_whose_native_uuid_is_in_the_right_values(self):
        left = ReferenceResults3(
            results=[
                ReferenceResult3(path="p1", uuid="file-uuid-1"),
                ReferenceResult3(path="p2", uuid="file-uuid-2"),
            ]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="r1", uuid=None, data="file-uuid-1")]
        )
        result = ReferenceExpression3._filter_by_native_uuid(left, right, keep=True)
        assert result.files == ["p1"]

    def test_subtract_removes_left_items_whose_native_uuid_is_in_the_right_values(self):
        left = ReferenceResults3(
            results=[
                ReferenceResult3(path="p1", uuid="file-uuid-1"),
                ReferenceResult3(path="p2", uuid="file-uuid-2"),
            ]
        )
        right = ReferenceResults3(
            results=[ReferenceResult3(path="r1", uuid=None, data="file-uuid-1")]
        )
        result = ReferenceExpression3._filter_by_native_uuid(left, right, keep=False)
        assert result.files == ["p2"]

    def test_left_item_with_no_native_uuid_never_matches(self):
        left = ReferenceResults3(results=[ReferenceResult3(path="p1", uuid=None)])
        right = ReferenceResults3(
            results=[ReferenceResult3(path="r1", uuid=None, data="file-uuid-1")]
        )
        result = ReferenceExpression3._filter_by_native_uuid(left, right, keep=True)
        assert result.results == []


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
# (references_notes/notes/reference_expressions_notes.txt).
#
# UPDATED 2026-08-19 (PR #254, all commits): both sides now use REAL '*'
# traversal, single plain reference strings, no sub-expression workaround
# needed anymore. Three '*'-traversal gaps had to close, in order, before
# this was reachable:
#   1. (#253) a bare field accessor riding alongside a pointer/':all()'.
#   2. (#254) ':having()' (CSVPATHS)/':flatten()' (RESULTS) combined with
#      traversal at all -- CSVPATHS' right side needs :having(), RESULTS'
#      left side needs :flatten(), neither was recognized before this.
#   3. (#254) a pointer became OPTIONAL in every RESULTS '*'-traversal
#      shape (previously always required) -- RESULTS' own left side
#      needs "every run, unreduced," which only exists without a
#      pointer. Confirmed against FilesReferenceFinder3 (never requires
#      one, any mode) and RESULTS' own literal-root precedent (same)
#      before making this change -- CsvpathsReferenceFinder3's own
#      narrower, asymmetric precedent (pointer required in POOL mode,
#      optional only in GROUP/':all()') was NOT the target; CSVPATHS'
#      right side already worked via its OWN existing ':all()'-no-
#      pointer precedent, unaffected by this RESULTS-only change.
# _left_side/_right_side below were previously each a UNION sub-
# expression of two literal per-group queries -- now single strings.
#
GROUPA_MANIFEST = [
    {
        "group_file_path": "named_paths/groupa/group.csvpath",
        "uuid": "gva",
        "named_paths": ["stmt orders text"],
        "named_paths_identities": ["orders"],
        "named_paths_name": "groupa",
        "fingerprint": "groupa-fp",
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


def _make_run(
    base,
    run_name: str,
    run_uuid: str,
    group_name: str,
    *,
    named_file_fingerprint=None,
    named_paths_fingerprint=None,
) -> str:
    run_dir = base / run_name
    manifest = {"run_uuid": run_uuid, "named_paths_name": group_name}
    if named_file_fingerprint is not None:
        manifest["named_file_fingerprint"] = named_file_fingerprint
    if named_paths_fingerprint is not None:
        manifest["named_paths_fingerprint"] = named_paths_fingerprint
    _write_json(run_dir / "manifest.json", manifest)
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
        _make_run(
            archive / "groupa",
            "2026-01-01_00-00-00",
            "a1",
            "groupa",
            named_file_fingerprint="groupa-fp",
            named_paths_fingerprint="groupa-fp",
        ),
        _make_run(archive / "groupa", "2026-01-02_00-00-00", "a2", "groupa"),
    ]
    b_runs = [
        _make_run(archive / "groupb", "2026-01-01_00-00-00", "b1", "groupb"),
        _make_run(archive / "groupb", "2026-01-02_00-00-00", "b2", "groupb"),
        _make_run(archive / "groupb", "2026-01-03_00-00-00", "b3", "groupb"),
    ]
    _write_archive_manifest_multi(archive, {"groupa": a_runs, "groupb": b_runs})
    return _FakeCsvPaths(str(archive), {"groupa": GROUPA_MANIFEST, "groupb": GROUPB_MANIFEST})


def _left_side(csvpaths) -> str:
    # "every run" -- a single real '*' traversal reference now (updated
    # 2026-08-19): ':flatten()' (any depth, POOL) with no pointer lists
    # every matched run across every group, unreduced -- both the
    # ':flatten()'-combined-with-traversal gap and the pointer-optional
    # gap had to close first (see this module's own docstring above).
    return "$*.results.:flatten():named_paths_name()"


def _right_side(csvpaths) -> str:
    # "every group with an 'orders' statement" -- a single real '*'
    # traversal reference now (updated 2026-08-19): ':having("orders")'
    # filters, ':all()' with no pointer lists every matching version per
    # group, unreduced -- CSVPATHS' own ':all()'-no-pointer precedent
    # already supported this once ':having()' itself was recognized in
    # traversal (#254), no further CSVPATHS change was needed.
    return '$*.csvpaths.:having("orders"):all():named_paths_name()'


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


class TestPathsVsValuesEndToEnd:
    # references_v3_expressions.md's own paths-vs-values compatibility
    # matrix, proven through real reference strings/resolve(), not just
    # the synthetic-ReferenceResults3 unit tests above -- confirms
    # _kind()/_produces_uuid() classify real references correctly and
    # resolve() dispatches to the right comparison basis. UNION's own
    # rule is separate and LHS-driven, revised 2026-08-26 (same day, but
    # a real second revision, not the original build) to compare by
    # conceptual KIND ("uuid", "name", ...) rather than requiring the
    # two sides' accessors to be literally identical -- see the tests
    # immediately below.
    def test_union_of_a_paths_left_and_values_right_succeeds_by_path(
        self, orders_archive
    ):
        # LHS is paths -- RHS unions freely, by path, regardless of its
        # own kind.
        expr = ReferenceExpression3(
            left="$*.results.:flatten()",  # paths -- no trailing accessor
            op=ReferenceExpression3.UNION,
            right=_right_side(orders_archive),  # values -- :named_paths_name()
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert sorted(r.uuid for r in result.results if r.uuid) == [
            "a1",
            "a2",
            "b1",
            "b2",
            "b3",
            "gva",
            "gvb",
        ]

    def test_union_of_a_values_left_and_paths_right_raises(self, orders_archive):
        # LHS is values -- a paths-only RHS has no accessor at all, so it
        # cannot match the left side's own terminal accessor.
        expr = ReferenceExpression3(
            left=_left_side(orders_archive),  # values -- :named_paths_name()
            op=ReferenceExpression3.UNION,
            right="$*.results.:flatten()",  # paths -- no trailing accessor
            csvpaths=orders_archive,
        )
        with pytest.raises(ReferenceException3):
            expr.resolve()

    def test_union_of_two_values_sides_with_different_kinds_raises(
        self, orders_archive
    ):
        # both sides are values, but the accessors are neither the same
        # function nor the same KIND (:named_paths_name() is "name",
        # :run_uuid() is "uuid") -- not comparable, even though both
        # happen to resolve to strings.
        expr = ReferenceExpression3(
            left=_left_side(orders_archive),  # values -- :named_paths_name()
            op=ReferenceExpression3.UNION,
            right="$groupa.results.:flatten():run_uuid()",  # values -- :run_uuid()
            csvpaths=orders_archive,
        )
        with pytest.raises(ReferenceException3):
            expr.resolve()

    def test_union_of_two_values_sides_with_the_same_kind_succeeds(
        self, orders_archive
    ):
        # :uuid() and :run_uuid() are different functions but share
        # KIND == "uuid" -- comparable under the revised rule, where the
        # earlier, now-superseded "accessor must be literally identical"
        # draft would have raised.
        expr = ReferenceExpression3(
            left="$groupa.results.:flatten():uuid()",  # values -- KIND "uuid"
            op=ReferenceExpression3.UNION,
            right="$groupb.results.:flatten():run_uuid()",  # values -- KIND "uuid"
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert sorted(r.data for r in result.results) == [
            "a1",
            "a2",
            "b1",
            "b2",
            "b3",
        ]

    def test_union_of_two_name_accessors_with_the_same_kind_succeeds(
        self, orders_archive
    ):
        # :named_paths_name() and :named_results_name() are different
        # functions but share KIND == "name".
        expr = ReferenceExpression3(
            left="$groupa.results.:flatten():named_paths_name()",
            op=ReferenceExpression3.UNION,
            right="$groupa.results.:flatten():named_results_name()",
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert len(result) > 0

    def test_union_of_fingerprint_and_named_file_fingerprint_succeeds(
        self, orders_archive
    ):
        # :fingerprint() (the named-paths group's own content) and
        # :named_file_fingerprint() (a RESULTS run's record of a
        # DIFFERENT entity's content) are different functions describing
        # different entities, but both share KIND == "fingerprint" --
        # David's own correction (2026-08-26) to an earlier, narrower
        # taxonomy that had left the fingerprint functions uncategorized
        # on the reasoning that different entities cannot be compared.
        # A fingerprint is a cryptographic identity of bytes, so "same
        # content" is meaningful across entities, unlike uuid/name.
        expr = ReferenceExpression3(
            left="$groupa.csvpaths.:fingerprint()",  # values -- KIND "fingerprint"
            op=ReferenceExpression3.UNION,
            right="$groupa.results.:flatten():named_file_fingerprint()",  # values -- KIND "fingerprint"
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert "groupa-fp" in {r.data for r in result.results}

    def test_union_of_fingerprint_and_named_paths_fingerprint_succeeds(
        self, orders_archive
    ):
        # the ORIGINAL motivating case for named_paths_fingerprint
        # existing at all (bucket-list entry, David 2026-08-26/added
        # 2026-08-27): "let a run be compared, by content, against the
        # named-paths group whose content produced it -- catching the
        # case where the same group.csvpaths text was loaded under two
        # different names (different uuids, identical fingerprints)."
        # :fingerprint() here reads groupa's CURRENT content fingerprint
        # (GROUPA_MANIFEST's own "groupa-fp"); :named_paths_fingerprint()
        # reads run a1's own RECORD of which content drove it -- set to
        # the same value by the orders_archive fixture. Both share
        # KIND == "fingerprint", same as the named_file_fingerprint
        # pairing above, just for the named-paths entity instead of the
        # named-file one.
        expr = ReferenceExpression3(
            left="$groupa.csvpaths.:fingerprint()",  # values -- KIND "fingerprint"
            op=ReferenceExpression3.UNION,
            right="$groupa.results.:flatten():named_paths_fingerprint()",  # values -- KIND "fingerprint"
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert "groupa-fp" in {r.data for r in result.results}

    def test_intersect_paths_paths_compares_by_identity(self, orders_archive):
        expr = ReferenceExpression3(
            left="$*.results.:flatten()",
            op=ReferenceExpression3.INTERSECT,
            right="$groupa.results.:flatten()",
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert sorted(r.uuid for r in result.results) == ["a1", "a2"]

    def test_intersect_values_left_paths_right_keeps_lhs_data(self, orders_archive):
        expr = ReferenceExpression3(
            left="$*.results.:flatten():named_paths_name()",  # values
            op=ReferenceExpression3.INTERSECT,
            right="$groupa.results.:flatten()",  # paths
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert sorted(r.uuid for r in result.results) == ["a1", "a2"]
        # LHS's own .data (the group name) survives -- the comparison
        # basis fell back to identity, the output shape did not change.
        assert all(r.data == "groupa" for r in result.results)

    def test_intersect_paths_left_values_right_non_uuid_raises(self, orders_archive):
        expr = ReferenceExpression3(
            left="$*.results.:flatten()",  # paths
            op=ReferenceExpression3.INTERSECT,
            right=_right_side(orders_archive),  # values, :named_paths_name() -- not uuid-valued
            csvpaths=orders_archive,
        )
        with pytest.raises(ReferenceException3):
            expr.resolve()

    def test_intersect_paths_left_values_right_uuid_valued_compares_native_uuid(
        self, orders_archive
    ):
        # paths(LHS)/values(RHS), RHS's own accessor (KIND == "uuid")
        # compares LHS's native uuid directly against RHS's own .data.
        expr = ReferenceExpression3(
            left="$*.results.:flatten()",  # paths -- native uuids a1,a2,b1,b2,b3
            op=ReferenceExpression3.INTERSECT,
            right="$groupa.results.:flatten():run_uuid()",  # values, uuid-valued -- a1, a2
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert sorted(r.uuid for r in result.results) == ["a1", "a2"]


class TestStarTraversalPlusFieldAccessorNowWorks:
    # PR #253 (2026-08-18) fixed the Finder-level gap this class used to
    # document as unsupported: a run/version-level field accessor can now
    # ride alongside a bare pointer or ':all()' in '*' traversal, for
    # both CsvpathsReferenceFinder3 (via the new _group_manifest_entry()
    # helper) and ResultsReferenceFinder3 (already group-independent once
    # the guard was loosened). Already covered directly at the Finder
    # level in test_csvpaths_reference_finder_3.py/
    # test_results_reference_finder_3.py -- proven here too since this is
    # the actual integration point ReferenceExpression3 needs: a plain
    # reference STRING with root_major='*' now resolves successfully all
    # the way through ReferenceFinderFactory3 -> the Finder -> resolve(),
    # not just when hand-built directly against the Finder class.
    def test_csvpaths_star_traversal_with_field_accessor_resolves(
        self, orders_archive
    ):
        expr = ReferenceExpression3(
            left="$*.csvpaths.:all():named_paths_name()",
            op=ReferenceExpression3.UNION,
            right="$*.csvpaths.:all():named_paths_name()",
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        assert sorted(r.data for r in result.results) == ["groupa", "groupb"]

    def test_results_star_traversal_with_field_accessor_resolves(
        self, orders_archive
    ):
        expr = ReferenceExpression3(
            left="$*.results.:last():named_paths_name()",
            op=ReferenceExpression3.UNION,
            right="$groupa.results.:flatten():named_paths_name()",
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        # groupB's b3 (2026-01-03) is the true global-latest run -- '*'
        # traversal pools/sorts across both groups by real timestamp, so
        # this only comes back correctly if the star-rooted side above
        # actually resolved through traversal rather than raising.
        assert "b3" in {r.uuid for r in result.results}
        assert {r.data for r in result.results} == {"groupa", "groupb"}


class TestHavingAndFlattenPlusStarTraversalNowWork:
    # PR #254 (2026-08-19, full run) closed this gap in stages: first
    # recognizing ':having()' (CSVPATHS)/':flatten()' (RESULTS) in '*'
    # traversal at all, then making a pointer OPTIONAL in every RESULTS
    # shape (RESULTS' own left side needs "every run, unreduced," which
    # only a missing pointer gives -- CSVPATHS' own ':all()' already had
    # its own no-pointer precedent, unaffected). This class used to
    # assert both raised; confirmed live before rewriting that neither
    # does anymore, then replaced with positive tests -- proven here at
    # the ReferenceExpression3 level (plain reference strings, not the
    # Finder classes directly), same integration point
    # TestStarTraversalPlusFieldAccessorNowWorks above proves.
    def test_csvpaths_having_combined_with_traversal_now_works(
        self, orders_archive
    ):
        expr = ReferenceExpression3(
            left="$*.csvpaths.:having(\"orders\"):all():named_paths_name()",
            op=ReferenceExpression3.UNION,
            right="$groupa.csvpaths.:having(\"orders\"):named_paths_name()",
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        # right's groupa item is IDENTICAL to left's own groupa item
        # (same path/uuid/resolved data) -- UNION's dedup collapses the
        # duplicate, leaving one groupa (from either side) plus left's
        # own groupb, not three/two raw items pooled naively.
        assert sorted(r.data for r in result.results) == ["groupa", "groupb"]

    def test_results_flatten_combined_with_traversal_now_works(
        self, orders_archive
    ):
        expr = ReferenceExpression3(
            left="$*.results.:flatten():named_paths_name()",
            op=ReferenceExpression3.UNION,
            right="$groupa.results.:flatten():named_paths_name()",
            csvpaths=orders_archive,
        )
        result = expr.resolve()
        # right's a1/a2 are IDENTICAL to left's own a1/a2 (same run
        # dir/uuid/resolved data) -- UNION's dedup collapses the
        # duplicates, leaving all 5 distinct runs once each, not 6.
        assert sorted(r.uuid for r in result.results) == [
            "a1",
            "a2",
            "b1",
            "b2",
            "b3",
        ]
