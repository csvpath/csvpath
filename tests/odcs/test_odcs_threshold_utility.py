import os

import pytest

from csvpath import CsvPath
from csvpath.odcs.threshold_utility import ThresholdUtility as thut

DATA = os.path.join(
    "tests",
    "odcs",
    "test_resources",
    "normative",
    "01_orders_simple",
    "data",
    "orders_mixed.csv",
)


def test_odcs_thut_operator() -> None:
    assert thut.operator(rule={"metric": "rowCount", "mustBe": 5}) == ("mustBe", 5)
    with pytest.raises(ValueError):
        thut.operator(rule={"metric": "rowCount"})
    with pytest.raises(ValueError):
        thut.operator(rule={"mustBe": 1, "mustNotBe": 2})
    with pytest.raises(TypeError):
        thut.operator(rule=None)


@pytest.mark.parametrize(
    "rule,zero",
    [
        ({"mustBe": 0}, True),
        ({"mustBeLessThan": 1}, True),
        ({"mustBeLessOrEqualTo": 0}, True),
        ({"mustBe": 1}, False),
        ({"mustBeLessThan": 3}, False),
        ({"mustBeLessOrEqualTo": 2}, False),
        ({"mustBeBetween": [0, 0]}, False),
        ({"mustBeGreaterThan": 0}, False),
    ],
)
def test_odcs_thut_is_zero_tolerance(rule: dict, zero: bool) -> None:
    assert thut.is_zero_tolerance(rule=rule) is zero


def test_odcs_thut_fail_when_text() -> None:
    v = "@x"
    assert thut.fail_when(value=v, rule={"mustBe": 0}) == "neq( @x, 0 )"
    assert thut.fail_when(value=v, rule={"mustNotBe": 0}) == "eq( @x, 0 )"
    assert thut.fail_when(value=v, rule={"mustBeGreaterThan": 0}) == "lte( @x, 0 )"
    assert thut.fail_when(value=v, rule={"mustBeGreaterOrEqualTo": 1}) == "gt( 1, @x )"
    assert thut.fail_when(value=v, rule={"mustBeLessThan": 3}) == "gte( @x, 3 )"
    assert thut.fail_when(value=v, rule={"mustBeLessOrEqualTo": 3}) == "gt( @x, 3 )"
    assert (
        thut.fail_when(value=v, rule={"mustBeBetween": [2, 4]})
        == "or( gt( 2, @x ), gt( @x, 4 ) )"
    )
    assert (
        thut.fail_when(value=v, rule={"mustNotBeBetween": [2, 4]})
        == "and( gte( @x, 2 ), gte( 4, @x ) )"
    )


def test_odcs_thut_fail_when_never_uses_lt() -> None:
    # lt(), below(), and before() behave as lte() -- issue #301
    for op in thut.OPERATORS:
        value = [1, 2] if "Between" in op else 1
        text = thut.fail_when(value="@x", rule={op: value})
        for bad in ["lt(", "below(", "before(", "not("]:
            assert bad not in text


def test_odcs_thut_fail_when_bad_input() -> None:
    with pytest.raises(ValueError):
        thut.fail_when(value="", rule={"mustBe": 0})
    with pytest.raises(ValueError):
        thut.fail_when(value="@x", rule={"mustBeBetween": [1]})
    with pytest.raises(TypeError):
        thut.fail_when(value="@x", rule={"mustBe": "zero"})


@pytest.mark.parametrize(
    "rule,value,broken",
    [
        ({"mustBe": 0}, 0, False),
        ({"mustBe": 0}, 1, True),
        ({"mustNotBe": 0}, 0, True),
        ({"mustNotBe": 0}, 1, False),
        ({"mustBeGreaterThan": 3}, 3, True),
        ({"mustBeGreaterThan": 3}, 4, False),
        ({"mustBeGreaterOrEqualTo": 3}, 2, True),
        ({"mustBeGreaterOrEqualTo": 3}, 3, False),
        ({"mustBeLessThan": 3}, 3, True),
        ({"mustBeLessThan": 3}, 2, False),
        ({"mustBeLessOrEqualTo": 3}, 4, True),
        ({"mustBeLessOrEqualTo": 3}, 3, False),
        ({"mustBeBetween": [2, 4]}, 1, True),
        ({"mustBeBetween": [2, 4]}, 2, False),
        ({"mustBeBetween": [2, 4]}, 4, False),
        ({"mustBeBetween": [2, 4]}, 5, True),
        ({"mustNotBeBetween": [2, 4]}, 1, False),
        ({"mustNotBeBetween": [2, 4]}, 2, True),
        ({"mustNotBeBetween": [2, 4]}, 4, True),
        ({"mustNotBeBetween": [2, 4]}, 5, False),
    ],
)
def test_odcs_thut_fail_when_runs_in_csvpath(
    rule: dict, value: int, broken: bool
) -> None:
    #
    # each condition, evaluated by CsvPath on a counter-like variable at
    # the boundaries, fails the run exactly when the rule is broken
    #
    condition = thut.fail_when(value="@v", rule=rule)
    path = CsvPath()
    path.collect(
        f"""~ validation-mode: print, no-raise, no-fail, no-stop ~
        ${DATA}[*][
            first_line.nocontrib() -> @v = {value}
            and.nocontrib( eq( count_lines(), total_lines() ), {condition} ) -> fail()
        ]"""
    )
    assert path.is_valid is (not broken)


def test_odcs_thut_percent() -> None:
    assert thut.is_percent(rule={"unit": "percent"}) is True
    assert thut.is_percent(rule={"unit": "rows"}) is False
    assert thut.is_percent(rule={}) is False
    with pytest.raises(TypeError):
        thut.is_percent(rule=None)


def test_odcs_thut_zero_tolerance_percent() -> None:
    # fewer than 1 row means none; fewer than 1 percent does not
    assert thut.is_zero_tolerance(rule={"mustBeLessThan": 1}) is True
    assert (
        thut.is_zero_tolerance(rule={"mustBeLessThan": 1, "unit": "percent"}) is False
    )
    assert thut.is_zero_tolerance(rule={"mustBe": 0, "unit": "percent"}) is True


def test_odcs_thut_count_value() -> None:
    assert thut.count_value(var="a_null", rule={"mustBe": 0}) == "@a_null"
    assert thut.count_value(var="a_null", rule={"mustBe": 0, "unit": "percent"}) == (
        "multiply( divide( @a_null, subtract(total_lines(), 1) ), 100 )"
    )
    with pytest.raises(ValueError):
        thut.count_value(var="", rule={"mustBe": 0})


@pytest.mark.parametrize(
    "text,fires_at",
    [
        ("a\n", [0]),
        ("a\nx\ny\n", [2]),
        ("a\nx\ny\n\n", [2]),
        ("a\nx\n\ny\n\n\n", [3]),
        ("a\n\n", [0]),
    ],
)
def test_odcs_thut_last_data_line(tmp_path, text: str, fires_at: list) -> None:
    #
    # true exactly once, on the last line with data, whatever blank lines
    # follow or sit in between. last() composed in and() does not run on a
    # frozen blank last line, which is why the converter uses this instead.
    #
    data = tmp_path / "data.csv"
    data.write_text(text, encoding="utf-8")
    path = CsvPath()
    path.collect(
        f"""~ validation-mode: print, no-raise, no-fail, no-stop ~
        ${data}[*][
            {thut.LAST_DATA_LINE} -> push("at", line_number())
        ]"""
    )
    assert path.variables.get("at") == fires_at
