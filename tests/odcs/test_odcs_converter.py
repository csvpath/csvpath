"""SchemaObjectConverter and OdcsConverter, plus small end-to-end runs of
generated csvpaths for rules the normative pairs do not cover."""

import copy

import pytest

from csvpath import CsvPath
from csvpath.odcs import OdcsConverter, OdcsException
from csvpath.odcs.conversion_report import ConversionReport
from csvpath.odcs.schema_object_converter import SchemaObjectConverter


def _contract(*objects: dict) -> dict:
    return {
        "apiVersion": "v3.2.0",
        "kind": "DataContract",
        "id": "c1",
        "version": "1.0.0",
        "status": "active",
        "schema": list(objects),
    }


def _obj(name: str = "t", **extra) -> dict:
    obj = {"name": name, "properties": [{"name": "a", "logicalType": "string"}]}
    obj.update(extra)
    return obj


def _run(*, csvpath: str, tmp_path, text: str) -> tuple[list, bool]:
    data = tmp_path / "data.csv"
    data.write_text(text, encoding="utf-8")
    path = CsvPath()
    lines = path.collect(csvpath.replace("$[", f"${data}[", 1))
    return lines, path.is_valid


# ============================
# SchemaObjectConverter
# ============================


def test_odcs_schema_object_converter_bad_input() -> None:
    report = ConversionReport()
    with pytest.raises(TypeError):
        SchemaObjectConverter(contract=None, obj=_obj(), report=report)
    with pytest.raises(TypeError):
        SchemaObjectConverter(contract=_contract(), obj=None, report=report)
    with pytest.raises(TypeError):
        SchemaObjectConverter(contract=_contract(), obj=_obj(), report=None)
    with pytest.raises(ValueError):
        SchemaObjectConverter(contract=_contract(), obj={"name": ""}, report=report)


def test_odcs_schema_object_converter_metadata() -> None:
    text = SchemaObjectConverter(
        contract=_contract(), obj=_obj(), report=ConversionReport()
    ).convert()
    assert text.startswith(
        "~\n"
        "  id: t\n"
        "  odcs-contract-id: c1\n"
        "  odcs-contract-version: 1.0.0\n"
        "  odcs-schema-object: t\n"
        "  validation-mode: print, no-raise, no-fail, no-stop\n"
        "~\n"
        "$[1*][\n"
    )


def test_odcs_schema_object_converter_no_properties() -> None:
    with pytest.raises(OdcsException):
        SchemaObjectConverter(
            contract=_contract(), obj={"name": "t"}, report=ConversionReport()
        ).convert()


def test_odcs_schema_object_converter_row_count() -> None:
    obj = _obj(quality=[{"metric": "rowCount", "mustBeBetween": [1, 2]}])
    text = SchemaObjectConverter(
        contract=_contract(), obj=obj, report=ConversionReport()
    ).convert()
    assert (
        "    and.nocontrib( last(), or( gt( 1, subtract(total_lines(), 1) ), "
        "gt( subtract(total_lines(), 1), 2 ) ) ) -> fail()\n"
        "    first_line.nocontrib() -> skip()\n"
    ) in text


def test_odcs_schema_object_converter_skips() -> None:
    obj = _obj(
        quality=[
            {
                "metric": "duplicateValues",
                "arguments": {"properties": ["a"]},
                "mustBe": 0,
            },
            {"type": "sql", "query": "SELECT 1", "mustBe": 1},
        ],
        relationships=[{"from": "t.a", "to": "u.b"}],
    )
    report = ConversionReport()
    SchemaObjectConverter(contract=_contract(), obj=obj, report=report).convert()
    assert [(s.location, s.feature) for s in report.skipped] == [
        ("quality[0]", "quality.duplicateValues"),
        ("quality[1]", "quality.sql"),
        ("relationships[0]", "relationship"),
    ]


# ============================
# OdcsConverter
# ============================


def test_odcs_converter_bad_input() -> None:
    with pytest.raises(ValueError):
        OdcsConverter(contract=None)
    with pytest.raises(TypeError):
        OdcsConverter(contract=[])
    bad = _contract(_obj())
    bad["apiVersion"] = "v2.2.2"
    with pytest.raises(OdcsException):
        OdcsConverter(contract=bad)


def test_odcs_converter_no_schema() -> None:
    with pytest.raises(OdcsException):
        OdcsConverter(contract=_contract()).convert()


def test_odcs_converter_duplicate_object_names() -> None:
    with pytest.raises(OdcsException):
        OdcsConverter(contract=_contract(_obj("t"), _obj("t"))).convert()


def test_odcs_converter_keeps_contract_order_and_does_not_mutate() -> None:
    contract = _contract(_obj("z"), _obj("a"))
    before = copy.deepcopy(contract)
    conversion = OdcsConverter(contract=contract).convert()
    assert list(conversion.csvpaths) == ["z", "a"]
    assert contract == before


# ============================
# end to end, beyond the pairs
# ============================


def test_odcs_converter_null_values_threshold_runs(tmp_path) -> None:
    obj = {
        "name": "t",
        "properties": [
            {"name": "id", "logicalType": "integer", "required": True},
            {
                "name": "note",
                "logicalType": "string",
                "quality": [{"metric": "nullValues", "mustBeLessThan": 2}],
            },
        ],
    }
    csvpath = OdcsConverter(contract=_contract(obj)).convert().csvpaths["t"]
    one_null = "id,note\n1,a\n2,\n3,c\n"
    lines, valid = _run(csvpath=csvpath, tmp_path=tmp_path, text=one_null)
    assert [line[0] for line in lines] == ["1", "3"] and valid is True
    two_nulls = "id,note\n1,a\n2,\n3,\n"
    lines, valid = _run(csvpath=csvpath, tmp_path=tmp_path, text=two_nulls)
    assert [line[0] for line in lines] == ["1"] and valid is False


def test_odcs_converter_row_count_range_runs(tmp_path) -> None:
    obj = _obj(quality=[{"metric": "rowCount", "mustBeBetween": [1, 2]}])
    csvpath = OdcsConverter(contract=_contract(obj)).convert().csvpaths["t"]
    for text, valid in [
        ("a\n", False),
        ("a\nx\n", True),
        ("a\nx\ny\n", True),
        ("a\nx\ny\nz\n", False),
    ]:
        _, is_valid = _run(csvpath=csvpath, tmp_path=tmp_path, text=text)
        assert is_valid is valid, text


def test_odcs_converter_quoted_and_indexed_headers_run(tmp_path) -> None:
    obj = {
        "name": "t",
        "properties": [
            {"name": "Order ID", "logicalType": "integer", "required": True},
            {"name": "price($)", "logicalType": "number", "required": True},
        ],
    }
    csvpath = OdcsConverter(contract=_contract(obj)).convert().csvpaths["t"]
    assert '#"Order ID"' in csvpath and "#1" in csvpath
    text = "Order ID,price($)\n1,2.50\nx,2.50\n3,\n"
    lines, _ = _run(csvpath=csvpath, tmp_path=tmp_path, text=text)
    assert lines == [["1", "2.50"]]
