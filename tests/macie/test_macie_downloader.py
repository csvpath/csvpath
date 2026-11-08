"""MacieDownloader, offline (specs/macie/download-design.md). botocore's
Stubber serves the AWS responses and checks every request's parameters and
every canned response against AWS's own macie2, s3 and sts service
models, so a misspelled parameter or a wrong shape fails here, with no AWS
account and no cost. No test here calls AWS."""

import datetime
import io
import json

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_downloader import MacieDownloader
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.recommended_lists import RecommendedLists

UTC = datetime.timezone.utc
ACCOUNT = "123456789012"
REGION = "us-east-1"
JOB_ID = "3ce05dbb7ec5505def334104bf1b3bca"
JOB_ARN = f"arn:aws:macie2:{REGION}:{ACCOUNT}:classification-job/{JOB_ID}"
CDI_ID = "2a1b7e4c-5d3f-4e8a-9b0c-1d2e3f4a5b6c"
REGEX_LIST = "k3m9p2q8r5t1v7w4x6y0za"
WORDS_LIST = "b8c2d4f6h1j3l5n7p9r0sa"
FILTER_ID = "f1f2f3f4-0000-4000-8000-000000000001"
TEMPLATE_ID = "e2a5b8c1d4f7a0b3c6d9e2f5a8b1c4d7"
WHEN = datetime.datetime(2026, 4, 10, 12, 0, tzinfo=UTC)
NOW = datetime.datetime(2026, 11, 8, 17, 40, tzinfo=UTC)
WORDS = b"Akua Mansa\n\nEMP-111111\n  EMP-222222  \n"


def _downloader():
    session = boto3.Session(
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        region_name=REGION,
    )
    d = MacieDownloader(session=session, clock=lambda: NOW)
    stubs = {
        "macie": Stubber(d.macie),
        "s3": Stubber(d.s3),
        "sts": Stubber(d.sts),
    }
    return d, stubs


def _activate(stubs):
    for s in stubs.values():
        s.activate()


def _done(stubs):
    for s in stubs.values():
        s.assert_no_pending_responses()
        s.deactivate()


def _identity(stubs):
    stubs["sts"].add_response(
        "get_caller_identity",
        {
            "Account": ACCOUNT,
            "Arn": f"arn:aws:iam::{ACCOUNT}:user/ci",
            "UserId": "AIDA",
        },
        {},
    )


def _job(stubs, *, selector="INCLUDE", ids=None, cdis=None, lists=None):
    stubs["macie"].add_response(
        "describe_classification_job",
        {
            "jobArn": JOB_ARN,
            "jobId": JOB_ID,
            "name": "hr-employee-ids",
            "jobStatus": "COMPLETE",
            "jobType": "ONE_TIME",
            "createdAt": WHEN,
            "managedDataIdentifierSelector": selector,
            "managedDataIdentifierIds": ids
            if ids is not None
            else ["CREDIT_CARD_NUMBER"],
            "customDataIdentifierIds": cdis if cdis is not None else [CDI_ID],
            "allowListIds": lists if lists is not None else [REGEX_LIST, WORDS_LIST],
            "s3JobDefinition": {
                "bucketDefinitions": [{"accountId": ACCOUNT, "buckets": ["acme-hr"]}]
            },
            "samplingPercentage": 100,
        },
        {"jobId": JOB_ID},
    )


def _available(stubs, ids):
    #
    # two pages, so pagination is exercised
    #
    half = len(ids) // 2
    stubs["macie"].add_response(
        "list_managed_data_identifiers",
        {
            "items": [
                {"category": "PERSONAL_INFORMATION", "id": i} for i in ids[:half]
            ],
            "nextToken": "page-2",
        },
        {},
    )
    stubs["macie"].add_response(
        "list_managed_data_identifiers",
        {"items": [{"category": "PERSONAL_INFORMATION", "id": i} for i in ids[half:]]},
        {"nextToken": "page-2"},
    )


def _cdi(stubs, *, deleted=False):
    stubs["macie"].add_response(
        "get_custom_data_identifier",
        {
            "arn": f"arn:aws:macie2:{REGION}:{ACCOUNT}:custom-data-identifier/{CDI_ID}",
            "createdAt": WHEN,
            "deleted": deleted,
            "id": CDI_ID,
            "name": "EmployeeId",
            "regex": "EMP-\\d{6}",
            "keywords": ["employee id"],
            "ignoreWords": [],
            "maximumMatchDistance": 50,
            "severityLevels": [{"occurrencesThreshold": 1, "severity": "MEDIUM"}],
        },
        {"id": CDI_ID},
    )


def _allow_lists(stubs, *, s3=None, words_status="OK"):
    stubs["macie"].add_response(
        "get_allow_list",
        {
            "arn": f"arn:aws:macie2:{REGION}:{ACCOUNT}:allow-list/{REGEX_LIST}",
            "createdAt": WHEN,
            "updatedAt": WHEN,
            "criteria": {"regex": "[a-z]+@acme\\.com"},
            "id": REGEX_LIST,
            "name": "acme-emails",
            "status": {"code": "OK"},
        },
        {"id": REGEX_LIST},
    )
    stubs["macie"].add_response(
        "get_allow_list",
        {
            "arn": f"arn:aws:macie2:{REGION}:{ACCOUNT}:allow-list/{WORDS_LIST}",
            "createdAt": WHEN,
            "updatedAt": WHEN,
            "criteria": {
                "s3WordsList": {"bucketName": "acme-lists", "objectKey": "names.txt"}
            },
            "id": WORDS_LIST,
            "name": "contractors",
            "status": {"code": words_status},
        },
        {"id": WORDS_LIST},
    )
    params = {"Bucket": "acme-lists", "Key": "names.txt"}
    if s3 is None:
        stubs["s3"].add_response(
            "get_object", {"Body": StreamingBody(io.BytesIO(WORDS), len(WORDS))}, params
        )
    elif isinstance(s3, bytes):
        stubs["s3"].add_response(
            "get_object", {"Body": StreamingBody(io.BytesIO(s3), len(s3))}, params
        )
    else:
        stubs["s3"].add_client_error(
            "get_object",
            service_error_code=s3,
            http_status_code=403,
            expected_params=params,
        )


def _filters(stubs, n=1):
    stubs["macie"].add_response(
        "list_findings_filters",
        {
            "findingsFilterListItems": [
                {"id": FILTER_ID, "name": "suppress-test", "action": "ARCHIVE"}
            ][:n]
        },
        {},
    )
    if n:
        stubs["macie"].add_response(
            "get_findings_filter",
            {
                "action": "ARCHIVE",
                "id": FILTER_ID,
                "name": "suppress-test",
                "position": 1,
                "findingCriteria": {
                    "criterion": {"severity.description": {"eq": ["Low"]}}
                },
            },
            {"id": FILTER_ID},
        )


def _download_job(stubs, d, **job):
    _activate(stubs)
    wrapper = d.download_job(job_id=JOB_ID)
    _done(stubs)
    return wrapper


#
# a job
#


def test_macie_download_job() -> None:
    d, stubs = _downloader()
    _identity(stubs)
    _job(stubs)
    _available(stubs, ["CREDIT_CARD_NUMBER", "USA_SOCIAL_SECURITY_NUMBER", "NAME"])
    _cdi(stubs)
    _allow_lists(stubs)
    _filters(stubs)
    w = _download_job(stubs, d)
    assert w["source"] == {
        "origin": "job",
        "account_id": ACCOUNT,
        "region": REGION,
        "downloaded_at": "2026-11-08T17:40:00Z",
        "job_id": JOB_ID,
    }
    assert w["selection"] == {
        "managedDataIdentifierSelector": "INCLUDE",
        "managedDataIdentifierIds": ["CREDIT_CARD_NUMBER"],
        "excludedManagedDataIdentifierIds": [],
        "customDataIdentifierIds": [CDI_ID],
        "allowListIds": [REGEX_LIST, WORDS_LIST],
    }
    m = w["managedDataIdentifiers"]
    assert m["resolved"] == ["CREDIT_CARD_NUMBER"]
    assert m["resolution"] == {"method": "selector", "recommended_list": None}
    assert [a["id"] for a in m["available"]] == [
        "CREDIT_CARD_NUMBER",
        "USA_SOCIAL_SECURITY_NUMBER",
        "NAME",
    ]
    #
    # verbatim, less ResponseMetadata, datetimes as UTC ISO 8601
    #
    job = w["aws"]["classificationJob"]
    assert job["jobArn"] == JOB_ARN
    assert job["createdAt"] == "2026-04-10T12:00:00Z"
    assert "ResponseMetadata" not in job
    assert w["customDataIdentifiers"][0]["regex"] == "EMP-\\d{6}"
    words = w["allowLists"][1]
    assert words["contents"] == {
        "status": "OK",
        "entries": ["Akua Mansa", "EMP-111111", "EMP-222222"],
        "sha256": __import__("hashlib").sha256(WORDS).hexdigest(),
        "error": None,
    }
    assert "contents" not in w["allowLists"][0]
    assert w["findingsFilters"][0]["id"] == FILTER_ID
    assert w["warnings"] == []
    json.dumps(w)


def test_macie_download_job_round_trip() -> None:
    #
    # the downloaded wrapper converts: download, then the offline load
    #
    d, stubs = _downloader()
    _identity(stubs)
    _job(stubs)
    _available(stubs, ["CREDIT_CARD_NUMBER", "NAME"])
    _cdi(stubs)
    _allow_lists(stubs)
    _filters(stubs, n=0)
    w = _download_job(stubs, d)
    conversion = MacieConverter(wrapper=w).convert(list_dir="lists")
    assert "macie_cdi(" in conversion.csvpath
    assert 'macie_mdi(\n        "CREDIT_CARD_NUMBER"' in conversion.csvpath
    assert conversion.lists == {WORDS_LIST: ["Akua Mansa", "EMP-111111", "EMP-222222"]}
    assert f"macie-source-arn: {JOB_ARN.replace(':', '|')}" in conversion.csvpath


@pytest.mark.parametrize(
    "selector, ids, expected",
    [
        ("EXCLUDE", ["NAME"], ["CREDIT_CARD_NUMBER", "USA_SOCIAL_SECURITY_NUMBER"]),
        ("ALL", [], ["CREDIT_CARD_NUMBER", "USA_SOCIAL_SECURITY_NUMBER", "NAME"]),
        ("NONE", [], []),
    ],
)
def test_macie_download_job_selectors(selector, ids, expected) -> None:
    d, stubs = _downloader()
    _identity(stubs)
    _job(stubs, selector=selector, ids=ids, cdis=[], lists=[])
    _available(stubs, ["CREDIT_CARD_NUMBER", "USA_SOCIAL_SECURITY_NUMBER", "NAME"])
    _filters(stubs, n=0)
    _activate(stubs)
    w = d.download_job(job_id=JOB_ID)
    _done(stubs)
    assert w["managedDataIdentifiers"]["resolved"] == expected
    assert w["selection"]["excludedManagedDataIdentifierIds"] == (
        ids if selector == "EXCLUDE" else []
    )


def test_macie_download_job_recommended() -> None:
    #
    # the account offers all but one recommended id: it is left out, with a
    # warning, so the wrapper never claims an identifier AWS does not run
    #
    recommended, label = RecommendedLists.for_job()
    offered = [i for i in recommended if i != "PKCS"]
    d, stubs = _downloader()
    _identity(stubs)
    _job(stubs, selector="RECOMMENDED", ids=[], cdis=[], lists=[])
    _available(stubs, offered)
    _filters(stubs, n=0)
    _activate(stubs)
    w = d.download_job(job_id=JOB_ID)
    _done(stubs)
    m = w["managedDataIdentifiers"]
    assert m["resolved"] == offered
    assert m["resolution"]["recommended_list"] == label
    assert [x["code"] for x in w["warnings"]] == ["RECOMMENDED_ID_UNAVAILABLE"]
    assert w["warnings"][0]["subject"] == "PKCS"


def test_macie_download_unreadable_words_list() -> None:
    d, stubs = _downloader()
    _identity(stubs)
    _job(stubs)
    _available(stubs, ["CREDIT_CARD_NUMBER"])
    _cdi(stubs)
    _allow_lists(stubs, s3="AccessDenied", words_status="S3_OBJECT_ACCESS_DENIED")
    _filters(stubs, n=0)
    w = _download_job(stubs, d)
    contents = w["allowLists"][1]["contents"]
    assert contents["status"] == "ACCESS_DENIED"
    assert contents["entries"] == [] and contents["sha256"] is None
    assert "s3://acme-lists/names.txt" in contents["error"]
    #
    # Macie's own status and ours are separate facts, each with a warning
    #
    assert [x["code"] for x in w["warnings"]] == [
        "MACIE_ALLOW_LIST_STATUS",
        "ALLOW_LIST_UNREADABLE",
    ]
    #
    # it still converts; the list is reported as not translated
    #
    conversion = MacieConverter(wrapper=w).convert(list_dir="lists")
    assert conversion.lists == {}


@pytest.mark.parametrize(
    "body, status",
    [
        (b"\n  \n", "EMPTY"),
        (("x" * 91 + "\n").encode(), "ERROR"),
        (b"\xff\xfe", "ERROR"),
    ],
)
def test_macie_download_words_list_problems(body: bytes, status: str) -> None:
    d, stubs = _downloader()
    _identity(stubs)
    _job(stubs)
    _available(stubs, ["CREDIT_CARD_NUMBER"])
    _cdi(stubs)
    _allow_lists(stubs, s3=body)
    _filters(stubs, n=0)
    w = _download_job(stubs, d)
    assert w["allowLists"][1]["contents"]["status"] == status
    assert w["warnings"][-1]["code"] == "ALLOW_LIST_UNREADABLE"


def test_macie_download_deleted_custom_identifier() -> None:
    d, stubs = _downloader()
    _identity(stubs)
    _job(stubs, lists=[])
    _available(stubs, ["CREDIT_CARD_NUMBER"])
    _cdi(stubs, deleted=True)
    _filters(stubs, n=0)
    w = _download_job(stubs, d)
    assert w["customDataIdentifiers"][0]["deleted"] is True
    warning = w["warnings"][0]
    assert warning["code"] == "CDI_DELETED_BUT_SELECTED"
    assert "deleted in Macie" in warning["message"]


def test_macie_download_stops_on_an_aws_error() -> None:
    d, stubs = _downloader()
    _identity(stubs)
    stubs["macie"].add_client_error(
        "describe_classification_job",
        service_error_code="AccessDeniedException",
        service_message="not authorized to perform macie2:DescribeClassificationJob",
        http_status_code=403,
        expected_params={"jobId": JOB_ID},
    )
    _activate(stubs)
    with pytest.raises(MacieException, match="AccessDeniedException"):
        d.download_job(job_id=JOB_ID)


def test_macie_download_stops_when_a_custom_identifier_is_unreachable() -> None:
    #
    # unreachable is not deleted: it stops the download, so it can never
    # look like a deletion in a wrapper
    #
    d, stubs = _downloader()
    _identity(stubs)
    _job(stubs, lists=[])
    _available(stubs, ["CREDIT_CARD_NUMBER"])
    stubs["macie"].add_client_error(
        "get_custom_data_identifier",
        service_error_code="ResourceNotFoundException",
        http_status_code=404,
        expected_params={"id": CDI_ID},
    )
    _activate(stubs)
    with pytest.raises(MacieException, match="ResourceNotFoundException"):
        d.download_job(job_id=JOB_ID)


#
# the automated-discovery template
#


def _template(stubs, *, first_enabled):
    stubs["macie"].add_response(
        "get_automated_discovery_configuration",
        {
            "classificationScopeId": "c" * 32,
            "sensitivityInspectionTemplateId": TEMPLATE_ID,
            "status": "ENABLED",
            "firstEnabledAt": first_enabled,
        },
        {},
    )
    stubs["macie"].add_response(
        "get_sensitivity_inspection_template",
        {
            "sensitivityInspectionTemplateId": TEMPLATE_ID,
            "name": "automated-sensitive-data-discovery",
            "includes": {
                "managedDataIdentifierIds": ["DATE_OF_BIRTH"],
                "customDataIdentifierIds": [],
                "allowListIds": [],
            },
            "excludes": {"managedDataIdentifierIds": ["PKCS"]},
        },
        {"id": TEMPLATE_ID},
    )


@pytest.mark.parametrize(
    "first_enabled, list_name",
    [
        (datetime.datetime(2024, 3, 1, tzinfo=UTC), RecommendedLists.AUTOMATED),
        (datetime.datetime(2023, 1, 5, tzinfo=UTC), RecommendedLists.AUTOMATED_STATIC),
    ],
)
def test_macie_download_template(first_enabled, list_name) -> None:
    data = RecommendedLists.load(name=list_name)
    d, stubs = _downloader()
    _identity(stubs)
    _template(stubs, first_enabled=first_enabled)
    _available(stubs, list(data["ids"]) + ["DATE_OF_BIRTH"])
    _filters(stubs, n=0)
    _activate(stubs)
    w = d.download_template()
    _done(stubs)
    assert w["source"]["origin"] == "template"
    assert w["source"]["template_id"] == TEMPLATE_ID
    assert "sensitivityInspectionTemplate" in w["aws"]
    m = w["managedDataIdentifiers"]
    assert m["resolution"]["recommended_list"] == RecommendedLists.label(data=data)
    #
    # the account's recommended set, plus includes, less excludes
    #
    assert "DATE_OF_BIRTH" in m["resolved"]
    assert "PKCS" not in m["resolved"]
    assert set(m["resolved"]) == (set(data["ids"]) | {"DATE_OF_BIRTH"}) - {"PKCS"}
    assert w["selection"]["managedDataIdentifierSelector"] == "RECOMMENDED"
    #
    # a template has no ARN: none is invented
    #
    conversion = MacieConverter(wrapper=w).convert()
    assert "macie-source-arn" not in conversion.csvpath
    assert f"macie-template-id: {TEMPLATE_ID}" in conversion.csvpath


def test_macie_download_template_not_set_up() -> None:
    d, stubs = _downloader()
    _identity(stubs)
    stubs["macie"].add_response(
        "get_automated_discovery_configuration", {"status": "DISABLED"}, {}
    )
    _activate(stubs)
    with pytest.raises(MacieException, match="no sensitivity inspection template"):
        d.download_template()


def test_macie_downloader_bad_input() -> None:
    with pytest.raises(ValueError):
        MacieDownloader(session=None)

    #
    # a stand-in session: a real one could pick a region up from the
    # machine's AWS config
    #
    class NoRegion:
        region_name = None

    with pytest.raises(ValueError, match="region"):
        MacieDownloader(session=NoRegion())
    d, _ = _downloader()
    with pytest.raises(ValueError):
        d.download_job(job_id="")
    with pytest.raises(TypeError):
        MacieDownloader(
            session=boto3.Session(
                aws_access_key_id="t", aws_secret_access_key="t", region_name=REGION
            ),
            clock="now",
        )
