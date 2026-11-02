"""Runs each normative pair's data through the pure-Python matching core,
without CVL, and checks it produces the pair's expected findings, finding
lines, errors, and printouts. test_macie_normative_runs checks the same
expectations through real CVL runs."""

import csv
import json
import os

import pytest
import yaml

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.custom_identifier import CustomIdentifier
from csvpath.macie.findings_tally import FindingsTally, IdentifierTally
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NORMATIVE = os.path.join("tests", "macie", "test_resources", "normative")
PAIRS = sorted(
    d for d in os.listdir(NORMATIVE) if os.path.isdir(os.path.join(NORMATIVE, d))
)


def _wrapper(pair_dir: str) -> dict:
    names = [
        n for n in os.listdir(pair_dir) if MacieWrapperLoader.is_wrapper_path(path=n)
    ]
    assert len(names) == 1
    return MacieWrapperLoader.from_path(path=os.path.join(pair_dir, names[0]))


def _metadata_int(csvpath_file: str, key: str) -> int:
    with open(csvpath_file, encoding="utf-8") as f:
        for line in f:
            k, _, v = line.strip().partition(":")
            if k == key:
                return int(v.strip())
    raise AssertionError(f"No {key} in {csvpath_file}")


def _run(*, wrapper: dict, data: str, max_findings: int, max_detail: int) -> dict:
    allow = AllowListSet()
    for a in wrapper.get("allowLists", []):
        s = a["settings"]
        if "regex" in s["criteria"]:
            allow.add_regex(name=s["name"], pattern=s["criteria"]["regex"])
        else:
            allow.add_words(name=s["name"], entries=a["contents"]["entries"])
    identifiers = []
    aws = wrapper.get("aws", {})
    source = aws.get("classificationJob") or aws.get("sensitivityInspectionTemplate")
    source_arn = None
    if source is not None:
        source_arn = source.get("jobArn") or source.get("arn")
    tally = FindingsTally(
        max_findings=max_findings, max_detail=max_detail, source_arn=source_arn
    )
    for c in wrapper.get("customDataIdentifiers", []):
        cdi = CustomIdentifier.from_aws(cdi=c)
        identifiers.append(cdi)
        tally.add(
            tally=IdentifierTally(
                name=cdi.name,
                severity=cdi.severity,
                max_detail=max_detail,
                arn=c.get("arn"),
            )
        )
    #
    # managed identifiers come after the custom ones, in the wrapper's
    # resolved order, as the converter writes them
    #
    catalog = ManagedCatalog.load()
    for name in (wrapper.get("managedDataIdentifiers") or {}).get("resolved") or []:
        if not catalog.has(name=name):
            continue
        e = catalog.identifier(name=name)
        mdi = ManagedIdentifier(
            name=name,
            category=e["category"],
            detector=e["detector"],
            keyword_mode=e["keyword_mode"],
            keywords=e["keywords"],
            distance=e["distance"],
            severity=SeverityLevels.parse(text=e["severity"]),
            catalog=catalog,
        )
        identifiers.append(mdi)
        tally.add(
            tally=IdentifierTally(
                name=name,
                severity=mdi.severity,
                max_detail=max_detail,
                category=mdi.category,
            )
        )
    errors, printouts, lines = [], [], set()
    with open(data, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    headers = rows[0]
    for line, row in enumerate(rows[1:], start=1):
        #
        # the breaker stops the run on the line where the total reaches the
        # max. later lines are not read, and nothing more is recorded on
        # this line, but the line itself still counts as a finding line
        #
        if tally.tripped:
            break
        for identifier in identifiers:
            for i, cell in enumerate(row):
                n = identifier.occurrences(
                    cell=cell, header=headers[i], allow_lists=allow
                )
                for _ in range(n):
                    if tally.tripped:
                        break
                    lines.add(line)
                    if tally.record(
                        name=identifier.name,
                        row=line + 1,
                        column=i + 1,
                        column_name=headers[i],
                    ):
                        msg = FindingsTally.detail_message(
                            name=identifier.name,
                            occurrence=tally.tallies[identifier.name].count,
                            line=line,
                            column=i + 1,
                            column_name=headers[i],
                        )
                        errors.append({"line": line, "message": msg})
                        printouts.append(msg)
                    if tally.tripped:
                        tally.stopped_at_line = line
    printouts.extend(tally.summary_messages())
    return {
        "findings": tally.to_findings(),
        "lines": sorted(lines),
        "errors": errors,
        "printouts": printouts,
    }


@pytest.mark.parametrize("pair", PAIRS)
def test_macie_pair_semantics(pair: str) -> None:
    pair_dir = os.path.join(NORMATIVE, pair)
    wrapper = _wrapper(pair_dir)
    with open(os.path.join(pair_dir, "expected.yaml"), encoding="utf-8") as f:
        expected = yaml.safe_load(f)
    for run in expected["runs"]:
        csvpath_file = os.path.join(pair_dir, "expected", run["csvpath"])
        result = _run(
            wrapper=wrapper,
            data=os.path.join(pair_dir, "data", run["data"]),
            max_findings=_metadata_int(csvpath_file, "macie-max-findings"),
            max_detail=_metadata_int(csvpath_file, "macie-max-detail"),
        )
        with open(
            os.path.join(pair_dir, "expected", run["findings"]), encoding="utf-8"
        ) as f:
            assert result["findings"] == json.load(f)
        assert result["lines"] == run["finding_lines"]
        assert result["errors"] == run["errors"]
        with open(
            os.path.join(pair_dir, "expected", run["printouts"]["macie"]),
            encoding="utf-8",
        ) as f:
            assert result["printouts"] == f.read().splitlines()
