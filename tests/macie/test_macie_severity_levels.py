import pytest

from csvpath.macie.severity_levels import SeverityLevels
from csvpath.macie.macie_exceptions import MacieException


def test_macie_severity_parse_and_text() -> None:
    s = SeverityLevels.parse(text="1:LOW 5:MEDIUM 10:HIGH")
    assert s.levels == [(1, "LOW"), (5, "MEDIUM"), (10, "HIGH")]
    assert s.to_text() == "1:LOW 5:MEDIUM 10:HIGH"


@pytest.mark.parametrize(
    "count, severity",
    [
        (0, None),
        (1, "LOW"),
        (4, "LOW"),
        (5, "MEDIUM"),
        (9, "MEDIUM"),
        (10, "HIGH"),
        (999, "HIGH"),
    ],
)
def test_macie_severity_for_count(count: int, severity) -> None:
    s = SeverityLevels.parse(text="1:LOW 5:MEDIUM 10:HIGH")
    assert s.severity(count=count) == severity


def test_macie_severity_below_lowest_threshold_is_no_finding() -> None:
    s = SeverityLevels.parse(text="3:HIGH")
    assert s.severity(count=2) is None
    assert s.severity(count=3) == "HIGH"


def test_macie_severity_default_is_macies() -> None:
    for absent in [None, []]:
        s = SeverityLevels.from_aws(severity_levels=absent)
        assert s.levels == [(1, "MEDIUM")]


def test_macie_severity_from_aws_sorts() -> None:
    s = SeverityLevels.from_aws(
        severity_levels=[
            {"occurrencesThreshold": 50, "severity": "HIGH"},
            {"occurrencesThreshold": 1, "severity": "LOW"},
        ]
    )
    assert s.to_text() == "1:LOW 50:HIGH"


def test_macie_severity_is_final() -> None:
    s = SeverityLevels.parse(text="1:LOW 10:HIGH")
    assert not s.is_final(count=9)
    assert s.is_final(count=10)


@pytest.mark.parametrize(
    "text",
    [
        "1:URGENT",
        "1-LOW",
        "x:LOW",
        "0:LOW",
        "5:LOW 1:MEDIUM",
        "1:MEDIUM 5:LOW",
        "1:LOW 1:MEDIUM",
        "1:LOW 5:LOW",
    ],
)
def test_macie_severity_bad_levels(text: str) -> None:
    with pytest.raises(MacieException):
        SeverityLevels.parse(text=text)


def test_macie_severity_bad_input() -> None:
    with pytest.raises(TypeError):
        SeverityLevels.parse(text=None)
    with pytest.raises(ValueError):
        SeverityLevels.parse(text=" ")
    with pytest.raises(ValueError):
        SeverityLevels(levels=[])
    with pytest.raises(MacieException):
        SeverityLevels(levels=[(True, "LOW")])
    with pytest.raises(TypeError):
        SeverityLevels.from_aws(severity_levels="1:LOW")
    s = SeverityLevels.parse(text="1:LOW")
    for c in [-1, True, "1"]:
        with pytest.raises(ValueError):
            s.severity(count=c)
