"""The synthetic files for the live check against Macie
(tests/macie/live/make_live_files.py): every expectation holds for the
Framework's own stand-ins, cell by cell. This keeps the data honest, so
when Macie's findings are compared later, a difference is about Macie, not
about a badly built test value."""

import csv
import os
import sys

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.custom_identifier import CustomIdentifier
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

sys.path.insert(0, os.path.join("tests", "macie", "live"))
import make_live_files as mlf  # noqa: E402

#
# the job's custom identifier, as the README asks for it to be created
#
EMPLOYEE_ID = {
    "id": "live-employee-id",
    "name": "EmployeeId",
    "regex": "EMP-\\d{6}",
    "keywords": ["employee id", "emp id"],
    "ignoreWords": ["EMP-000000"],
    "maximumMatchDistance": 50,
    "severityLevels": [
        {"occurrencesThreshold": 1, "severity": "LOW"},
        {"occurrencesThreshold": 5, "severity": "MEDIUM"},
        {"occurrencesThreshold": 10, "severity": "HIGH"},
    ],
}


@pytest.fixture(scope="module")
def written(tmp_path_factory):
    out = tmp_path_factory.mktemp("live")
    doc = mlf.write_all(out=str(out))
    return str(out), doc


def _allow(doc) -> AllowListSet:
    allow = AllowListSet()
    allow.add_regex(name="training-accounts", pattern="EMP-9\\d{5}")
    allow.add_words(name="contractors", entries=list(doc["contractors"]))
    return allow


def _identifier(catalog: ManagedCatalog, name: str):
    if name == "EmployeeId":
        return CustomIdentifier.from_aws(cdi=EMPLOYEE_ID)
    e = catalog.identifier(name=name)
    return ManagedIdentifier(
        name=name,
        category=e["category"],
        detector=e["detector"],
        keyword_mode=e["keyword_mode"],
        keywords=e["keywords"],
        distance=e["distance"],
        severity=SeverityLevels.parse(text=e["severity"]),
        catalog=catalog,
    )


def test_macie_live_files_written(written) -> None:
    out, doc = written
    names = sorted(os.listdir(os.path.join(out, "data")))
    assert names == sorted(f"{m.__name__}.csv" for m in mlf.FILES)
    for n in names:
        size = os.path.getsize(os.path.join(out, "data", n))
        assert mlf.TARGET_BYTES <= size < mlf.TARGET_BYTES * 1.1, n
    contractors = os.path.join(out, "macie-config", "allow", "contractors.txt")
    with open(contractors, encoding="utf-8") as f:
        assert f.read().splitlines() == mlf.CONTRACTORS
    assert len(doc["expected"]) >= 40


def test_macie_live_files_are_deterministic(written, tmp_path) -> None:
    out, _ = written
    mlf.write_all(out=str(tmp_path))
    for n in os.listdir(os.path.join(out, "data")):
        with open(os.path.join(out, "data", n), "rb") as a:
            with open(os.path.join(tmp_path, "data", n), "rb") as b:
                assert a.read() == b.read(), n


def test_macie_live_expectations_hold_for_the_stand_ins(written) -> None:
    out, doc = written
    catalog = ManagedCatalog.load()
    allow = _allow(doc)
    wrong = []
    for e in doc["expected"]:
        with open(
            os.path.join(out, "data", e["file"]), encoding="utf-8", newline=""
        ) as f:
            rows = list(csv.reader(f))
        headers, row = rows[0], rows[e["row"] - 1]
        i = e["column_number"] - 1
        assert headers[i] == e["column"]
        n = _identifier(catalog, e["identifier"]).occurrences(
            cell=row[i], header=headers[i], allow_lists=allow
        )
        if n != e["count"]:
            wrong.append(
                (e["file"], e["row"], e["identifier"], e["count"], n, e["note"])
            )
    assert wrong == []


def test_macie_live_clean_file_has_nothing(written) -> None:
    #
    # no stand-in finds anything in the clean file or the padding
    #
    out, doc = written
    catalog = ManagedCatalog.load()
    allow = _allow(doc)
    identifiers = [_identifier(catalog, n) for n in catalog.names] + [
        _identifier(catalog, "EmployeeId")
    ]
    with open(
        os.path.join(out, "data", "clean.csv"), encoding="utf-8", newline=""
    ) as f:
        rows = list(csv.reader(f))
    headers = rows[0]
    found = []
    for row in rows[1:200]:
        for i, cell in enumerate(row):
            for ident in identifiers:
                if ident.occurrences(cell=cell, header=headers[i], allow_lists=allow):
                    found.append((ident.name, cell))
    assert found == []
