"""Runs each normative pair's expected csvpath, through real CVL, against
the pair's data and checks every output: the matched lines, the "macie"
print stream, the collected errors, and the macie_findings variable.
test_macie_pair_semantics checks the same expectations without CVL."""

import csv
import json
import os

import pytest
import yaml

from csvpath import CsvPath
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


def _runs() -> list[tuple[str, dict]]:
    runs = []
    for d in sorted(os.listdir(NORMATIVE)):
        pair = os.path.join(NORMATIVE, d)
        if not os.path.isdir(pair):
            continue
        with open(os.path.join(pair, "expected.yaml"), encoding="utf-8") as f:
            for run in yaml.safe_load(f)["runs"]:
                runs.append((pair, run))
    return runs


def _run_id(param) -> str:
    if isinstance(param, dict):
        return f"{param['csvpath']}-{param['data']}"
    return os.path.basename(param)


def _with_data_path(*, csvpath: str, data_path: str) -> str:
    #
    # expected csvpaths have no filename in their root, as the transpiler's
    # output will not
    #
    assert csvpath.count("$[1*]") == 1
    return csvpath.replace("$[1*]", f"${data_path}[1*]", 1)


@pytest.mark.parametrize("pair,run", _runs(), ids=_run_id)
def test_macie_normative_run(pair: str, run: dict) -> None:
    with open(os.path.join(pair, "expected", run["csvpath"]), encoding="utf-8") as f:
        csvpath = f.read()
    data_path = os.path.join(pair, "data", run["data"])
    path = CsvPath()
    printer = StreamPrinter()
    path.set_printers([printer])
    matched = path.collect(_with_data_path(csvpath=csvpath, data_path=data_path))

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
