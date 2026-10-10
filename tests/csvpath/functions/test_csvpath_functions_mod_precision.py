"""mod() gives exact remainders for decimal operands (issue #305).

mod() used to compute a float modulo and round it to 2 places. Float noise
made real multiples look like non-multiples (0.3 % 0.1 came out as 0.1),
and the rounding made small real remainders look like 0 (10.001 % 5 came
out as 0.0).
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _mod(expression: str) -> float:
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", "raise")
    path.parse(f"${PATH}[1][ @r = {expression} ]")
    path.fast_forward()
    return path.variables["r"]


@pytest.mark.parametrize(
    "dividend,divisor,expected",
    [
        #
        # the rows from issue #305
        #
        ("0.3", "0.1", 0.0),
        ("1.15", "0.05", 0.0),
        ("10.001", "5", 0.001),
        ("10", "5", 0.0),
        #
        # more of each kind of error the rounding caused
        #
        ("10.2", "0.03", 0.0),
        ("10.123", "1", 0.123),
        ("0.0000001", "2", 1e-07),
        #
        # integers were already exact and stay the same
        #
        ("7", "3", 1.0),
        ("9", "3", 0.0),
    ],
)
def test_function_mod_precision(dividend: str, divisor: str, expected: float) -> None:
    assert _mod(f"mod({dividend}, {divisor})") == expected


@pytest.mark.parametrize(
    "dividend,divisor",
    [
        ("-7", "3"),
        ("7", "-3"),
        ("-7", "-3"),
        ("-0.3", "0.1"),
        ("10.001", "-3"),
        ("-10.123", "0.5"),
    ],
)
def test_function_mod_sign_follows_python(dividend: str, divisor: str) -> None:
    #
    # the result takes the divisor's sign, as Python's float modulo does
    #
    result = _mod(f"mod({dividend}, {divisor})")
    python = float(dividend) % float(divisor)
    assert result == pytest.approx(python, abs=1e-9)
    if result != 0:
        assert (result < 0) == (float(divisor) < 0)


def test_function_mod_huge_dividend_falls_back_to_float() -> None:
    #
    # the quotient is too large for an exact Decimal remainder, so the plain
    # float result is kept, unrounded. (written out in full: CsvPath does not
    # accept exponent literals such as 1e30.)
    #
    assert _mod("mod(1000000000000000000000000000000, 0.1)") == 1e30 % 0.1


def test_function_mod_zero_divisor_still_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        _mod("mod(5, 0)")


def test_function_mod_multiple_of_check_on_cells(tmp_path) -> None:
    #
    # eq( mod(#c, 0.05), 0 ) is the check the ODCS converter would emit for
    # multipleOf: 0.05. before #305 it accepted 10.001 and rejected 0.3, 1.15,
    # and 10. infinite, non-numeric, and empty cells do not match.
    #
    data = tmp_path / "multiples.csv"
    data.write_text(
        "id,c\n1,0.3\n2,1.15\n3,10.001\n4,10\n5,-7\n6,inf\n7,abc\n8,\n",
        encoding="utf-8",
    )
    path = CsvPath()
    lines = path.collect(
        f"~ validation-mode: print, no-raise ~ ${data}[1*][ eq( mod(#c, 0.05), 0 ) ]"
    )
    assert [line[0] for line in lines] == ["1", "2", "4", "5"]
