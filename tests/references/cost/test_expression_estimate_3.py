import pytest

from csvpath.references.reference_estimate_3 import ExpressionEstimate3, ReferenceEstimate3
from csvpath.references.reference_expression_3 import ReferenceExpression3
from tests.references.cost.read_counter import ReadCounter
from tests.references.cost.test_results_estimate_soundness_3 import csvpaths  # noqa: F401

#
# an expression gives one estimate per side (David's note: "a reference
# expression results in two fully separate estimates"); a paths side is
# queried and never resolved (B2), so it keeps only its query part
#
LEFT = '$*.files.:type("csv")'
RIGHT = '$validate_orders.results.:last().*:errors():idchain("add[0]")'


def test_one_estimate_per_side(csvpaths):  # noqa: F811
    ex = ReferenceExpression3.from_string(expression=f"{LEFT} UNION {RIGHT}", csvpaths=csvpaths).estimate()
    assert isinstance(ex, ExpressionEstimate3)
    assert isinstance(ex.left, ReferenceEstimate3) and isinstance(ex.right, ReferenceEstimate3)
    assert ex.left.reference == LEFT and ex.right.reference == RIGHT


def test_a_paths_side_keeps_only_its_query(csvpaths):  # noqa: F811
    ex = ReferenceExpression3.from_string(expression=f"{LEFT} UNION {RIGHT}", csvpaths=csvpaths).estimate()
    assert ex.left.resolve_reads == {}
    assert any("queried, not resolved" in w for w in ex.left.why)


def test_a_values_side_keeps_its_resolve(csvpaths):  # noqa: F811
    values = "$validate_orders.results.:last().*:uuid()"
    ex = ReferenceExpression3.from_string(expression=f"{values} UNION {values}", csvpaths=csvpaths).estimate()
    assert ex.left.resolve_reads == {"instance_manifest": 4}


def test_a_sub_expression_nests(csvpaths):  # noqa: F811
    ex = ReferenceExpression3.from_string(
        expression=f"({LEFT} UNION {LEFT}) SUBTRACT {RIGHT}", csvpaths=csvpaths
    ).estimate()
    assert isinstance(ex.left, ExpressionEstimate3)
    assert "left:" in ex.summary() and ex.to_dict()["left"]["left"]["reference"] == LEFT


def test_estimating_an_expression_reads_only_ledgers(csvpaths):  # noqa: F811
    expr = ReferenceExpression3.from_string(expression=f"{LEFT} UNION {RIGHT}", csvpaths=csvpaths)
    with ReadCounter.for_csvpaths(csvpaths) as counter:
        expr.estimate()
    assert set(counter.reads) == {"ledger"}


def test_the_summary_names_kinds_plainly(csvpaths):  # noqa: F811
    from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3

    est = ReferenceFinderFactory3.for_reference(
        reference="$*.results.:all().*:valid(:true())", csvpaths=csvpaths
    ).estimate()
    text = est.summary()
    assert "11 run listings" in text and "23 instance manifests" in text and "1 ledger" in text


def test_without_resolve_needs_a_reason(csvpaths):  # noqa: F811
    from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3

    est = ReferenceFinderFactory3.for_reference(reference=RIGHT, csvpaths=csvpaths).estimate()
    with pytest.raises(ValueError):
        est.without_resolve(because=" ")


def test_the_summary_names_estimated_kinds_plainly(csvpaths):  # noqa: F811
    ex = ReferenceExpression3.from_string(expression=f"{LEFT} UNION {RIGHT}", csvpaths=csvpaths).estimate()
    text = ex.summary()
    assert "estimated: 2 name listings (upper bound" in text
    assert "name_listing" not in text


def test_a_paths_side_keeps_a_structural_may_raise(csvpaths):  # noqa: F811
    # "may raise -- several functions on name_one" can raise at query
    # (reviewer on #738)
    ex = ReferenceExpression3.from_string(
        expression=f'$*.files.:type("csv"):last() UNION {RIGHT}', csvpaths=csvpaths
    ).estimate()
    assert ex.left.would_raise and ex.left.would_raise.startswith("may raise")


def test_a_paths_side_drops_a_resolve_raise(csvpaths):  # noqa: F811
    from csvpath.references.reference_estimate_3 import CostWeights, ReferenceEstimate3

    est = ReferenceEstimate3(
        reference="$a.files.:last()",
        reads=[],
        why=[],
        backend="local",
        weights=CostWeights.for_config(csvpaths.config),
        sql=False,
        would_raise="may raise -- resolve: up to 5 version files at once (compendium 5.3)",
    )
    assert est.without_resolve(because="a paths side").would_raise is None
