"""Truth tables for the boolean match deciders and(), or(), not(), nand() and nor().

The semantics asserted here come from the function docs:

- and()  docs/func_gen/and.md   True when all its match components are True
- or()   docs/functions/andor.md  True when any one of its components is True
- not()  docs/func_gen/not.md   the boolean inverse of its argument
- nand() docs/func_gen/nand.md  False if its contained components are all True,
                                i.e. not(and())
- nor()  docs/func_gen/nor.md   True if its contained components are all False,
                                i.e. not(or())

yes() and no() are used as the inputs because docs/functions/no.md says they
always match and never match, so they give fixed True and False operands that
do not depend on the data.

Each case runs on line 1 of test.csv only, so a single evaluation decides the
assigned variable. Two kinds of test are here:

- the value of the function, read back from an assigned variable
- the match of the function, used as a bare match component, read back as
  whether line 1 was collected

Both matter because the deciders produce their value by calling their own
matches(), and a regression in either path would be invisible to the other.

none() arguments are deliberately not covered. See the PR body: the docs say an
explicit None is considered False, but none() currently matches True inside
these functions, so that case is reported as a finding rather than pinned.
"""

import os

import pytest

from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

T = "yes()"
F = "no()"


def _assigned_value(*, expression: str):
    """Assigns the expression to @result on line 1 and returns @result."""
    path = CsvPath()
    path.parse(f"${PATH}[1][ @result = {expression} ]")
    path.fast_forward()
    assert "result" in path.variables
    return path.variables["result"]


def _line_matches(*, expression: str) -> bool:
    """Uses the expression as the only match component on line 1."""
    path = CsvPath()
    path.parse(f"${PATH}[1][ {expression} ]")
    lines = path.collect()
    # only line 1 is in scope, so there is either one line or none
    assert len(lines) in (0, 1)
    return len(lines) == 1


# (left operand, right operand, and, or, nand, nor)
TWO_ARG_TABLE = [
    (T, T, True, True, False, False),
    (T, F, False, True, True, False),
    (F, T, False, True, True, False),
    (F, F, False, False, True, True),
]


def _two_arg_cases(*, column: int) -> list:
    return [(row[0], row[1], row[column]) for row in TWO_ARG_TABLE]


@pytest.mark.parametrize("a,b,expected", _two_arg_cases(column=2))
def test_and_two_arg_truth_table(a, b, expected):
    expression = f"and({a}, {b})"
    assert _assigned_value(expression=expression) is expected
    assert _line_matches(expression=expression) is expected


@pytest.mark.parametrize("a,b,expected", _two_arg_cases(column=3))
def test_or_two_arg_truth_table(a, b, expected):
    expression = f"or({a}, {b})"
    assert _assigned_value(expression=expression) is expected
    assert _line_matches(expression=expression) is expected


@pytest.mark.parametrize("a,b,expected", _two_arg_cases(column=4))
def test_nand_two_arg_truth_table(a, b, expected):
    expression = f"nand({a}, {b})"
    assert _assigned_value(expression=expression) is expected
    assert _line_matches(expression=expression) is expected


@pytest.mark.parametrize("a,b,expected", _two_arg_cases(column=5))
def test_nor_two_arg_truth_table(a, b, expected):
    expression = f"nor({a}, {b})"
    assert _assigned_value(expression=expression) is expected
    assert _line_matches(expression=expression) is expected


@pytest.mark.parametrize("a,b", [(row[0], row[1]) for row in TWO_ARG_TABLE])
def test_nand_is_not_and(a, b):
    # nand() should agree with not() wrapped around and() on every input
    nand = _assigned_value(expression=f"nand({a}, {b})")
    not_and = _assigned_value(expression=f"not(and({a}, {b}))")
    assert nand is not_and


@pytest.mark.parametrize("a,b", [(row[0], row[1]) for row in TWO_ARG_TABLE])
def test_nor_is_not_or(a, b):
    # nor() should agree with not() wrapped around or() on every input
    nor = _assigned_value(expression=f"nor({a}, {b})")
    not_or = _assigned_value(expression=f"not(or({a}, {b}))")
    assert nor is not_or


@pytest.mark.parametrize("a,expected", [(T, False), (F, True)])
def test_not_truth_table(a, expected):
    expression = f"not({a})"
    assert _assigned_value(expression=expression) is expected
    assert _line_matches(expression=expression) is expected


# three operands: every arrangement that has a different count of True values,
# plus the single odd one out in each position, because the deciders loop over
# their operands and can stop early.
THREE_ARG_TABLE = [
    # (operands, and, or, nand, nor)
    ((T, T, T), True, True, False, False),
    ((F, T, T), False, True, True, False),
    ((T, F, T), False, True, True, False),
    ((T, T, F), False, True, True, False),
    ((T, F, F), False, True, True, False),
    ((F, T, F), False, True, True, False),
    ((F, F, T), False, True, True, False),
    ((F, F, F), False, False, True, True),
]


@pytest.mark.parametrize(
    "operands,expected", [(row[0], row[1]) for row in THREE_ARG_TABLE]
)
def test_and_three_arg(operands, expected):
    expression = f"and({', '.join(operands)})"
    assert _assigned_value(expression=expression) is expected
    assert _line_matches(expression=expression) is expected


@pytest.mark.parametrize(
    "operands,expected", [(row[0], row[2]) for row in THREE_ARG_TABLE]
)
def test_or_three_arg(operands, expected):
    expression = f"or({', '.join(operands)})"
    assert _assigned_value(expression=expression) is expected
    assert _line_matches(expression=expression) is expected


@pytest.mark.parametrize(
    "operands,expected", [(row[0], row[3]) for row in THREE_ARG_TABLE]
)
def test_nand_three_arg(operands, expected):
    expression = f"nand({', '.join(operands)})"
    assert _assigned_value(expression=expression) is expected
    assert _line_matches(expression=expression) is expected


@pytest.mark.parametrize(
    "operands,expected", [(row[0], row[4]) for row in THREE_ARG_TABLE]
)
def test_nor_three_arg(operands, expected):
    expression = f"nor({', '.join(operands)})"
    assert _assigned_value(expression=expression) is expected
    assert _line_matches(expression=expression) is expected


@pytest.mark.parametrize(
    "expression,expected",
    [
        # line 1 is David Kermit: both equalities are True
        ('nand(#firstname == "David", #lastname == "Kermit")', False),
        ('nand(#firstname == "David", #lastname == "Bat")', True),
        ('nor(#firstname == "Frog", #lastname == "Bat")', True),
        ('nor(#firstname == "David", #lastname == "Bat")', False),
    ],
)
def test_nand_nor_with_header_equalities(expression, expected):
    # the docs call the operands match components, so equalities over
    # headers must work the same way yes() and no() do
    assert _assigned_value(expression=expression) is expected


@pytest.mark.parametrize("function", ["nand", "nor"])
def test_nand_nor_need_at_least_two_args(function):
    # the data and call signatures in docs/func_gen/nand.md and nor.md
    # both list two required arguments, so one argument is a language error.
    # raise mode is set explicitly so the test does not depend on the
    # config's [errors] policy.
    path = CsvPath()
    with pytest.raises(ChildrenException):
        path.parse(
            f"~ validation-mode: raise ~ ${PATH}[1][ @result = {function}(yes()) ]"
        )
        path.fast_forward()
