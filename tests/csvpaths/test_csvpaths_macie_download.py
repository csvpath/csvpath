"""PathsManager.add_named_paths_from_macie(): download a Macie job's
setup and load it as a named-paths group, then run it
(specs/macie/download-design.md). The AWS side is botocore's Stubber,
serving normative pair 09's job as AWS would return it, so the group's
run must give pair 09's verified findings exactly. No AWS call is made."""

import datetime
import io
import json
import os

import boto3
import pytest
import yaml
from botocore.response import StreamingBody
from botocore.stub import Stubber

from csvpath import CsvPaths
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.macie_group_loader import MacieGroupLoader
from csvpath.util.nos import Nos

PAIR = os.path.join(
    "tests", "macie", "test_resources", "normative", "09_text_allow_list"
)
WRAPPER = os.path.join(PAIR, "hr-contractor-allow.macie.json")
GROUP = "macie_test_download"
NAMED_FILE = "macie_test_download_employees"
TIMES = {"createdAt", "updatedAt"}


def _pair() -> dict:
    with open(WRAPPER, encoding="utf-8") as f:
        return json.load(f)


def _as_aws(value):
    """the pair's JSON back to what boto3 returns: datetimes, not strings"""
    if isinstance(value, dict):
        return {
            k: (
                datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
                if k in TIMES
                else _as_aws(v)
            )
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_as_aws(v) for v in value]
    return value


class StubSession:
    """hands the downloader real boto3 clients, stubbed"""

    region_name = "us-east-1"

    def __init__(self) -> None:
        real = boto3.Session(
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
            region_name=self.region_name,
        )
        self.clients = {n: real.client(n) for n in ["macie2", "s3", "sts"]}
        self.stubs = {n: Stubber(c) for n, c in self.clients.items()}

    def client(self, name: str):
        return self.clients[name]

    def activate(self) -> None:
        for s in self.stubs.values():
            s.activate()

    def done(self) -> None:
        for s in self.stubs.values():
            s.assert_no_pending_responses()
            s.deactivate()


def _serve_pair_09(session: StubSession) -> None:
    w = _pair()
    job = w["aws"]["classificationJob"]
    macie, s3 = session.stubs["macie2"], session.stubs["s3"]
    session.stubs["sts"].add_response(
        "get_caller_identity",
        {
            "Account": w["source"]["account_id"],
            "Arn": "arn:aws:iam::1:user/ci",
            "UserId": "U",
        },
        {},
    )
    macie.add_response(
        "describe_classification_job", _as_aws(job), {"jobId": job["jobId"]}
    )
    macie.add_response(
        "list_managed_data_identifiers",
        {"items": w["managedDataIdentifiers"]["available"]},
        {},
    )
    for cdi in w["customDataIdentifiers"]:
        macie.add_response(
            "get_custom_data_identifier", _as_aws(cdi), {"id": cdi["id"]}
        )
    for a in w["allowLists"]:
        settings = a["settings"]
        macie.add_response("get_allow_list", _as_aws(settings), {"id": settings["id"]})
        words = settings["criteria"].get("s3WordsList")
        if words:
            body = "".join(f"{e}\n" for e in a["contents"]["entries"]).encode()
            s3.add_response(
                "get_object",
                {"Body": StreamingBody(io.BytesIO(body), len(body))},
                {"Bucket": words["bucketName"], "Key": words["objectKey"]},
            )
    macie.add_response("list_findings_filters", {"findingsFilterListItems": []}, {})


@pytest.fixture
def paths():
    p = CsvPaths()
    p.paths_manager.remove_named_paths(GROUP)
    p.file_manager.remove_named_file(NAMED_FILE)
    yield p
    p.paths_manager.remove_named_paths(GROUP)
    p.file_manager.remove_named_file(NAMED_FILE)


def test_macie_download_and_load_runs_as_pair_09(paths) -> None:
    paths.config.set(section="macie", name="max_detail", value="3")
    session = StubSession()
    _serve_pair_09(session)
    job_id = _pair()["source"]["job_id"]
    session.activate()
    ref = paths.paths_manager.add_named_paths_from_macie(
        name=GROUP, session=session, job_id=job_id
    )
    session.done()
    assert ref is not None
    #
    # the wrapper is in the group home and nowhere else, named for the
    # csvpath, with its report; the report and manifest say where it came
    # from
    #
    home = paths.paths_manager.named_paths_home(GROUP)
    wrapper_path = Nos(home).join("hr-contractor-allow.macie.json")
    with open(wrapper_path, encoding="utf-8") as f:
        stored = json.load(f)
    assert stored["source"]["job_id"] == job_id
    assert (
        stored["allowLists"][1]["contents"]["entries"]
        == (_pair()["allowLists"][1]["contents"]["entries"])
    )
    provenance = f"aws:macie2:us-east-1:123456789012:classification-job/{job_id}"
    with open(f"{wrapper_path}.report.json", encoding="utf-8") as f:
        report = json.load(f)
    assert report["source_path"] == provenance
    assert report["lists"] == [{"name": "c0n7r4a1c7o9r5s3a6l0lw", "entries": 3}]
    with open(Nos(home).join("manifest.json"), encoding="utf-8") as f:
        assert json.load(f)[-1]["source_path"] == provenance
    am = paths.paths_manager.asset_manager
    assert am.get_asset_file(GROUP, "macie_catalog.json") is not None
    #
    # the run gives pair 09's findings, printouts and finding lines
    #
    data = os.path.join(PAIR, "data", "employees.csv")
    paths.file_manager.add_named_file(name=NAMED_FILE, path=data)
    paths.collect_paths(filename=NAMED_FILE, pathsname=GROUP)
    result = paths.results_manager.get_named_results(GROUP)[0]
    with open(os.path.join(PAIR, "expected", "findings.json"), encoding="utf-8") as f:
        assert result.csvpath.variables["macie_findings"] == json.load(f)
    with open(
        os.path.join(PAIR, "expected", "printouts.macie.txt"), encoding="utf-8"
    ) as f:
        assert result.get_printouts("macie") == f.read().splitlines()
    with open(os.path.join(PAIR, "expected.yaml"), encoding="utf-8") as f:
        run = yaml.safe_load(f)["runs"][0]
    errors = [{"line": e.line_count, "message": e.message} for e in result.errors]
    assert errors == run["errors"]
    #
    # and the run kept the downloaded wrapper with its other inputs
    #
    inputs = os.path.join(result.run_dir, "_extra_data", "macie", "inputs.json")
    with open(inputs, encoding="utf-8") as f:
        assert "hr-contractor-allow.macie.json" in json.load(f)["files"]


def test_macie_download_and_load_stops_on_aws_errors(paths) -> None:
    session = StubSession()
    session.stubs["sts"].add_response(
        "get_caller_identity",
        {"Account": "123456789012", "Arn": "arn:aws:iam::1:user/ci", "UserId": "U"},
        {},
    )
    session.stubs["macie2"].add_client_error(
        "describe_classification_job",
        service_error_code="AccessDeniedException",
        http_status_code=403,
        expected_params={"jobId": "nope"},
    )
    session.activate()
    with pytest.raises(MacieException, match="AccessDeniedException"):
        paths.paths_manager.add_named_paths_from_macie(
            name=GROUP, session=session, job_id="nope"
        )
    assert not paths.paths_manager.has_named_paths(GROUP)


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"job_id": None, "template": False}, ValueError),
        ({"job_id": "j", "template": True}, ValueError),
        ({"job_id": "j", "template": "yes"}, TypeError),
        ({"job_id": "j", "append": "yes"}, TypeError),
        ({"job_id": "j", "name": ""}, ValueError),
    ],
)
def test_macie_download_and_load_bad_input(paths, kwargs, error) -> None:
    args = {"name": GROUP, "session": StubSession(), **kwargs}
    with pytest.raises(error):
        paths.paths_manager.add_named_paths_from_macie(**args)
    assert not paths.paths_manager.has_named_paths(GROUP)


def test_macie_provenance() -> None:
    job = {
        "origin": "job",
        "region": "eu-west-1",
        "account_id": "1" * 12,
        "job_id": "j1",
    }
    assert MacieGroupLoader.provenance(source=job) == (
        "aws:macie2:eu-west-1:111111111111:classification-job/j1"
    )
    template = {
        "origin": "template",
        "region": "eu-west-1",
        "account_id": "1" * 12,
        "template_id": "t1",
    }
    assert MacieGroupLoader.provenance(source=template).endswith(
        ":sensitivity-inspection-template/t1"
    )
    assert not MacieGroupLoader.provenance(source=template).startswith("arn:")
