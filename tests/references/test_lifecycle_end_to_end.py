"""':lifecycle()', end to end, in every datatype (David, 2026-10-29; built
2026-11-05).

keep and gone each register a named-file, load a named-paths group and run
it. Then all three of gone's are deleted. Every root ledger keeps gone's
entries, marked "lifecycle": "deleted"; keep's are "active". A ledger read
(':manifest()' under '*') returns the whole ledger, and ':lifecycle()' is
the opt-in filter. Bare '*' reads walk the live names, which no longer hold
gone (decision 3). Local backend, roots under pytest's tmp_path.
"""

import json
import time

import pytest

from csvpath import CsvPaths
from csvpath.references.csvpaths_reference_finder_3 import CsvpathsReferenceFinder3
from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.results_reference_finder_3 import ResultsReferenceFinder3

FINDERS = {
    "files": FilesReferenceFinder3,
    "csvpaths": CsvpathsReferenceFinder3,
    "results": ResultsReferenceFinder3,
}
LEDGERS = {
    "files": "named_files/manifest.json",
    "csvpaths": "named_paths/manifest.json",
    "results": "archive/manifest.json",
}


def _csvpaths(root) -> CsvPaths:
    p = CsvPaths()
    for section, key, value in (
        ("inputs", "files", root / "named_files"),
        ("inputs", "csvpaths", root / "named_paths"),
        ("results", "archive", root / "archive"),
    ):
        p.config.add_to_config(section=section, key=key, value=str(value))
    p.config.add_to_config(section="listeners", key="groups", value="")
    return p


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    root = tmp_path_factory.mktemp("lifecycle")
    p = _csvpaths(root)
    for name in ("keep", "gone"):
        (root / f"{name}.csv").write_text("a,b\n1,2\n")
        (root / f"{name}.csvpath").write_text("~id:only~ $[*][ yes() ]")
        p.file_manager.add_named_file(name=name, path=str(root / f"{name}.csv"))
        p.paths_manager.add_named_paths_from_file(
            name=name, file_path=str(root / f"{name}.csvpath")
        )
        p.collect_paths(filename=name, pathsname=name)
        # run dirs are named to the second
        time.sleep(1.1)
    p.file_manager.remove_named_file("gone")
    p.paths_manager.remove_named_paths("gone")
    p.results_manager.remove_named_results("gone")
    # each ledger uuid (and RESULTS run_uuid) to its name
    names = {}
    for datatype, ledger in LEDGERS.items():
        entries = json.loads((root / ledger).read_text())
        assert {e["lifecycle"] for e in entries} == {"active", "deleted"}
        found = {}
        for e in entries:
            name = e.get("named_file_name") or e.get("named_paths_name")
            found[e["uuid"]] = name
            if e.get("run_uuid") is not None:
                found[e["run_uuid"]] = name
        names[datatype] = found
    return _csvpaths(root), names


def _finder(project, datatype: str, reference: str):
    p, _ = project
    return FINDERS[datatype](
        csvpaths=p, ref=ReferenceParser3(string=reference, csvpaths=p)
    )


def _names(project, datatype: str, reference: str) -> list:
    _, names = project
    results = _finder(project, datatype, reference).query()
    return [names[datatype][u] for u in results.uuids]


@pytest.mark.parametrize("datatype", list(FINDERS))
@pytest.mark.parametrize(
    "reference, expected",
    [
        ("$*.{dt}.:manifest():uuid()", ["keep", "gone"]),
        ('$*.{dt}.:manifest():lifecycle("active"):uuid()', ["keep"]),
        ('$*.{dt}.:manifest():uuid():lifecycle("active")', ["keep"]),
        ('$*.{dt}.:manifest():lifecycle("deleted")', ["gone"]),
        # gates filter, then the pointer picks, in either written order
        ('$*.{dt}.:manifest():lifecycle("active"):last()', ["keep"]),
        ('$*.{dt}.:manifest():last():lifecycle("active")', ["keep"]),
        ('$*.{dt}.:manifest():lifecycle("deleted"):first()', ["gone"]),
        # bare '*' reads the live names: gone is not there to filter
        ('$*.{dt}.:lifecycle("active")', ["keep"]),
        ('$*.{dt}.:lifecycle("deleted")', []),
    ],
)
def test_the_lifecycle_gate(project, datatype, reference, expected):
    assert _names(project, datatype, reference.format(dt=datatype)) == expected


@pytest.mark.parametrize("datatype", list(FINDERS))
def test_the_lifecycle_field(project, datatype):
    finder = _finder(project, datatype, f"$*.{datatype}.:manifest():lifecycle()")
    assert [r.data for r in finder.resolve().results] == ["active", "deleted"]


@pytest.mark.parametrize("datatype", ["csvpaths", "results"])
def test_a_per_name_read(project, datatype):
    # a literal root reads the lifecycle from the ledger too
    finder = _finder(project, datatype, f"$keep.{datatype}.:last():lifecycle()")
    assert [r.data for r in finder.resolve().results] == ["active"]
    gated = f'$keep.{datatype}.:last():lifecycle("active")'
    assert _names(project, datatype, gated) == ["keep"]
    gated = f'$keep.{datatype}.:last():lifecycle("deleted")'
    assert _names(project, datatype, gated) == []


@pytest.mark.parametrize("datatype", list(FINDERS))
@pytest.mark.parametrize(
    "reference",
    [
        '$*.{dt}.:status("complete"):lifecycle("active")',
        '$*.{dt}.:lifecycle("active"):status("complete")',
        '$*.{dt}.:manifest():status("complete"):lifecycle("active")',
    ],
)
def test_lifecycle_with_status(project, datatype, reference):
    # ':status()' is a field in every datatype (CSVPATHS since 2026-11-06)
    assert _names(project, datatype, reference.format(dt=datatype)) == ["keep"]
