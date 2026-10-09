"""Low-level tests of the small ODCS classes: QualityUtility,
ConversionReport/SkippedItem, and CsvPathParts."""

import pytest

from csvpath.odcs.conversion_report import ConversionReport, SkippedItem
from csvpath.odcs.csvpath_parts import CsvPathParts
from csvpath.odcs.quality_utility import QualityUtility as quut


def test_odcs_quut_metric() -> None:
    assert quut.metric(rule={"metric": "rowCount"}) == "rowCount"
    assert quut.metric(rule={"rule": "nullValues"}) == "nullValues"
    assert quut.metric(rule={"type": "sql"}) is None
    with pytest.raises(TypeError):
        quut.metric(rule=None)


def test_odcs_quut_skip_reason() -> None:
    assert "database" in quut.skip_reason(kind="sql", rule={})
    assert "soda" in quut.skip_reason(kind="custom", rule={"engine": "soda"})
    assert "descriptions" in quut.skip_reason(kind="text", rule={})
    assert "other" in quut.skip_reason(kind="other", rule={})
    with pytest.raises(ValueError):
        quut.skip_reason(kind="", rule={})
    with pytest.raises(TypeError):
        quut.skip_reason(kind="sql", rule=None)


def test_odcs_skipped_item_bounds() -> None:
    SkippedItem(object="o", location="l", feature="f", reason="r")
    with pytest.raises(ValueError):
        SkippedItem(object="", location="l", feature="f", reason="r")
    with pytest.raises(TypeError):
        SkippedItem(object="o", location=None, feature="f", reason="r")


def test_odcs_conversion_report() -> None:
    report = ConversionReport()
    report.skip(obj="a", location="properties.x", feature="pattern", reason="r1")
    report.skip(obj="b", location="quality[0]", feature="quality.sql", reason="r2")
    report.skip(obj="a", location="properties.y", feature="enum", reason="r3")
    assert [s.location for s in report.for_object(obj="a")] == [
        "properties.x",
        "properties.y",
    ]
    assert report.for_object(obj="c") == []
    with pytest.raises(ValueError):
        report.for_object(obj="")


def test_odcs_csvpath_parts_render_simple() -> None:
    parts = CsvPathParts(metadata={"id": "t"})
    parts.line_args.extend(["string(#a)", "integer(#b)"])
    parts.line_checks.append("regex(/x/, #a)")
    assert not parts.needs_full_scan
    assert parts.render() == (
        "~\n"
        "  id: t\n"
        "~\n"
        "$[1*][\n"
        "    line(\n"
        "        string(#a),\n"
        "        integer(#b)\n"
        "    )\n"
        "    regex(/x/, #a)\n"
        "]\n"
    )


def test_odcs_csvpath_parts_render_full_scan_order() -> None:
    parts = CsvPathParts(metadata={"id": "t"})
    parts.first_checks.append("FIRST")
    parts.line_args.append("string(#a)")
    parts.line_checks.append("CHECK")
    parts.counters.append("COUNTER")
    parts.last_checks.append("LAST")
    assert parts.needs_full_scan
    lines = [line.strip() for line in parts.render().splitlines()]
    order = ["$[*][", "FIRST", "first_line.nocontrib() -> skip()", "line("]
    assert lines[3:7] == order
    assert lines[-5:] == [")", "CHECK", "COUNTER", "LAST", "]"]


def test_odcs_csvpath_parts_only_first_checks_need_full_scan() -> None:
    #
    # threshold counters and last-line checks work in $[1*]: with no data
    # lines there is nothing to count, so they never need the header line
    #
    parts = CsvPathParts()
    parts.counters.append("x")
    parts.last_checks.append("x")
    assert not parts.needs_full_scan
    parts.first_checks.append("x")
    assert parts.needs_full_scan


def test_odcs_csvpath_parts_render_needs_line_args() -> None:
    with pytest.raises(ValueError):
        CsvPathParts().render()


def test_odcs_csvpath_parts_add_threshold() -> None:
    parts = CsvPathParts()
    rule = {"mustBeLessThan": 3}
    assert parts.add_threshold(base="a_null", when="W1", rule=rule) == "a_null"
    assert parts.add_threshold(base="a_null", when="W2", rule=rule) == "a_null_2"
    assert parts.counters == ["W1 -> counter.a_null(1)", "W2 -> counter.a_null_2(1)"]
    assert parts.last_checks == [
        "and.nocontrib( eq( count_lines(), total_lines() ), gte( @a_null, 3 ) ) -> fail()",
        "and.nocontrib( eq( count_lines(), total_lines() ), gte( @a_null_2, 3 ) ) -> fail()",
    ]
    assert not parts.needs_full_scan


def test_odcs_csvpath_parts_add_threshold_bad_input() -> None:
    parts = CsvPathParts()
    with pytest.raises(ValueError):
        parts.add_threshold(base="", when="W", rule={"mustBe": 0})
    with pytest.raises(ValueError):
        parts.add_threshold(base="a", when=" ", rule={"mustBe": 0})
