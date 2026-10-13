"""A data file path in the converted csvpath's root, for stand-alone runs.

OdcsConverter.convert(path=...) puts the data file in each csvpath's root,
$orders.csv[*][...], so the csvpath runs with a CsvPath alone, with no
string manipulation. Without a path the root is $[*][...], as named-paths
groups need, and the output is unchanged. A path is for a contract with
one table; it must exist and be usable in a csvpath root.
"""

import os

import pytest
import yaml

from csvpath import CsvPath
from csvpath.odcs.csvpath_parts import CsvPathParts
from csvpath.odcs.csvpath_text_utility import CsvPathTextUtility as csut
from csvpath.odcs.odcs_contract_loader import OdcsContractLoader
from csvpath.odcs.odcs_converter import OdcsConverter
from csvpath.odcs.schema_object_converter import SchemaObjectConverter
from csvpath.odcs.conversion_report import ConversionReport
import csvpath.odcs.odcs_converter as odcs_converter_module

from tests.odcs.test_odcs_normative_pairs import _data_lines, _run_id, _runs

NORMATIVE = os.path.join("tests", "odcs", "test_resources", "normative")
ORDERS = os.path.join(NORMATIVE, "01_orders_simple")
CRM = os.path.join(NORMATIVE, "02_crm_two_tables")
ORDERS_DATA = os.path.join(ORDERS, "data", "orders_mixed.csv")
MISSING = os.path.join(ORDERS, "data", "no_such_file.csv")


def _contract(pair: str) -> dict:
    return OdcsContractLoader.from_path(path=os.path.join(pair, "contract.yaml"))


def _expected(pair: str, name: str) -> str:
    with open(os.path.join(pair, "expected", f"{name}.csvpath"), encoding="utf-8") as f:
        return f.read()


#
# csut.data_path() and existing_data_path()
#


def test_data_path_none_is_no_path() -> None:
    assert csut.data_path(path=None) == ""
    assert csut.existing_data_path(path=None) == ""


def test_data_path_valid() -> None:
    assert csut.data_path(path="data/orders.csv") == "data/orders.csv"
    assert csut.data_path(path="C:\\data\\orders.csv") == "C:\\data\\orders.csv"


def test_data_path_wrong_type() -> None:
    with pytest.raises(TypeError):
        csut.data_path(path=1)


@pytest.mark.parametrize("bad", ["", "   "])
def test_data_path_empty(bad: str) -> None:
    with pytest.raises(ValueError, match="pass None"):
        csut.data_path(path=bad)


@pytest.mark.parametrize(
    "bad", ["orders[1].csv", "orders].csv", "a\nb.csv", "a\rb.csv"]
)
def test_data_path_cannot_break_the_root(bad: str) -> None:
    with pytest.raises(ValueError, match="csvpath root"):
        csut.data_path(path=bad)


def test_existing_data_path() -> None:
    assert csut.existing_data_path(path=ORDERS_DATA) == ORDERS_DATA
    with pytest.raises(ValueError, match="No data file"):
        csut.existing_data_path(path=MISSING)


#
# CsvPathParts.render()
#


def _parts(*, full_scan: bool) -> CsvPathParts:
    parts = CsvPathParts(line_args=["string(#a)"])
    if full_scan:
        parts.first_checks.append("yes()")
    return parts


@pytest.mark.parametrize("full_scan,scan", [(True, "[*]"), (False, "[1*]")])
def test_render_without_path(full_scan: bool, scan: str) -> None:
    text = _parts(full_scan=full_scan).render()
    assert f"\n${scan}[\n" in text
    assert text == _parts(full_scan=full_scan).render(path=None)


@pytest.mark.parametrize("full_scan,scan", [(True, "[*]"), (False, "[1*]")])
def test_render_with_path(full_scan: bool, scan: str) -> None:
    text = _parts(full_scan=full_scan).render(path="data/orders.csv")
    assert f"\n$data/orders.csv{scan}[\n" in text
    #
    # the path is in the root only
    #
    assert text.count("data/orders.csv") == 1
    assert text.replace("data/orders.csv", "") == _parts(full_scan=full_scan).render()


def test_render_rejects_a_bad_path() -> None:
    with pytest.raises(ValueError):
        _parts(full_scan=False).render(path="a[b].csv")


#
# SchemaObjectConverter.convert(path=...)
#


def _object_converter(pair: str) -> SchemaObjectConverter:
    contract = OdcsContractLoader.validate(contract=_contract(pair))
    return SchemaObjectConverter(
        contract=contract, obj=contract["schema"][0], report=ConversionReport()
    )


def test_schema_object_converter_path() -> None:
    expected = _expected(ORDERS, "orders")
    assert _object_converter(ORDERS).convert() == expected
    with_path = _object_converter(ORDERS).convert(path=ORDERS_DATA)
    assert with_path == expected.replace("\n$[", f"\n${ORDERS_DATA}[", 1)


def test_schema_object_converter_missing_file() -> None:
    with pytest.raises(ValueError, match="No data file"):
        _object_converter(ORDERS).convert(path=MISSING)


#
# OdcsConverter.convert(path=...)
#


def test_converter_without_path_unchanged() -> None:
    conversion = OdcsConverter(contract=_contract(ORDERS)).convert()
    assert conversion.csvpaths["orders"] == _expected(ORDERS, "orders")


def test_converter_with_path() -> None:
    conversion = OdcsConverter(contract=_contract(ORDERS)).convert(path=ORDERS_DATA)
    assert conversion.csvpaths["orders"] == _expected(ORDERS, "orders").replace(
        "\n$[", f"\n${ORDERS_DATA}[", 1
    )


def test_converter_checks_the_file_before_converting(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("conversion started before the path was checked")

    monkeypatch.setattr(odcs_converter_module, "SchemaObjectConverter", fail)
    with pytest.raises(ValueError, match="No data file"):
        OdcsConverter(contract=_contract(ORDERS)).convert(path=MISSING)


def test_converter_path_is_for_one_table() -> None:
    data = os.path.join(CRM, "data", os.listdir(os.path.join(CRM, "data"))[0])
    with pytest.raises(ValueError, match="customers, payments"):
        OdcsConverter(contract=_contract(CRM)).convert(path=data)
    #
    # without a path a multi-table contract converts as before
    #
    assert len(OdcsConverter(contract=_contract(CRM)).convert().csvpaths) == 2


#
# stand-alone runs: every single-table normative run, with a path and a
# CsvPath alone, gives the expected lines and is_valid
#


def _single_table_runs() -> list:
    runs = []
    for pair, run in _runs():
        with open(os.path.join(pair, "contract.yaml"), encoding="utf-8") as f:
            if len(yaml.safe_load(f).get("schema") or []) == 1:
                runs.append((pair, run))
    return runs


@pytest.mark.parametrize("pair,run", _single_table_runs(), ids=_run_id)
def test_stand_alone_run_with_path(pair: str, run: dict) -> None:
    data_path = os.path.join(pair, "data", run["data"])
    name = run["csvpath"][: -len(".csvpath")]
    conversion = OdcsConverter(contract=_contract(pair)).convert(path=data_path)
    path = CsvPath()
    matched = path.collect(conversion.csvpaths[name])
    lines = _data_lines(data_path)
    assert matched == [lines[i] for i in run["valid_lines"]]
    assert path.is_valid is run["is_valid"]
