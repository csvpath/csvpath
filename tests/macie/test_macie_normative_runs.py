"""For each normative pair: the converter must produce the pair's expected
csvpath exactly, and both the expected csvpath and the converter's output
must, through real CVL against the pair's data, give every expected output:
the matched lines, the "macie" print stream, the collected errors, and the
macie_findings variable. test_macie_pair_semantics checks the same
expectations without CVL."""

import csv
import json
import os

import pytest
import yaml

from csvpath import CsvPath
from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.util.printer import Printer

NORMATIVE = os.path.join("tests", "macie", "test_resources", "normative")


class StreamPrinter(Printer):
    """keeps each print stream's lines separately"""

    __test__ = False

    def __init__(self) -> None:
        self.streams: dict[str, list[str]] = {}

    @property
    def lines_printed(self) -> int:
        return sum(len(v) for v in self.streams.values())

    @property
    def last_line(self) -> str:
        return ""

    def print(self, string: str) -> None:
        self.print_to("default", string)

    def print_to(self, name: str, string: str) -> None:
        self.streams.setdefault(name or "default", []).append(string)


def _pairs() -> list[str]:
    return sorted(
        os.path.join(NORMATIVE, d)
        for d in os.listdir(NORMATIVE)
        if os.path.isdir(os.path.join(NORMATIVE, d))
    )


def _expected(pair: str) -> dict:
    with open(os.path.join(pair, "expected.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _runs() -> list[tuple[str, dict, str]]:
    #
    # each run twice: the hand-checked expected csvpath, and the converter's
    # output for the pair's wrapper run stand-alone against the data
    #
    runs = []
    for pair in _pairs():
        for run in _expected(pair)["runs"]:
            for source in ["expected", "converted"]:
                runs.append((pair, run, source))
    return runs


def _run_id(param) -> str:
    if isinstance(param, dict):
        return f"{param['csvpath']}-{param['data']}"
    return os.path.basename(param)


def _convert(*, pair: str, path: str | None = None) -> str:
    names = [n for n in os.listdir(pair) if MacieWrapperLoader.is_wrapper_path(path=n)]
    assert len(names) == 1
    wrapper = MacieWrapperLoader.from_path(path=os.path.join(pair, names[0]))
    args = _expected(pair).get("conversion") or {}
    return MacieConverter(wrapper=wrapper).convert(path=path, **args).csvpath


def _with_data_path(*, csvpath: str, data_path: str) -> str:
    #
    # expected csvpaths have no filename in their root, as the converter's
    # output for a named-paths group does not
    #
    assert csvpath.count("$[1*]") == 1
    return csvpath.replace("$[1*]", f"${data_path}[1*]", 1)


@pytest.mark.parametrize("pair", _pairs(), ids=_run_id)
def test_macie_converter_produces_expected_csvpath(pair: str) -> None:
    for run in _expected(pair)["runs"]:
        with open(
            os.path.join(pair, "expected", run["csvpath"]), encoding="utf-8"
        ) as f:
            assert _convert(pair=pair) == f.read()


@pytest.mark.parametrize("pair,run,source", _runs(), ids=_run_id)
def test_macie_normative_run(pair: str, run: dict, source: str) -> None:
    data_path = os.path.join(pair, "data", run["data"])
    if source == "expected":
        with open(
            os.path.join(pair, "expected", run["csvpath"]), encoding="utf-8"
        ) as f:
            csvpath = _with_data_path(csvpath=f.read(), data_path=data_path)
    else:
        csvpath = _convert(pair=pair, path=data_path)
    path = CsvPath()
    printer = StreamPrinter()
    path.set_printers([printer])
    matched = path.collect(csvpath)

    with open(data_path, encoding="utf-8", newline="") as f:
        lines = list(csv.reader(f))
    assert matched == [lines[i] for i in run["finding_lines"]]

    for stream, name in run["printouts"].items():
        with open(os.path.join(pair, "expected", name), encoding="utf-8") as f:
            assert printer.streams.get(stream, []) == f.read().splitlines()
    #
    # the default stream gets nothing: errors are not echoed (no-print)
    #
    assert printer.streams.get("default", []) == []

    errors = [{"line": e.line_count, "message": e.message} for e in path.errors]
    assert errors == run["errors"]

    with open(os.path.join(pair, "expected", run["findings"]), encoding="utf-8") as f:
        assert path.variables["macie_findings"] == json.load(f)
