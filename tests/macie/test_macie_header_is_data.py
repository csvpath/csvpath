"""When the first line of a file holds a value an identifier finds, it is
data, not a header (#479; live probe, 2026-11-18). Macie then reports no
column names and has no header keywords; so do we, and we say so on the
macie stream and in the errors, as the first line is not scanned either.
Without this, the value became a "column name" in the findings, the
printouts and the errors."""

import json
import os
import re

import pytest

from csvpath import CsvPath
from csvpath.macie.functions.macie_run import MacieRun
from test_macie_normative_runs import StreamPrinter

PAIR = os.path.join("tests", "macie", "test_resources", "normative", "01_employee_ids")
DATA = os.path.join(PAIR, "data", "employees.csv")


def _csvpath() -> str:
    d = os.path.join(PAIR, "expected")
    name = [f for f in os.listdir(d) if f.endswith(".csvpath")][0]
    with open(os.path.join(d, name), encoding="utf-8") as f:
        return f.read()


def _run(path: str) -> tuple[CsvPath, list[str]]:
    p = CsvPath()
    printer = StreamPrinter()
    p.set_printers([printer])
    p.parse(_csvpath().replace("$[", f"${path}[", 1))
    p.collect()
    return p, printer.streams.get("macie", [])


@pytest.fixture
def files(tmp_path) -> dict[str, str]:
    with open(DATA, encoding="utf-8") as f:
        lines = f.read().splitlines()
    out = {}
    for name, content in [
        ("normal", lines),
        ("headerless", lines[1:]),
        ("title", ["HR export,2026-11-17,,,"] + lines),
    ]:
        p = tmp_path / f"{name}.csv"
        p.write_text("\n".join(content) + "\n", encoding="utf-8")
        out[name] = str(p)
    return out


def _cells(p: CsvPath) -> list[dict]:
    f = p.variables["macie_findings"]
    return [
        c
        for d in f["customDataIdentifiers"]["detections"]
        for c in d["occurrences"]["cells"]
    ]


def test_macie_normal_header_is_a_header(files) -> None:
    p, printed = _run(files["normal"])
    assert MacieRun.HEADER_IS_DATA not in printed
    assert {c["columnName"] for c in _cells(p)} == {"employee_id", "manager_note"}


def test_macie_headerless_first_line_is_data(files) -> None:
    p, printed = _run(files["headerless"])
    with open(files["headerless"], encoding="utf-8") as f:
        first = f.readline().strip().split(",")
    assert first[2] == "EMP-123456"
    #
    # no value from the first line is used as a column name, anywhere
    #
    assert all(c["columnName"] is None for c in _cells(p))
    out = "\n".join(
        [json.dumps(p.variables["macie_findings"])]
        + printed
        + [f"{e.message}" for e in p.errors]
    )
    assert "EMP-123456" not in out
    #
    # said once, loudly, on the stream and in the errors; the run stays valid
    #
    assert printed.count(MacieRun.HEADER_IS_DATA) == 1
    assert MacieRun.HEADER_IS_DATA in [f"{e.message}" for e in p.errors]
    assert p.is_valid
    #
    # the same findings as before: the in-cell keyword ones (Macie agreed,
    # live probe 2026-11-18)
    #
    assert p.variables["macie_findings"]["customDataIdentifiers"]["totalCount"] == 3


def test_macie_title_line_is_not_data(files) -> None:
    #
    # a title holds no value an identifier finds, so it stays the header;
    # its text names the columns, which leaks nothing
    #
    p, printed = _run(files["title"])
    assert MacieRun.HEADER_IS_DATA not in printed
    assert p.variables["macie_findings"]["customDataIdentifiers"]["totalCount"] == 3


class _Detector:
    def matches(self, *, cell):
        return [(0, 1)] if "7" in cell else []


class _Managed:
    detector = _Detector()


class _Custom:
    regex = re.compile(r"EMP-\d{6}")


def test_macie_finds_value() -> None:
    assert MacieRun._finds_value(identifier=_Managed(), text="x7")
    assert not MacieRun._finds_value(identifier=_Managed(), text="x")
    assert MacieRun._finds_value(identifier=_Custom(), text="EMP-123456")
    assert not MacieRun._finds_value(identifier=_Custom(), text="employee_id")
    assert not MacieRun._finds_value(identifier=object(), text="EMP-123456")
