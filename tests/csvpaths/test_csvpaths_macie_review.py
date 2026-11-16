"""The Jev review in a named-paths group run (specs/macie/jev-review-
build.md), with a fake Jev: MacieReview.CLIENT_FACTORY stands in for the
SDK's client, so nothing reaches the network. The review annotates: the
findings are the same with it as without it.

Each CsvPath in a group run reads config.ini itself, so each test writes
a copy of the active config.ini with the review's keys and points
CSVPATH_CONFIG_PATH at it, for that test only: the review is configured
where users configure it."""

import configparser
import copy
import json
import os

import pytest

from csvpath import CsvPaths
from csvpath.macie.macie_review import MacieReview

PAIR = os.path.join(
    "tests", "macie", "test_resources", "normative", "09_text_allow_list"
)
WRAPPER = os.path.join(PAIR, "hr-contractor-allow.macie.json")
DATA = os.path.join(PAIR, "data", "employees.csv")
GROUP = "macie_review_test"
NAMED_FILE = "macie_review_test_employees"


class _Usage:
    input_tokens = 300
    output_tokens = 30


class _Answer:
    def __init__(self, d: dict) -> None:
        self.d = d

    def model_dump(self) -> dict:
        return dict(self.d)


class _Response:
    def __init__(self, keys) -> None:
        self.model = "jev-1.14.0"
        self.usage = _Usage()
        self.answers = {
            k: _Answer(
                {
                    "type": "choice",
                    "choice": "likely",
                    "confidence": 0.9,
                    "probabilities": {
                        "likely": 0.88,
                        "doubtful": 0.1,
                        "unrelated": 0.02,
                    },
                }
            )
            for k in keys
        }


class _Client:
    sent = []

    def __enter__(self):
        return self

    def __exit__(self, *a) -> None:
        return None

    def system_one(self, *, state, questions):
        _Client.sent.append({k: q.instructions for k, q in questions.items()})
        return _Response(questions)


class _Failing(_Client):
    def system_one(self, *, state, questions):
        raise ConnectionError("no route to host")


def _config(
    *,
    tmp_path,
    monkeypatch,
    review: str | None,
    key: str = "test-key",
    macie: dict | None = None,
) -> None:
    source = os.environ.get("CSVPATH_CONFIG_PATH") or os.path.join(
        "config", "config.ini"
    )
    parser = configparser.RawConfigParser()
    parser.read(source, encoding="utf-8")
    target = os.path.join(tmp_path, "config.ini")
    for section in ("config", "macie", "jev"):
        if not parser.has_section(section):
            parser.add_section(section)
    parser.set("config", "path", target)
    if review is None:
        parser.remove_option("macie", "review")
    else:
        parser.set("macie", "review", review)
    parser.set("jev", "key", key)
    for name, value in (macie or {}).items():
        parser.set("macie", name, value)
    with open(target, "w", encoding="utf-8") as f:
        parser.write(f)
    monkeypatch.setenv("CSVPATH_CONFIG_PATH", target)


def _run(*, client=_Client):
    paths = CsvPaths()
    paths.paths_manager.remove_named_paths(GROUP)
    paths.file_manager.remove_named_file(NAMED_FILE)
    MacieReview.CLIENT_FACTORY = lambda *, model, api_key: client()
    try:
        paths.paths_manager.add_named_paths_from_file(name=GROUP, file_path=WRAPPER)
        paths.file_manager.add_named_file(name=NAMED_FILE, path=DATA)
        paths.collect_paths(filename=NAMED_FILE, pathsname=GROUP)
    finally:
        MacieReview.CLIENT_FACTORY = None
    return paths.results_manager.get_named_results(GROUP)[0]


@pytest.fixture(autouse=True)
def clean():
    _Client.sent = []
    yield
    MacieReview.CLIENT_FACTORY = None
    paths = CsvPaths()
    paths.paths_manager.remove_named_paths(GROUP)
    paths.file_manager.remove_named_file(NAMED_FILE)


def _without_review(findings: dict) -> dict:
    f = copy.deepcopy(findings)
    f["csvpath"].pop("review", None)
    for d in f["customDataIdentifiers"]["detections"]:
        d.pop("review", None)
    for c in f["sensitiveData"]:
        for d in c["detections"]:
            d.pop("review", None)
    return f


def test_csvpaths_macie_review_annotates_only(tmp_path, monkeypatch) -> None:
    _config(tmp_path=tmp_path, monkeypatch=monkeypatch, review=None)
    plain = _run().csvpath.variables["macie_findings"]
    assert "review" not in plain["csvpath"]
    _config(tmp_path=tmp_path, monkeypatch=monkeypatch, review="EmployeeId")
    result = _run()
    reviewed = result.csvpath.variables["macie_findings"]
    #
    # every count, severity and cell as without the review
    #
    assert _without_review(reviewed) == plain
    detection = reviewed["customDataIdentifiers"]["detections"][0]
    assert detection["name"] == "EmployeeId"
    assert len(detection["review"]) >= 1
    for e in detection["review"]:
        assert (e["verdict"], e["confidence"]) == ("likely", 0.88)
        assert e["columnName"] in ("employee_id", "manager_note")
    summary = reviewed["csvpath"]["review"]
    assert summary["status"] == "complete"
    assert summary["model"] == "jev-1.14.0"
    assert summary["questions"] == len(detection["review"])
    assert result.csvpath.is_valid


def test_csvpaths_macie_review_sends_no_value(tmp_path, monkeypatch) -> None:
    _config(tmp_path=tmp_path, monkeypatch=monkeypatch, review="EmployeeId")
    _run()
    assert len(_Client.sent) == 1
    with open(DATA, encoding="utf-8") as f:
        text = f.read()
    assert "EMP-123456" in text
    for question in _Client.sent[0].values():
        assert "EMP-123456" not in question
        assert "AAA-######" in question
        #
        # the file as the user knows it, not the stored copy's hash name
        #
        assert f"File: {NAMED_FILE}." in question


def test_csvpaths_macie_review_printouts_and_record(tmp_path, monkeypatch) -> None:
    _config(tmp_path=tmp_path, monkeypatch=monkeypatch, review="EmployeeId")
    result = _run()
    printouts = result.get_printouts("macie")
    assert any(p.startswith("macie review EmployeeId column ") for p in printouts)
    assert any(p.startswith("macie review: complete, ") for p in printouts)
    path = os.path.join(result.run_dir, "_extra_data", "macie")
    records = [n for n in os.listdir(path) if n.startswith("review.")]
    assert len(records) == 1
    with open(os.path.join(path, records[0]), encoding="utf-8") as f:
        record = json.load(f)
    assert record["status"] == "complete"
    assert record["request"]["state"].startswith("A data-loss-prevention scan")
    assert sorted(record["request"]["questions"]) == sorted(
        record["response"]["answers"]
    )


def test_csvpaths_macie_review_failure_keeps_the_run(tmp_path, monkeypatch) -> None:
    _config(tmp_path=tmp_path, monkeypatch=monkeypatch, review="EmployeeId")
    result = _run(client=_Failing)
    findings = result.csvpath.variables["macie_findings"]
    assert findings["csvpath"]["review"]["status"] == "failed"
    assert (
        "ConnectionError: no route to host" in findings["csvpath"]["review"]["reason"]
    )
    assert "review" not in findings["customDataIdentifiers"]["detections"][0]
    printouts = result.get_printouts("macie")
    assert "macie review: failed: ConnectionError: no route to host" in printouts
    assert any("macie review failed" in f"{e}" for e in result.errors)
    #
    # decision 1 (David, 2026-11-15): the findings are complete; the run
    # stays valid
    #
    assert result.csvpath.is_valid


def test_csvpaths_macie_review_not_a_reviewed_identifier(tmp_path, monkeypatch) -> None:
    _config(
        tmp_path=tmp_path, monkeypatch=monkeypatch, review="USA_SOCIAL_SECURITY_NUMBER"
    )
    result = _run()
    findings = result.csvpath.variables["macie_findings"]
    assert findings["csvpath"]["review"]["status"] == "complete"
    assert findings["csvpath"]["review"]["questions"] == 0
    assert _Client.sent == []


def test_csvpaths_macie_review_when_the_breaker_trips(tmp_path, monkeypatch) -> None:
    #
    # pair 03 trips the breaker at 5 occurrences. The review runs when it
    # trips, from record(), and counts only what was recorded
    #
    pair = os.path.join("tests", "macie", "test_resources", "normative", "03_breaker")
    _config(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        review="EmployeeId, BadgeId",
        macie={"max_findings": "5"},
    )
    paths = CsvPaths()
    paths.paths_manager.remove_named_paths(GROUP)
    paths.file_manager.remove_named_file(NAMED_FILE)
    MacieReview.CLIENT_FACTORY = lambda *, model, api_key: _Client()
    try:
        paths.paths_manager.add_named_paths_from_file(
            name=GROUP, file_path=os.path.join(pair, "hr-badges.macie.json")
        )
        paths.file_manager.add_named_file(
            name=NAMED_FILE, path=os.path.join(pair, "data", "badges.csv")
        )
        paths.collect_paths(filename=NAMED_FILE, pathsname=GROUP)
    finally:
        MacieReview.CLIENT_FACTORY = None
    findings = paths.results_manager.get_named_results(GROUP)[0].csvpath.variables[
        "macie_findings"
    ]
    assert findings["csvpath"]["stopped"] is True
    assert findings["csvpath"]["review"]["status"] == "complete"
    assert len(_Client.sent) == 1
    flagged = sum(d["count"] for d in findings["customDataIdentifiers"]["detections"])
    assert flagged == 5
    reviewed = [
        e
        for d in findings["customDataIdentifiers"]["detections"]
        for e in d.get("review", [])
    ]
    assert len(reviewed) == findings["csvpath"]["review"]["questions"] >= 1
