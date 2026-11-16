"""MacieReview's pieces outside a run: the config it reads, why a column
was flagged, how the review is added to macie_findings, and its
printouts. The group-run tests are tests/csvpaths/test_csvpaths_macie_review.py."""

import pytest

from csvpath.macie.custom_identifier import CustomIdentifier
from csvpath.macie.macie_review import MacieReview


class _Config:
    def __init__(self, values: dict) -> None:
        self.values = values

    def get(self, *, section, name, default=None, **kw):
        return self.values.get((section, name), default)


def test_macie_review_identifiers() -> None:
    assert MacieReview(config=_Config({})).on is False
    assert MacieReview(config=None).on is False
    r = MacieReview(config=_Config({("macie", "review"): "A_ID, B_ID ,,"}))
    assert r.identifiers == {"A_ID", "B_ID"}
    assert r.reviews(name="A_ID") and not r.reviews(name="C_ID")
    assert MacieReview(
        config=_Config({("macie", "review"): ["A_ID", "B_ID"]})
    ).identifiers == {
        "A_ID",
        "B_ID",
    }
    with pytest.raises(ValueError):
        MacieReview(config=_Config({("macie", "review"): "all"}))


def test_macie_review_why() -> None:
    cdi = CustomIdentifier.from_aws(
        cdi={
            "id": "x",
            "name": "EmployeeId",
            "regex": "EMP-\\d{6}",
            "keywords": ["employee id"],
            "ignoreWords": [],
            "maximumMatchDistance": 50,
            "severityLevels": [{"occurrencesThreshold": 1, "severity": "LOW"}],
        }
    )
    assert MacieReview.why(identifier=cdi, header="employee_id") == (
        "the column header holds a keyword"
    )
    assert MacieReview.why(identifier=cdi, header="notes") == (
        "a keyword is near the value in the cell, or the value needs none"
    )


def _findings() -> dict:
    return {
        "customDataIdentifiers": {
            "detections": [{"name": "EmployeeId", "count": 3, "severity": "LOW"}],
            "totalCount": 3,
        },
        "sensitiveData": [
            {
                "category": "PERSONAL_INFORMATION",
                "detections": [{"type": "USA_SOCIAL_SECURITY_NUMBER", "count": 2}],
            }
        ],
        "csvpath": {"stopped": False},
    }


def _result(status: str = "complete") -> dict:
    return {
        "status": status,
        "reason": None if status == "complete" else "ConnectionError: down",
        "model": "jev-1.14.0",
        "questions": 1,
        "input_tokens": 200,
        "output_tokens": 20,
        "seconds": 0.3,
        "entries": []
        if status == "failed"
        else [
            {
                "identifier": "USA_SOCIAL_SECURITY_NUMBER",
                "column": 7,
                "columnName": "ref_no",
                "verdict": "unrelated",
                "confidence": 0.06,
                "probabilities": {"likely": 0.06},
                "facts": ["Every one of the 40 flagged values is the same value."],
            }
        ],
        "not_reviewed": [],
        "request": None,
        "response": None,
    }


def test_macie_review_attach() -> None:
    f = MacieReview.attach(findings=_findings(), result=_result())
    ssn = f["sensitiveData"][0]["detections"][0]
    assert ssn["count"] == 2
    assert ssn["review"] == [
        {
            "column": 7,
            "columnName": "ref_no",
            "verdict": "unrelated",
            "confidence": 0.06,
            "probabilities": {"likely": 0.06},
            "facts": ["Every one of the 40 flagged values is the same value."],
        }
    ]
    assert "review" not in f["customDataIdentifiers"]["detections"][0]
    assert f["csvpath"]["review"]["status"] == "complete"
    assert "request" not in f["csvpath"]["review"]


def test_macie_review_printouts() -> None:
    assert MacieReview.printouts(result=_result()) == [
        "macie review USA_SOCIAL_SECURITY_NUMBER column 7 ref_no: unrelated (0.06); "
        "Every one of the 40 flagged values is the same value.",
        "macie review: complete, 1 questions, jev-1.14.0, 0.3 s, 200 tokens in, 20 out",
    ]
    assert MacieReview.printouts(result=_result("failed")) == [
        "macie review: failed: ConnectionError: down"
    ]


def test_macie_review_printouts_nothing_to_review() -> None:
    result = _result()
    result.update({"questions": 0, "entries": [], "model": None, "seconds": None})
    assert MacieReview.printouts(result=result) == ["macie review: nothing to review"]
