#
# ':manifest()' written as its own segment after a path (name_one gap
# review, item D). It raised "Does not yet support :manifest() as a name_one
# path segment". Compendium 3.9c: ':manifest()' "doesn't operate as or in a
# path segment at all"; in RESULTS it implies a '*' (one manifest per run),
# in FILES it does not. So:
# - RESULTS 'customers/:manifest():first()' is 'customers/:first():manifest()'
#   (NRE 662-663)
# - FILES 'orders/:manifest()' (3.9b) is 'orders:manifest()'
#
import pytest

from csvpath.references.reference_3 import FunctionCall3, Star3
from csvpath.references.reference_finder_3 import ReferenceFinder3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.reference_parser_3 import ReferenceParser3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import layout  # noqa: F401
from tests.references.test_results_wildcard_paths_3 import runs  # noqa: F401


def _query(csvpaths, reference: str) -> list:
    finder = ReferenceFinderFactory3.for_reference(
        reference=reference, csvpaths=csvpaths
    )
    return [(str(r.path), r.uuid) for r in finder.query().results]


class TestAttachTrailingManifest:
    def _name_one(self, csvpaths, reference):
        return ReferenceParser3(string=reference, csvpaths=csvpaths).parsed.name_one

    def test_results_adds_the_run_slot(self, runs):  # noqa: F811
        p, _ = runs
        n = self._name_one(p, "$acme.results.customers/:manifest():first()")
        ReferenceFinder3._attach_trailing_manifest(name_one=n, implies_star=True)
        assert n.path[0] == "customers" and isinstance(n.path[1], Star3)
        assert [f.name for f in n.functions] == ["manifest", "first"]

    def test_files_does_not(self, runs):  # noqa: F811
        p, _ = runs
        n = self._name_one(p, "$acme.files.orders/:manifest()")
        ReferenceFinder3._attach_trailing_manifest(name_one=n, implies_star=False)
        assert n.path == ["orders"]
        assert [f.name for f in n.functions] == ["manifest"]

    def test_a_bare_manifest_is_left_alone(self, runs):  # noqa: F811
        p, _ = runs
        n = self._name_one(p, "$acme.files.:manifest()")
        ReferenceFinder3._attach_trailing_manifest(name_one=n, implies_star=False)
        assert isinstance(n.path[0], FunctionCall3) and not n.functions

    def test_none_raises(self):
        with pytest.raises(ValueError):
            ReferenceFinder3._attach_trailing_manifest(name_one=None, implies_star=True)


RESULTS_PAIRS = [
    # NRE 662-663, on a template the fixture has
    (
        "$acme.results.customers/east/:manifest():first()",
        "$acme.results.customers/east/:first():manifest()",
    ),
    ("$acme.results.beta/:manifest():last()", "$acme.results.beta/*:manifest():last()"),
    ("$acme.results.beta/:manifest():last()", "$acme.results.beta/:last():manifest()"),
    ("$*.results.beta/:manifest():last()", "$*.results.beta/:last():manifest()"),
    (
        "$acme.results.north/:all()/:manifest()",
        "$acme.results.north/:all()/*:manifest()",
    ),
    # more segment kinds (reviewer on #793)
    ("$acme.results.*/:manifest()", "$acme.results.*/*:manifest()"),
    ("$*.results.*/:manifest()", "$*.results.*/*:manifest()"),
    (
        "$acme.results.:regex(/^b/)/:manifest()",
        "$acme.results.:regex(/^b/)/*:manifest()",
    ),
    (
        '$*.results.:choice("beta|gamma")/:manifest()',
        '$*.results.:choice("beta|gamma")/*:manifest()',
    ),
    (
        "$acme.results.:flatten()/2025/:manifest()",
        "$acme.results.:flatten()/2025/*:manifest()",
    ),
]


class TestResults:
    @pytest.mark.parametrize("written,same_as", RESULTS_PAIRS)
    def test_the_same_as_the_spelling_with_the_run_slot(
        self,
        runs,  # noqa: F811
        written,
        same_as,
    ):
        p, _ = runs
        got = _query(p, written)
        assert got and got == _query(p, same_as)

    def test_it_is_each_runs_manifest(self, runs):  # noqa: F811
        p, _ = runs
        paths = [path for path, _ in _query(p, "$acme.results.beta/:manifest():last()")]
        assert len(paths) == 1 and paths[0].endswith("manifest.json")


FILES_PAIRS = [
    (
        '$cappa.files.:name("three.csv")/:manifest()',
        '$cappa.files.:name("three.csv"):manifest()',
    ),
    (
        '$beta.files.EMEA/:name("two.csv")/:manifest()',
        '$beta.files.EMEA/:name("two.csv"):manifest()',
    ),
    ("$beta.files.EMEA/*/:manifest()", "$beta.files.EMEA/*:manifest()"),
]


class TestFiles:
    @pytest.mark.parametrize("written,same_as", FILES_PAIRS)
    def test_the_same_as_the_spelling_without_the_slash(
        self,
        layout,  # noqa: F811
        written,
        same_as,
    ):
        p, _ = layout
        got = _query(p, written)
        assert got and got == _query(p, same_as)

    def test_no_star_is_implied(self, layout):  # noqa: F811
        # 'orders/2026' names a file home 'orders/2026', which cappa does not
        # have ('orders/2026/four.csv' is one level deeper)
        p, _ = layout
        assert _query(p, "$cappa.files.orders/2026/:manifest()") == []
        assert _query(p, "$cappa.files.orders/2026/*/:manifest()")


@pytest.mark.parametrize("pair", RESULTS_PAIRS)
def test_the_results_estimate_keeps_its_contract(runs, pair):  # noqa: F811
    # pair[1] too: '$*.results.beta/:last():manifest()' was costed as the
    # ledger set on main
    p, _ = runs
    for reference in pair:
        finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
        measured, raised = _measure(p, reference)
        assert _problems(finder.estimate(), measured, raised) == []


@pytest.mark.parametrize("pair", FILES_PAIRS)
def test_the_files_estimate_keeps_its_contract(layout, pair):  # noqa: F811
    p, _ = layout
    for reference in pair:
        finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
        measured, raised = _measure(p, reference)
        assert _problems(finder.estimate(), measured, raised) == []


@pytest.mark.parametrize(
    "reference",
    ["$acme.results.*/:manifest()", "$acme.results.:regex(/^b/)/:manifest()"],
)
def test_the_estimate_is_the_same_before_and_after_a_query(runs, reference):  # noqa: F811
    # the estimator normalizes as query() does; it saw the raw path, so a
    # query run first changed its answer (reviewer on #793)
    p, _ = runs
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    before = finder.estimate()
    finder.query()
    after = finder.estimate()
    assert before.reads == after.reads and before.would_raise == after.would_raise


@pytest.mark.parametrize(
    "reference",
    [
        "$acme.results.*:manifest()",
        "$*.results.*:manifest()",
        "$acme.results.*",
        "$acme.results.:manifest()",
    ],
)
def test_a_lone_star_is_estimated_as_the_zero_level_runs(runs, reference):  # noqa: F811
    # it counted every run (13 against 2 read; reviewer on #793)
    p, _ = runs
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    measured, raised = _measure(p, reference)
    assert _problems(finder.estimate(), measured, raised) == []
