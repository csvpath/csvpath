"""Clean lines (specs/macie/clean-lines-design.md): with config.ini
[macie] collect = clean, a Macie csvpath collects the lines without
findings, so a csvpath after it with source-mode: preceding reads only
those. The findings are the same in both modes. A tripped breaker leaves
the lines after it unscanned, so in clean mode it fails the run, says so,
and calls stop_all().

Each CsvPath in a group run reads config.ini itself, so each test writes
a copy of the active config.ini with the [macie] keys and points
CSVPATH_CONFIG_PATH at it, for that test only."""

import configparser
import os

import pytest

from csvpath import CsvPaths
from csvpath.macie.functions.macie_run import MacieRun

NORMATIVE = os.path.join("tests", "macie", "test_resources", "normative")
LICENSES = os.path.join(NORMATIVE, "21_drivers_licenses")
BREAKER = os.path.join(NORMATIVE, "03_breaker")
GROUP = "macie_clean_lines_test"
NAMED_FILE = "macie_clean_lines_test_data"
AFTER = """~
  id: after
  source-mode: preceding
~
$[*][ yes() ]
"""
EVERY_LINE = """~
  id: every_line
~
$[*][ yes() ]
"""


def _config(*, tmp_path, monkeypatch, macie: dict) -> None:
    source = os.environ.get("CSVPATH_CONFIG_PATH") or os.path.join(
        "config", "config.ini"
    )
    parser = configparser.RawConfigParser()
    parser.read(source, encoding="utf-8")
    target = os.path.join(tmp_path, "config.ini")
    for section in ("config", "macie"):
        if not parser.has_section(section):
            parser.add_section(section)
    parser.set("config", "path", target)
    for name in ("collect", "max_findings"):
        parser.remove_option("macie", name)
    for name, value in macie.items():
        parser.set("macie", name, value)
    with open(target, "w", encoding="utf-8") as f:
        parser.write(f)
    monkeypatch.setenv("CSVPATH_CONFIG_PATH", target)


def _load(*, tmp_path, wrapper: str, data: str, then: str) -> CsvPaths:
    paths = CsvPaths()
    paths.paths_manager.remove_named_paths(GROUP)
    paths.file_manager.remove_named_file(NAMED_FILE)
    paths.paths_manager.add_named_paths_from_file(name=GROUP, file_path=wrapper)
    then_path = os.path.join(tmp_path, "then.csvpath")
    with open(then_path, "w", encoding="utf-8") as f:
        f.write(then)
    paths.paths_manager.add_named_paths_from_file(
        name=GROUP, file_path=then_path, append=True
    )
    paths.file_manager.add_named_file(name=NAMED_FILE, path=data)
    return paths


def _results(paths: CsvPaths) -> dict:
    out = {}
    for r in paths.results_manager.get_named_results(GROUP):
        lines = r.lines if isinstance(r.lines, list) else r.lines.to_list()
        out[r.csvpath.identity] = (r, [line[0] for line in lines])
    return out


@pytest.fixture(autouse=True)
def clean():
    yield
    paths = CsvPaths()
    paths.paths_manager.remove_named_paths(GROUP)
    paths.file_manager.remove_named_file(NAMED_FILE)


def _licenses(*, tmp_path, monkeypatch, collect: str | None) -> dict:
    _config(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        macie={} if collect is None else {"collect": collect},
    )
    paths = _load(
        tmp_path=tmp_path,
        wrapper=os.path.join(LICENSES, "group-b-drivers-licenses.macie.json"),
        data=os.path.join(LICENSES, "data", "drivers.csv"),
        then=AFTER,
    )
    paths.collect_paths(filename=NAMED_FILE, pathsname=GROUP)
    return _results(paths)


def test_csvpaths_macie_collects_findings_by_default(tmp_path, monkeypatch) -> None:
    results = _licenses(tmp_path=tmp_path, monkeypatch=monkeypatch, collect=None)
    #
    # pair 21: lines 1 to 9 have findings, line 10 has none
    #
    macie, lines = results["group-b-drivers-licenses"]
    assert lines == [f"{i}" for i in range(1, 10)]
    assert results["after"][1] == lines
    assert not any(
        p.startswith("macie: clean lines") for p in macie.get_printouts("macie")
    )


def test_csvpaths_macie_collects_clean_lines(tmp_path, monkeypatch) -> None:
    findings = _licenses(tmp_path=tmp_path, monkeypatch=monkeypatch, collect="findings")
    clean = _licenses(tmp_path=tmp_path, monkeypatch=monkeypatch, collect="clean")
    macie, lines = clean["group-b-drivers-licenses"]
    assert lines == ["10"]
    assert clean["after"][1] == ["10"]
    assert macie.csvpath.is_valid
    #
    # the findings and errors are the same in both modes
    #
    plain = findings["group-b-drivers-licenses"][0]
    assert (
        macie.csvpath.variables["macie_findings"]
        == plain.csvpath.variables["macie_findings"]
    )
    assert len(macie.errors) == len(plain.errors) == 12
    assert MacieRun.CLEAN_CHECKED.format(
        n=7, not_checked="none"
    ) in macie.get_printouts("macie")


def _breaker(*, tmp_path, monkeypatch, collect: str, then: str) -> CsvPaths:
    #
    # pair 03 with max_findings 5: the total reaches 5 on line 4, so lines
    # 5 and 6 are never scanned
    #
    _config(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        macie={"collect": collect, "max_findings": "5"},
    )
    return _load(
        tmp_path=tmp_path,
        wrapper=os.path.join(BREAKER, "hr-badges.macie.json"),
        data=os.path.join(BREAKER, "data", "badges.csv"),
        then=then,
    )


def test_csvpaths_macie_clean_lines_breaker_fails_the_run(
    tmp_path, monkeypatch
) -> None:
    paths = _breaker(
        tmp_path=tmp_path, monkeypatch=monkeypatch, collect="clean", then=AFTER
    )
    paths.collect_paths(filename=NAMED_FILE, pathsname=GROUP)
    results = _results(paths)
    macie, lines = results["hr-badges"]
    assert macie.csvpath.variables["macie_findings"]["csvpath"]["stopped"] is True
    assert lines == ["3"]
    assert not macie.csvpath.is_valid
    assert MacieRun.CLEAN_TRIPPED.format(line=4) in macie.get_printouts("macie")


def test_csvpaths_macie_findings_breaker_keeps_the_run(tmp_path, monkeypatch) -> None:
    paths = _breaker(
        tmp_path=tmp_path, monkeypatch=monkeypatch, collect="findings", then=AFTER
    )
    paths.collect_paths(filename=NAMED_FILE, pathsname=GROUP)
    macie, lines = _results(paths)["hr-badges"]
    assert lines == ["1", "2", "4"]
    assert macie.csvpath.is_valid
    assert not any(
        p.startswith("macie: breaker tripped") for p in macie.get_printouts("macie")
    )


def test_csvpaths_macie_clean_lines_breaker_stops_a_by_line_run(
    tmp_path, monkeypatch
) -> None:
    #
    # breadth-first: each line goes through each csvpath. stop_all() stops
    # the other csvpath at the line the breaker tripped on, so it never
    # reads the lines after it, which were not scanned
    #
    paths = _breaker(
        tmp_path=tmp_path, monkeypatch=monkeypatch, collect="clean", then=EVERY_LINE
    )
    paths.collect_by_line(filename=NAMED_FILE, pathsname=GROUP)
    results = _results(paths)
    assert not results["hr-badges"][0].csvpath.is_valid
    #
    # $[*] takes the header too. the breaker trips on line 4, before the
    # other csvpath sees it
    #
    assert results["every_line"][1] == ["row_id", "1", "2", "3"]
