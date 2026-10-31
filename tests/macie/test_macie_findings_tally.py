import pytest

from csvpath.macie.findings_tally import FindingsTally, IdentifierTally
from csvpath.macie.severity_levels import SeverityLevels

CDI_ARN = "arn:aws:macie2:us-east-1:123456789012:custom-data-identifier/2a1b"


def _tally(name: str = "EmployeeId", max_detail: int = 3, **kw) -> IdentifierTally:
    return IdentifierTally(
        name=name,
        severity=SeverityLevels.parse(text="1:LOW 5:MEDIUM 10:HIGH"),
        max_detail=max_detail,
        **kw,
    )


def _record(t, n: int, *, row: int = 2) -> list[bool]:
    return [t.record(row=row, column=3, column_name="employee_id") for _ in range(n)]


def test_macie_tally_detail_cap_stops_reporting_not_counting() -> None:
    t = _tally(max_detail=3)
    assert _record(t, 5) == [True, True, True, False, False]
    assert t.count == 5
    assert t.detailed == 3
    assert t.severity_now() == "MEDIUM"


def test_macie_tally_zero_detail() -> None:
    t = _tally(max_detail=0)
    assert _record(t, 2) == [False, False]
    assert t.count == 2


def test_macie_tally_keeps_at_most_15_cells() -> None:
    t = _tally(max_detail=100)
    _record(t, 20)
    assert t.count == 20
    assert len(t.cells) == IdentifierTally.MAX_CELLS == 15
    assert t.cells[0] == {
        "cellReference": None,
        "column": 3,
        "columnName": "employee_id",
        "row": 2,
    }


def test_macie_tally_custom_and_managed_detection_shapes() -> None:
    custom = _tally(arn=CDI_ARN)
    _record(custom, 1)
    d = custom.to_detection()
    assert (d["arn"], d["name"], d["count"], d["severity"]) == (
        CDI_ARN,
        "EmployeeId",
        1,
        "LOW",
    )
    assert "type" not in d
    managed = _tally(name="CREDIT_CARD_NUMBER", category="FINANCIAL_INFORMATION")
    _record(managed, 1)
    d = managed.to_detection()
    assert d["type"] == "CREDIT_CARD_NUMBER"
    assert "name" not in d and "arn" not in d


def test_macie_tally_bad_input() -> None:
    with pytest.raises(ValueError):
        _tally(name=" ")
    with pytest.raises(TypeError):
        IdentifierTally(name="x", severity="1:LOW", max_detail=1)
    for m in [-1, True, None]:
        with pytest.raises(ValueError):
            _tally(max_detail=m)
    t = _tally()
    for row, column in [(0, 1), (1, 0), (True, 1), (1, "3")]:
        with pytest.raises(ValueError):
            t.record(row=row, column=column, column_name="c")
    with pytest.raises(TypeError):
        t.record(row=1, column=1, column_name=None)


def _findings(max_findings: int = 100) -> FindingsTally:
    f = FindingsTally(max_findings=max_findings, max_detail=3)
    f.add(tally=_tally(arn=CDI_ARN))
    return f


def test_macie_findings_breaker_trips_when_total_reaches_max() -> None:
    f = _findings(max_findings=3)
    f.add(tally=_tally(name="Other"))
    f.record(name="EmployeeId", row=2, column=3, column_name="e")
    f.record(name="Other", row=2, column=4, column_name="o")
    assert not f.tripped
    f.record(name="EmployeeId", row=3, column=3, column_name="e")
    assert f.tripped
    with pytest.raises(ValueError, match="tripped"):
        f.record(name="Other", row=3, column=4, column_name="o")


def test_macie_findings_shape() -> None:
    f = _findings()
    managed = _tally(name="CREDIT_CARD_NUMBER", category="FINANCIAL_INFORMATION")
    f.add(tally=managed)
    f.add(tally=_tally(name="NeverFound"))
    f.record(name="EmployeeId", row=2, column=3, column_name="employee_id")
    f.record(name="CREDIT_CARD_NUMBER", row=4, column=5, column_name="card")
    out = f.to_findings()
    assert out["customDataIdentifiers"]["totalCount"] == 1
    assert [d["name"] for d in out["customDataIdentifiers"]["detections"]] == [
        "EmployeeId"
    ]
    assert out["sensitiveData"][0]["category"] == "FINANCIAL_INFORMATION"
    assert out["sensitiveData"][0]["totalCount"] == 1
    assert out["csvpath"] == {
        "source_arn": None,
        "stopped": False,
        "stopped_at_line": None,
        "max_findings": 100,
        "max_detail": 3,
    }


def test_macie_findings_messages() -> None:
    assert (
        FindingsTally.detail_message(
            name="EmployeeId",
            occurrence=4,
            line=1,
            column=3,
            column_name="employee_id",
        )
        == "macie EmployeeId: occurrence 4, line 1 (row 2), column 3 employee_id"
    )
    f = FindingsTally(max_findings=100, max_detail=3)
    for name, n in [("A", 8), ("B", 1), ("C", 0)]:
        f.add(tally=_tally(name=name))
        for _ in range(n):
            f.record(name=name, row=2, column=1, column_name="c")
    f.add(
        tally=IdentifierTally(
            name="D", severity=SeverityLevels.parse(text="3:HIGH"), max_detail=3
        )
    )
    f.record(name="D", row=2, column=1, column_name="c")
    assert f.summary_messages() == [
        "macie A: 8 occurrences, severity MEDIUM, detail shown for first 3",
        "macie B: 1 occurrence, severity LOW, detail shown for all 1",
        "macie C: 0 occurrences, severity none (below 1), no detail",
        "macie D: 1 occurrence, severity none (below 3), detail shown for all 1",
    ]


def test_macie_findings_message_when_tripped() -> None:
    f = _findings(max_findings=2)
    f.record(name="EmployeeId", row=2, column=3, column_name="e")
    f.record(name="EmployeeId", row=3, column=3, column_name="e")
    f.stopped_at_line = 2
    assert f.summary_messages()[-1] == (
        "macie: stopped at line 2 after 2 occurrences (max 2); results are "
        "partial and severities are at least as shown"
    )
    assert f.to_findings()["csvpath"]["stopped"] is True


def test_macie_findings_bad_input() -> None:
    for kw in [
        {"max_findings": 0, "max_detail": 1},
        {"max_findings": 1, "max_detail": -1},
    ]:
        with pytest.raises(ValueError):
            FindingsTally(**kw)
    f = _findings()
    with pytest.raises(TypeError):
        f.add(tally="x")
    with pytest.raises(ValueError, match="added twice"):
        f.add(tally=_tally())
    with pytest.raises(ValueError, match="No identifier"):
        f.record(name="Nope", row=1, column=1, column_name="c")


def test_macie_findings_source_arn() -> None:
    job = "arn:aws:macie2:us-east-1:123456789012:classification-job/5d0c"
    f = FindingsTally(max_findings=10, max_detail=1, source_arn=job)
    assert f.to_findings()["csvpath"]["source_arn"] == job


def test_macie_findings_bad_arns() -> None:
    from csvpath.macie.macie_exceptions import MacieException

    with pytest.raises(MacieException):
        FindingsTally(max_findings=10, max_detail=1, source_arn="arn:x")
    with pytest.raises(MacieException):
        _tally(arn="arn:x")
