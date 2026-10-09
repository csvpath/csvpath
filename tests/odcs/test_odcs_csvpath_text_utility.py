import re

import pytest

from csvpath import CsvPath
from csvpath.odcs.csvpath_text_utility import CsvPathTextUtility as csut


@pytest.mark.parametrize(
    "name,expected",
    [
        ("order_id", "#order_id"),
        ("order-id", "#order-id"),
        ("order.id", "#order.id"),
        ("Order ID", '#"Order ID"'),
        ("price($)", "#3"),
        ("42", "#3"),
    ],
)
def test_odcs_csut_header(name: str, expected: str) -> None:
    assert csut.header(name=name, index=3) == expected


def test_odcs_csut_header_bad_input() -> None:
    with pytest.raises(ValueError):
        csut.header(name="", index=0)
    with pytest.raises(ValueError):
        csut.header(name=None, index=0)
    with pytest.raises(ValueError):
        csut.header(name="a", index=-1)
    with pytest.raises(ValueError):
        csut.header(name="a", index=True)


def test_odcs_csut_string() -> None:
    assert csut.string(value="%Y-%m-%d") == '"%Y-%m-%d"'
    assert csut.string(value="") == '""'
    with pytest.raises(ValueError):
        csut.string(value='say "hi"')
    with pytest.raises(TypeError):
        csut.string(value=5)


def test_odcs_csut_in_values() -> None:
    assert csut.in_values(values=["open", "shipped"]) == '"open|shipped"'
    assert csut.in_values(values=[1, 2.5, True]) == '"1|2.5|true"'
    with pytest.raises(ValueError):
        csut.in_values(values=[])
    with pytest.raises(ValueError):
        csut.in_values(values=["a|b"])
    with pytest.raises(ValueError):
        csut.in_values(values=['a"b'])
    with pytest.raises(ValueError):
        csut.in_values(values=[None])
    with pytest.raises(ValueError):
        csut.in_values(values=[["nested"]])


@pytest.mark.parametrize(
    "pattern,expected",
    [
        ("^ORD-[0-9]{6}$", "/^ORD-[0-9]{6}$/"),
        ("^[A-Z]+/[0-9]+$", r"/^[A-Z]+\/[0-9]+$/"),
        (r"^[A-Z]+\/[0-9]+$", r"/^[A-Z]+\/[0-9]+$/"),
        ("abc/", r"/(?:abc\/)/"),
        ("/abc", r"/(?:\/abc)/"),
        (r"\d+\.\d{2}", r"/\d+\.\d{2}/"),
    ],
)
def test_odcs_csut_regex(pattern: str, expected: str) -> None:
    assert csut.regex(pattern=pattern) == expected


def test_odcs_csut_regex_bad_input() -> None:
    with pytest.raises(ValueError):
        csut.regex(pattern="^(?<code>[A-Z]{3})$")
    with pytest.raises(ValueError):
        csut.regex(pattern="")
    with pytest.raises(ValueError):
        csut.regex(pattern=None)


def test_odcs_csut_regex_literals_run_in_csvpath(tmp_path) -> None:
    #
    # the literals must survive the CsvPath grammar and regex() and still
    # mean the original pattern
    #
    data = tmp_path / "routes.csv"
    data.write_text("route\nABC/123\nABC-123\nabc/\n/abc\n", encoding="utf-8")
    cases = [
        ("^[A-Z]+/[0-9]+$", ["ABC/123"]),
        ("abc/$", ["abc/"]),
        ("^/abc", ["/abc"]),
    ]
    for pattern, expected in cases:
        literal = csut.regex(pattern=pattern)
        lines = CsvPath().collect(
            f"""~ validation-mode: print, no-raise ~
            ${data}[1*][ regex({literal}, #route) ]"""
        )
        assert [line[0] for line in lines] == expected, pattern
        assert [v for v in expected if re.search(pattern, v)] == expected


def test_odcs_csut_number() -> None:
    assert csut.number(value=10) == "10"
    assert csut.number(value=10.0) == "10"
    assert csut.number(value=0.5) == "0.5"
    assert csut.number(value=-3) == "-3"
    with pytest.raises(TypeError):
        csut.number(value="10")
    with pytest.raises(TypeError):
        csut.number(value=True)


def test_odcs_csut_variable() -> None:
    assert csut.variable(name="currency", suffix="invalid") == "currency_invalid"
    assert csut.variable(name="Order ID", suffix="null") == "order_id_null"
    with pytest.raises(ValueError):
        csut.variable(name="", suffix="null")
    with pytest.raises(ValueError):
        csut.variable(name="a", suffix="")
