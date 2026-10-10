"""boolean() matches valid booleans only, wherever it is used (issue #302).

boolean() reports a validation error for an invalid value such as the word
"perhaps". At the top level, and inside line() and and(), that error alone
fails the line. or() is different: it drops its branches' errors when any
branch matches. While boolean() matched invalid values, or() saw a matching
branch and accepted the line.

Data, one row per kind of value in column b:

    id,b
    1,true
    2,false
    3,1
    4,0
    5,perhaps     an invalid value
    6,            empty: matches unless notnone (issue #300)
    7,TRUE
"""

import pytest

from csvpath import CsvPath

DATA = "id,b\n1,true\n2,false\n3,1\n4,0\n5,perhaps\n6,\n7,TRUE\n"


def _matched_ids(*, tmp_path, expression: str, mode: str) -> list[str]:
    data = tmp_path / "booleans.csv"
    data.write_text(DATA, encoding="utf-8")
    path = CsvPath()
    lines = path.collect(f"~ validation-mode: {mode} ~ ${data}[1*][ {expression} ]")
    return [line[0] for line in lines]


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("boolean(#b)", ["1", "2", "3", "4", "6", "7"]),
        ("or( no(), boolean(#b) )", ["1", "2", "3", "4", "6", "7"]),
        ("or( empty(#b), boolean(#b) )", ["1", "2", "3", "4", "6", "7"]),
        ("and( yes(), boolean(#b) )", ["1", "2", "3", "4", "6", "7"]),
        ("boolean.strict(#b)", ["1", "2", "6", "7"]),
        ("or( no(), boolean.strict(#b) )", ["1", "2", "6", "7"]),
        #
        # not() inverts boolean()'s match, so it matches the invalid row 5,
        # but boolean() also reports a validation error for row 5, and in
        # this validation mode any error fails the line. the empty row 6
        # matches boolean() (issue #300), so not() rejects it.
        #
        ("not( boolean(#b) )", []),
    ],
)
def test_validity_boolean_nested(tmp_path, expression: str, expected: list) -> None:
    ids = _matched_ids(tmp_path=tmp_path, expression=expression, mode="print, no-raise")
    assert ids == expected


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("boolean(#b)", ["1", "2", "3", "4", "6", "7"]),
        ("or( no(), boolean(#b) )", ["1", "2", "3", "4", "6", "7"]),
        ("line( string(#id), boolean(#b) )", ["1", "2", "3", "4", "6", "7"]),
        #
        # in match mode errors do not fail the line, so not() of a
        # non-matching boolean() matches the invalid row 5. the empty row 6
        # matches boolean() (issue #300), so not() rejects it.
        #
        ("not( boolean(#b) )", ["5"]),
    ],
)
def test_validity_boolean_match_mode(tmp_path, expression: str, expected: list) -> None:
    #
    # with validation-mode match, an invalid value still does not match,
    # the same as for integer() below
    #
    ids = _matched_ids(
        tmp_path=tmp_path, expression=expression, mode="print, no-raise, match"
    )
    assert ids == expected


def test_validity_integer_match_mode_for_comparison(tmp_path) -> None:
    #
    # the behavior boolean() is consistent with: integer() does not match an
    # invalid value in match mode either
    #
    data = tmp_path / "integers.csv"
    data.write_text("id,n\n1,5\n2,abc\n", encoding="utf-8")
    path = CsvPath()
    lines = path.collect(
        f"~ validation-mode: print, no-raise, match ~ ${data}[1*][ integer(#n) ]"
    )
    assert [line[0] for line in lines] == ["1"]
