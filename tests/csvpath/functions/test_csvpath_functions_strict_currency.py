"""integer() and decimal() are permissive: they accept a currency value like
"$10". With the strict qualifier they must not, because a currency symbol is
not a strict numeric character (David, 2026-11-14, with #633).

Before the fix, integer.strict("$10") and decimal.strict("$10.50") matched,
because both go through ExpressionUtility.to_int() / to_float(), which strip
$, euro and pound signs.

Commas fail strict too (David, 2026-11-15): see
test_csvpath_functions_strict_numbers.py.
datatype() calls Decimal._is_match(strict=True) to infer types; the currency
check is in Decimal._decide_match, so datatype() is unchanged.
"""

import os

import pytest

from csvpath.csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

STRICT = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}strict_currency.csv"

ALL = ["$10", "10", "10.5", "$10.50", "€10.50", "£3", "1,000", "1,000.50", " $3.99"]


def _matched(function: str) -> list[str]:
    path = CsvPath()
    path.parse(
        f"~ validation-mode: no-raise, no-print ~ ${STRICT}[1*][ line( {function}(#a) ) ]"
    )
    return [line[0] for line in path.collect()]


class TestCsvPathFunctionsStrictCurrency:
    def test_integer_accepts_currency(self):
        assert _matched("integer") == ["$10", "10", "£3", "1,000"]

    def test_integer_strict_rejects_currency(self):
        assert _matched("integer.strict") == ["10"]

    def test_decimal_accepts_currency(self):
        assert _matched("decimal") == ALL

    def test_decimal_strict_rejects_currency(self):
        #
        # strict decimal also requires a "." (unchanged), so 10, £3 and
        # 1,000 were never strict decimals. 1,000.50 has a comma.
        #
        assert _matched("decimal.strict") == ["10.5"]

    @pytest.mark.parametrize("function", ["integer.strict", "decimal.strict"])
    def test_strict_currency_raises_in_raise_mode(self, function):
        path = CsvPath()
        path.parse(
            f"~ validation-mode: raise, no-print ~ ${STRICT}[1][ line( {function}(#a) ) ]"
        )
        with pytest.raises(MatchException, match="currency symbol"):
            path.collect()

    def test_strict_currency_is_reported_in_collect_mode(self):
        path = CsvPath()
        path.parse(
            f"~ validation-mode: collect, no-raise, no-print ~ ${STRICT}[1][ line( integer.strict(#a) ) ]"
        )
        assert path.collect() == []
        #
        # line() adds its own two summary errors for any type mismatch.
        #
        ours = [e for e in path.errors if "currency symbol" in e.message]
        assert len(ours) == 1
        assert ours[0].message == "'$10' has 'strict' but contains a currency symbol"

    def test_datatype_inference_is_unchanged(self):
        path = CsvPath()
        path.parse(f"""${STRICT}[1*][ push.nocontrib("t", datatype(#a)) ]""")
        path.collect()
        assert path.variables["t"] == [
            "integer",
            "integer",
            "decimal",
            "decimal",
            "decimal",
            "integer",
            "integer",
            "decimal",
            "decimal",
        ]
