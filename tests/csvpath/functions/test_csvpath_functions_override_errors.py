"""Errors from functions that override to_value(): count(), increment(),
first().

These do not go through Function.to_value(), so a check was due that
their errors are not silent. They are not: Expression records them. Two
things were wrong in what the user saw:
- a DataException printed as <class '...DataException'>, not its message;
- under an assignment, @x = increment(..), the error had an empty source,
  because the function never became the expression's current child.
"""

import os
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import DataException, MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _run(*, policy: str, match: str) -> tuple[CsvPath, list, list, Exception]:
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", policy)
    printed = []
    path.print = lambda msg, *args, **kwargs: printed.append(msg)
    raised = None
    lines = []
    path.parse(f"${PATH}[1][ {match} ]")
    try:
        lines = path.collect()
    except Exception as e:  # the type is part of what is tested
        raised = e
    return path, printed, lines, raised


def test_data_exception_str_is_its_message():
    assert str(DataException("increment value must be a positive int")) == (
        "increment value must be a positive int"
    )


def test_data_exception_with_no_message_names_its_class():
    assert str(DataException()) == "DataException"


def test_data_exception_is_still_a_match_exception():
    assert isinstance(DataException("x"), MatchException)


@pytest.mark.parametrize(
    "match",
    ['increment(yes(), "3")', "increment(yes(), 0)", "increment(yes(), 2.5)"],
)
def test_increment_error_says_what_is_wrong(match):
    path, printed, lines, raised = _run(policy="collect, print", match=match)
    assert raised is None
    assert lines == []
    assert [e.message for e in path.errors] == [
        "increment value must be a positive int"
    ]
    assert len(printed) == 1
    assert "positive int" in printed[0]


def test_increment_under_an_assignment_is_the_source():
    path, _, _, _ = _run(policy="collect", match='@x = increment(yes(), "3")')
    assert [e.source for e in path.errors] == ["increment[0]"]


def test_increment_error_in_raise_mode():
    path, printed, _, raised = _run(
        policy="raise, collect, print", match='@x = increment(yes(), "3")'
    )
    assert isinstance(raised, DataException)
    assert str(raised) == "increment value must be a positive int"
    assert [e.source for e in path.errors] == ["increment[0]"]
    assert len(printed) == 1


def test_count_under_an_assignment_is_the_source():
    # count's own error: a stack cannot be a tracking value
    path, _, _, _ = _run(policy="collect", match='push("s", "a") @x = count(@s)')
    assert [e.source for e in path.errors] == ["count[1]"]
    assert "unhashable" in path.errors[0].message


def test_an_error_below_count_keeps_its_own_source():
    # gt raised, so gt is the source, not count
    path, _, _, _ = _run(policy="collect", match='@x = count(gt("1,000", 9999))')
    assert [e.source for e in path.errors] == ["count[0].gt[0]"]


@pytest.mark.parametrize(
    "match,var,expected",
    [
        ("@x = count(yes())", "x", 1),
        ("@x = increment(yes(), 1)", "x", 1.0),
    ],
)
def test_no_error_no_change(match, var, expected):
    path, printed, lines, raised = _run(policy="raise, collect, print", match=match)
    assert raised is None
    assert path.errors == []
    assert path.variables[var] == expected


def test_first_no_error_no_change():
    path, _, lines, raised = _run(policy="raise, collect", match="first(#firstname)")
    assert raised is None
    assert path.errors == []
    assert len(lines) == 1
