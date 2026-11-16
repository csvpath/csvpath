"""datatype.strict (David, 2026-11-15): a value is a decimal or an integer only
if decimal.strict() or integer.strict() would accept it. Plain datatype() is
unchanged: it stays permissive, like plain decimal() and integer().

The invariant tested here is that datatype.strict and the strict type
functions cannot disagree, because they share Decimal._strict_problem().
"""

import os

import pytest

from csvpath.csvpath import CsvPath

RESOURCES = f"tests{os.sep}csvpath{os.sep}test_resources"
NUMBERS = f"{RESOURCES}{os.sep}strict_numbers.csv"
CURRENCY = f"{RESOURCES}{os.sep}strict_currency.csv"


def _datatypes(file: str, function: str) -> list[str]:
    path = CsvPath()
    path.parse(f"""${file}[1*][ push.nocontrib("t", {function}(#a)) ]""")
    path.collect()
    return path.variables["t"]


def _values(file: str) -> list[str]:
    path = CsvPath()
    path.parse(f"""${file}[1*][ push.nocontrib("v", #a) ]""")
    path.collect()
    return path.variables["v"]


def _accepted(file: str, function: str) -> set[str]:
    path = CsvPath()
    path.parse(
        f"~ validation-mode: no-raise, no-print ~ ${file}[1*][ line( {function}(#a) ) ]"
    )
    return {line[0] for line in path.collect()}


class TestCsvPathFunctionsDatatypeStrict:
    @pytest.mark.parametrize("file", [NUMBERS, CURRENCY])
    def test_datatype_strict_agrees_with_the_strict_type_functions(self, file):
        values = _values(file)
        types = _datatypes(file, "datatype.strict")
        integers = _accepted(file, "integer.strict")
        decimals = _accepted(file, "decimal.strict")
        assert len(values) == len(types)
        for v, t in zip(values, types):
            assert (t == "integer") == (v in integers), (v, t)
            assert (t == "decimal") == (v in decimals), (v, t)

    def test_datatype_strict_on_currency(self):
        assert _datatypes(CURRENCY, "datatype.strict") == [
            "string",
            "integer",
            "decimal",
            "string",
            "string",
            "string",
            "string",
            "string",
            "string",
        ]

    def test_plain_datatype_is_unchanged(self):
        #
        # the same rows without strict: currency and commas are numbers
        #
        assert _datatypes(CURRENCY, "datatype") == [
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

    def test_strict_none_is_unchanged(self):
        #
        # datatype.strict already passed strict to none(): "nan" is a string
        # under strict and none() without it.
        #
        values = _values(NUMBERS)
        i = values.index("nan")
        assert _datatypes(NUMBERS, "datatype")[i] == "none"
        assert _datatypes(NUMBERS, "datatype.strict")[i] == "string"
