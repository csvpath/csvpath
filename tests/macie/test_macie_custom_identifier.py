import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.custom_identifier import CustomIdentifier
from csvpath.macie.severity_levels import SeverityLevels
from csvpath.macie.macie_exceptions import MacieException

NO_ALLOW = AllowListSet()


def _cdi(**overrides) -> CustomIdentifier:
    args = {
        "name": "EmployeeId",
        "pattern": r"EMP-\d{6}",
        "keywords": ["employee id", "emp id"],
        "ignore_words": ["EMP-000000"],
        "distance": 50,
        "severity": SeverityLevels.parse(text="1:LOW 5:MEDIUM 10:HIGH"),
    }
    args.update(overrides)
    return CustomIdentifier(**args)


def _count(
    cdi: CustomIdentifier, cell: str, header: str = "notes", allow=NO_ALLOW
) -> int:
    return cdi.occurrences(cell=cell, header=header, allow_lists=allow)


def test_macie_cdi_header_keyword_counts_every_match() -> None:
    assert _count(_cdi(), "EMP-123456", header="employee_id") == 1
    assert _count(_cdi(), "EMP-123456 EMP-234567", header="Employee ID") == 2


def test_macie_cdi_without_keyword_nothing_counts() -> None:
    assert _count(_cdi(), "ref EMP-567890") == 0


def test_macie_cdi_keyword_in_cell_within_distance() -> None:
    assert _count(_cdi(), "emp id EMP-345678 transferred") == 1
    assert _count(_cdi(), "Employee ID: EMP-678901, EMP-789012") == 2


def test_macie_cdi_keyword_in_cell_too_far() -> None:
    cell = (
        "emp id is in the HR system, see the onboarding packet for details EMP-890123"
    )
    assert _count(_cdi(), cell) == 0
    assert _count(_cdi(distance=70), cell) == 1


def test_macie_cdi_no_keywords_means_every_match_counts() -> None:
    assert _count(_cdi(keywords=[]), "ref EMP-567890 and EMP-111111") == 2


def test_macie_cdi_ignore_word_is_case_sensitive_and_on_the_match() -> None:
    assert _count(_cdi(), "EMP-000000", header="employee_id") == 0
    #
    # the ignore word must be in the match, not just in the cell
    #
    assert _count(_cdi(), "EMP-000000 EMP-123456", header="employee_id") == 1
    assert (
        _count(_cdi(ignore_words=["emp-000000"]), "EMP-000000", header="employee_id")
        == 1
    )


def test_macie_cdi_allow_list_on_each_occurrence() -> None:
    allow = AllowListSet()
    allow.add_regex(name="training", pattern=r"EMP-9\d{5}")
    assert _count(_cdi(), "EMP-900001", header="employee_id", allow=allow) == 0
    assert (
        _count(_cdi(), "EMP-901234 EMP-012345", header="employee_id", allow=allow) == 1
    )
    assert _count(_cdi(), "emp id EMP-900001", allow=allow) == 0


def test_macie_cdi_regex_is_case_sensitive_with_no_word_boundaries() -> None:
    assert _count(_cdi(), "emp-112233", header="employee_id") == 0
    assert _count(_cdi(), "XEMP-223344", header="employee_id") == 1
    assert _count(_cdi(), "EMP-12345", header="employee_id") == 0


def test_macie_cdi_empty_cell() -> None:
    assert _count(_cdi(), "", header="employee_id") == 0


def test_macie_cdi_header_check_is_cached_per_header() -> None:
    cdi = _cdi()
    _count(cdi, "EMP-123456", header="employee_id")
    _count(cdi, "EMP-123456", header="notes")
    assert cdi._header_cache == {"employee_id": True, "notes": False}


def test_macie_cdi_from_aws() -> None:
    cdi = CustomIdentifier.from_aws(
        cdi={
            "name": "EmployeeId",
            "regex": r"EMP-\d{6}",
            "keywords": ["employee id"],
            "ignoreWords": ["EMP-000000"],
            "maximumMatchDistance": 20,
            "severityLevels": [{"occurrencesThreshold": 1, "severity": "LOW"}],
            "someNewAwsField": 1,
        }
    )
    assert cdi.distance == 20
    assert cdi.severity.to_text() == "1:LOW"
    assert cdi.ignore_words == ["EMP-000000"]


def test_macie_cdi_from_aws_defaults() -> None:
    cdi = CustomIdentifier.from_aws(cdi={"name": "X", "regex": "X\\d"})
    assert cdi.keywords == []
    assert cdi.ignore_words == []
    assert cdi.distance == 50
    assert cdi.severity.to_text() == "1:MEDIUM"


def test_macie_cdi_bad_input() -> None:
    with pytest.raises(ValueError):
        _cdi(name="")
    with pytest.raises(TypeError):
        _cdi(keywords="emp id")
    with pytest.raises(TypeError):
        _cdi(ignore_words=None)
    for d in [0, 301, True, None]:
        with pytest.raises(ValueError):
            _cdi(distance=d)
    with pytest.raises(TypeError):
        _cdi(severity="1:LOW")
    with pytest.raises(ValueError):
        _cdi(ignore_words=[""])
    with pytest.raises(MacieException):
        _cdi(pattern="(EMP")
    with pytest.raises(TypeError):
        CustomIdentifier.from_aws(cdi=None)
    with pytest.raises(TypeError):
        _cdi().occurrences(cell=None, header="h", allow_lists=NO_ALLOW)
    with pytest.raises(TypeError):
        _cdi().occurrences(cell="x", header="h", allow_lists=None)
