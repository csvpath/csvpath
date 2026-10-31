"""MacieConverter, one behavior at a time. test_macie_normative_runs checks
the converter's output exactly against each normative pair."""

import copy
import os

import pytest

from csvpath import CsvPath
from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.util.printer import TestPrinter

WRAPPERS = os.path.join("tests", "macie", "test_resources", "wrappers")
PAIR = os.path.join("tests", "macie", "test_resources", "normative", "01_employee_ids")


def _wrapper(name: str) -> dict:
    return MacieWrapperLoader.from_path(path=os.path.join(WRAPPERS, name))


def _job() -> dict:
    return _wrapper("job_download.macie.json")


def _handcrafted() -> dict:
    return _wrapper("handcrafted_minimal.macie.json")


def _metadata(csvpath: str) -> dict:
    comment = csvpath.split("~")[1]
    md = {}
    for line in comment.strip().splitlines():
        k, _, v = line.strip().partition(": ")
        md[k] = v
    return md


def _run(*, csvpath: str, data: str):
    path = CsvPath()
    printer = TestPrinter()
    path.set_printers([printer])
    matched = path.collect(csvpath.replace("$[1*]", f"${data}[1*]", 1))
    return path, matched


# =============
# names
# =============


def test_macie_converter_name_from_the_job() -> None:
    conversion = MacieConverter(wrapper=_job()).convert()
    assert conversion.name == "hr-exports-weekly"
    assert _metadata(conversion.csvpath)["id"] == "hr-exports-weekly"


def test_macie_converter_name_given() -> None:
    conversion = MacieConverter(wrapper=_job()).convert(name="weekly.hr_v2")
    assert conversion.name == "weekly.hr_v2"
    assert _metadata(conversion.csvpath)["id"] == "weekly.hr_v2"


def test_macie_converter_handcrafted_needs_a_name() -> None:
    with pytest.raises(MacieException):
        MacieConverter(wrapper=_handcrafted()).convert()
    conversion = MacieConverter(wrapper=_handcrafted()).convert(name="test-rules")
    assert conversion.name == "test-rules"


@pytest.mark.parametrize("name", ["", "has space", "a:b", "-leading", "a/b", "é"])
def test_macie_converter_bad_names(name: str) -> None:
    with pytest.raises(MacieException):
        MacieConverter(wrapper=_job()).convert(name=name)


def test_macie_converter_job_name_must_be_usable() -> None:
    w = _job()
    w["aws"]["classificationJob"]["name"] = "HR exports (weekly)"
    with pytest.raises(MacieException):
        MacieConverter(wrapper=w).convert()
    assert MacieConverter(wrapper=w).convert(name="hr").name == "hr"


# =============
# metadata
# =============


def test_macie_converter_job_metadata() -> None:
    md = _metadata(MacieConverter(wrapper=_job()).convert().csvpath)
    assert md["macie-origin"] == "job"
    assert md["macie-job-id"] == "3ce05dbb7ec5505def334104bf1b3bca"
    assert md["macie-account"] == "123456789012"
    assert md["macie-region"] == "us-east-1"
    assert md["macie-source-arn"].startswith("arn|aws|macie2|us-east-1|")
    assert ":" not in md["macie-source-arn"]
    assert md["macie-downloaded-at"] == "20261029T174000Z"
    assert md["macie-max-findings"] == "10000"
    assert md["macie-max-detail"] == "15"
    assert md["logic-mode"] == "OR"
    assert md["print-mode"] == "separate"
    assert md["validation-mode"] == (
        "collect, match, no-print, no-raise, no-fail, no-stop"
    )


def test_macie_converter_handcrafted_metadata() -> None:
    md = _metadata(MacieConverter(wrapper=_handcrafted()).convert(name="t").csvpath)
    assert md["macie-origin"] == "handcrafted"
    for k in [
        "macie-job-id",
        "macie-account",
        "macie-region",
        "macie-source-arn",
        "macie-downloaded-at",
    ]:
        assert k not in md


def test_macie_converter_template_metadata() -> None:
    w = _handcrafted()
    w["source"] = {
        "origin": "template",
        "account_id": "123456789012",
        "region": "eu-west-1",
        "downloaded_at": "2026-10-29T17:40:00Z",
        "template_id": "a1b2c3",
    }
    w["selection"]["managedDataIdentifierSelector"] = "RECOMMENDED"
    w["selection"]["managedDataIdentifierIds"] = []
    w["managedDataIdentifiers"] = {
        "resolved": ["CREDIT_CARD_NUMBER"],
        "resolution": {
            "method": "selector",
            "recommended_list": "automated-discovery-2026-10",
        },
    }
    w["aws"] = {
        "sensitivityInspectionTemplate": {"name": "automated-discovery", "id": "a1b2c3"}
    }
    conversion = MacieConverter(wrapper=w).convert()
    md = _metadata(conversion.csvpath)
    assert conversion.name == "automated-discovery"
    assert md["macie-template-id"] == "a1b2c3"
    assert md["macie-region"] == "eu-west-1"
    assert "macie-job-id" not in md
    assert "macie-source-arn" not in md


@pytest.mark.parametrize(
    "value, expected",
    [
        ("2026-10-29T17:40:00Z", "20261029T174000Z"),
        ("2026-10-29T17:40:00.123456Z", "20261029T174000Z"),
    ],
)
def test_macie_converter_downloaded_at(value: str, expected: str) -> None:
    w = _job()
    w["source"]["downloaded_at"] = value
    md = _metadata(MacieConverter(wrapper=w).convert().csvpath)
    assert md["macie-downloaded-at"] == expected


#
# the wrapper schema requires UTC with a trailing Z, so these fail when the
# wrapper is validated
#
@pytest.mark.parametrize(
    "value", ["yesterday", "2026-10-29T17:40:00", "2026-10-29T19:40:00+02:00"]
)
def test_macie_converter_bad_downloaded_at(value: str) -> None:
    w = _job()
    w["source"]["downloaded_at"] = value
    with pytest.raises(MacieException):
        MacieConverter(wrapper=w).convert()


def test_macie_converter_limits() -> None:
    md = _metadata(
        MacieConverter(wrapper=_job()).convert(max_findings=50, max_detail=0).csvpath
    )
    assert md["macie-max-findings"] == "50"
    assert md["macie-max-detail"] == "0"


@pytest.mark.parametrize(
    "args",
    [
        {"max_findings": 0},
        {"max_findings": "10"},
        {"max_findings": True},
        {"max_detail": -1},
        {"max_detail": None},
    ],
)
def test_macie_converter_bad_limits(args: dict) -> None:
    with pytest.raises(ValueError):
        MacieConverter(wrapper=_job()).convert(**args)


# =============
# body
# =============


def test_macie_converter_body_order() -> None:
    #
    # allow lists first, then the identifiers, then the report
    #
    csvpath = MacieConverter(wrapper=_job()).convert().csvpath
    body = csvpath.split("~")[2]
    assert body.index("macie_allow_regex") < body.index("macie_cdi(")
    assert body.index('"EmployeeId"') < body.index('"LegacyAccount"')
    assert body.rstrip().endswith("last.nocontrib() -> macie_report()\n]")


def test_macie_converter_cdi_arguments() -> None:
    csvpath = MacieConverter(wrapper=_job()).convert().csvpath
    assert (
        '    macie_cdi(\n        "LegacyAccount",\n'
        '        "arn:aws:macie2:us-east-1:123456789012:custom-data-identifier/'
        '7f6e5d4c-3b2a-4190-8e7f-6a5b4c3d2e1f",\n'
        "        /ACCT[0-9]{8}/,\n"
    ) in csvpath


def test_macie_converter_handcrafted_defaults() -> None:
    #
    # no ARN, no ignore words, no severity levels (Macie's default)
    #
    csvpath = MacieConverter(wrapper=_handcrafted()).convert(name="t").csvpath
    assert (
        '        "EmployeeId",\n'
        '        "",\n'
        "        /EMP-\\d{6}/,\n"
        '        "employee id",\n'
        '        "",\n'
        "        50,\n"
        '        "1:MEDIUM"\n'
    ) in csvpath


def test_macie_converter_data_path(tmp_path) -> None:
    data = tmp_path / "d.csv"
    data.write_text("a\n1\n", encoding="utf-8")
    csvpath = MacieConverter(wrapper=_job()).convert(path=str(data)).csvpath
    assert f"\n${data}[1*][\n" in csvpath


def test_macie_converter_missing_data_path() -> None:
    with pytest.raises(ValueError):
        MacieConverter(wrapper=_job()).convert(path="no/such/file.csv")


def test_macie_converter_needs_a_custom_identifier() -> None:
    w = _handcrafted()
    w["customDataIdentifiers"] = []
    w["selection"]["customDataIdentifierIds"] = []
    with pytest.raises(MacieException):
        MacieConverter(wrapper=w).convert(name="t")


@pytest.mark.parametrize(
    "field, value",
    [
        ("keywords", ["emp|id"]),
        ("keywords", ['emp "id"']),
        ("ignoreWords", ["EMP|0000"]),
        ("name", 'Employee "Id"'),
    ],
)
def test_macie_converter_inexpressible_values_fail(field: str, value) -> None:
    w = _handcrafted()
    w["customDataIdentifiers"][0][field] = value
    with pytest.raises(MacieException):
        MacieConverter(wrapper=w).convert(name="t")


def test_macie_converter_bad_regex_fails() -> None:
    w = _handcrafted()
    w["customDataIdentifiers"][0]["regex"] = "(EMP"
    with pytest.raises(MacieException):
        MacieConverter(wrapper=w).convert(name="t")


def test_macie_converter_bad_cdi_arn_fails() -> None:
    w = _handcrafted()
    w["customDataIdentifiers"][0]["arn"] = "arn:aws:s3:::bucket"
    with pytest.raises(MacieException):
        MacieConverter(wrapper=w).convert(name="t")


# =============
# regex literals, through a real run
# =============


@pytest.mark.parametrize(
    "regex, cell, count",
    [
        #
        # a slash must be escaped so the literal ends where it should
        #
        (r"ID/\d{3}", "ID/123", 1),
        (r"\d{2}/\d{2}/\d{4}", "10/31/2026", 1),
        #
        # a mid-pattern flag, which Python rejects and RegexUtility rewrites
        #
        (r"EMP(?i)-x\d{2}", "EMP-X12", 1),
        #
        # characters with meaning in the CVL grammar
        #
        (r"A\]B", "A]B", 1),
        (r"\(\d\)", "(7)", 1),
        (r"[,;]\d", ",5", 1),
    ],
)
def test_macie_converter_regex_literals_run(
    tmp_path, regex: str, cell: str, count: int
) -> None:
    w = _handcrafted()
    w["customDataIdentifiers"][0]["regex"] = regex
    w["customDataIdentifiers"][0]["keywords"] = []
    w["allowLists"] = []
    w["selection"]["allowListIds"] = []
    data = tmp_path / "d.csv"
    data.write_text(f'v\n"{cell}"\n', encoding="utf-8")
    csvpath = MacieConverter(wrapper=w).convert(name="t").csvpath
    path, matched = _run(csvpath=csvpath, data=str(data))
    findings = path.variables["macie_findings"]
    assert findings["customDataIdentifiers"]["totalCount"] == count
    assert path.errors and path.is_valid is True


# =============
# report
# =============


def test_macie_converter_report() -> None:
    skipped = MacieConverter(wrapper=_job()).convert().report.skipped
    assert [(s.location, s.feature) for s in skipped] == [
        ("allowLists[1]", "allowList.s3WordsList"),
        ("managedDataIdentifiers.resolved[0]", "managedDataIdentifier"),
        ("managedDataIdentifiers.resolved[1]", "managedDataIdentifier"),
        ("managedDataIdentifiers.resolved[2]", "managedDataIdentifier"),
        ("findingsFilters[0]", "findingsFilter"),
        ("findingsFilters[1]", "findingsFilter"),
        ("warnings[0]", "warning.ALLOW_LIST_UNREADABLE"),
        ("warnings[1]", "warning.CDI_DELETED_BUT_SELECTED"),
    ]
    assert {s.object for s in skipped} == {"hr-exports-weekly"}
    assert "public-names" in skipped[0].reason
    assert "#470" in skipped[0].reason
    assert "CREDIT_CARD_NUMBER" in skipped[1].reason


def test_macie_converter_text_allow_list_is_not_in_the_csvpath() -> None:
    csvpath = MacieConverter(wrapper=_job()).convert().csvpath
    assert csvpath.count("macie_allow_regex") == 1
    assert '"acme-emails"' in csvpath
    assert "public-names" not in csvpath


def test_macie_converter_pair_report_is_empty() -> None:
    wrapper = MacieWrapperLoader.from_path(
        path=os.path.join(PAIR, "hr-employee-ids.macie.json")
    )
    assert MacieConverter(wrapper=wrapper).convert().report.skipped == []


def test_macie_converter_does_not_change_the_wrapper() -> None:
    w = _job()
    before = copy.deepcopy(w)
    MacieConverter(wrapper=w).convert()
    assert w == before


def test_macie_converter_bad_wrapper() -> None:
    with pytest.raises(ValueError):
        MacieConverter(wrapper=None)
    with pytest.raises(MacieException):
        MacieConverter(wrapper={"not": "a wrapper"})
