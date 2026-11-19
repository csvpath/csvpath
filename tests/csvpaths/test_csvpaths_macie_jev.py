"""NAME and ADDRESS through Jev in a named-paths group run
(specs/macie/jev-names-addresses-design.md), with a fake Jev:
MacieReview.CLIENT_FACTORY stands in for the SDK's client, so nothing
reaches the network.

The wrapper selects EmployeeId (a custom identifier), NAME and ADDRESS.
The converter writes macie_jev.nocontrib() for NAME and ADDRESS; they are
checked only when config.ini [macie] review names them, and their results
are a jev section apart from the Macie-shaped findings.

Each CsvPath in a group run reads config.ini itself, so each test writes
a copy of the active config.ini with the keys and points
CSVPATH_CONFIG_PATH at it, for that test only."""

import configparser
import copy
import json
import os

import pytest

from csvpath import CsvPaths
from csvpath.macie.macie_review import MacieReview

WRAPPERS = os.path.join("tests", "macie", "test_resources", "wrappers")
GROUP = "macie_jev_test"
NAMED_FILE = "macie_jev_test_people"
ROWS = [
    ["id", "full_name", "address", "notes"],
    ["1", "Akua Mansa", "12 Main St, Springfield, IL 62704", "employee id EMP-123456"],
    ["2", "Omar Haddad", "9 Oak St, Austin, TX 78701", ""],
    ["3", "Sara Lund", "", "left a voicemail"],
    ["4", "Ken Ito", "77 Elm Ave, Denver, CO 80202", ""],
]


class _Usage:
    input_tokens = 260
    output_tokens = 30


class _Answer:
    def __init__(self, d: dict) -> None:
        self.d = d

    def model_dump(self) -> dict:
        return dict(self.d)


def _choice(likely: float) -> dict:
    rest = (1.0 - likely) / 2
    return {
        "type": "choice",
        "choice": "likely" if likely >= 0.5 else "unrelated",
        "confidence": 0.9,
        "probabilities": {"likely": likely, "doubtful": rest, "unrelated": rest},
    }


class _Response:
    def __init__(self, questions: dict) -> None:
        self.model = "jev-1.14.0"
        self.usage = _Usage()
        self.answers = {
            k: _Answer(self._answer(q.instructions)) for k, q in questions.items()
        }

    @classmethod
    def _answer(cls, q: str) -> dict:
        if "Identifier: NAME" in q and "Column: full_name." in q:
            return _choice(0.95)
        if "Identifier: ADDRESS" in q and "Column: address." in q:
            return _choice(0.9)
        return _choice(0.05)


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


def _config(*, tmp_path, monkeypatch, review: str | None) -> None:
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
    parser.set("jev", "key", "test-key")
    with open(target, "w", encoding="utf-8") as f:
        parser.write(f)
    monkeypatch.setenv("CSVPATH_CONFIG_PATH", target)


def _files(tmp_path) -> tuple[str, str]:
    with open(
        os.path.join(WRAPPERS, "handcrafted_minimal.macie.json"), encoding="utf-8"
    ) as f:
        w = json.load(f)
    ids = ["NAME", "ADDRESS"]
    w["selection"]["managedDataIdentifierIds"] = list(ids)
    w["managedDataIdentifiers"]["resolved"] = list(ids)
    w["allowLists"] = []
    w["selection"]["allowListIds"] = []
    wrapper = os.path.join(tmp_path, "people-jev.macie.json")
    with open(wrapper, "w", encoding="utf-8") as f:
        json.dump(w, f)
    data = os.path.join(tmp_path, "people.csv")
    with open(data, "w", encoding="utf-8") as f:
        f.write(
            "\n".join(",".join(f'"{c}"' if "," in c else c for c in r) for r in ROWS)
        )
        f.write("\n")
    return wrapper, data


def _run(*, tmp_path, client=_Client):
    wrapper, data = _files(tmp_path)
    paths = CsvPaths()
    paths.paths_manager.remove_named_paths(GROUP)
    paths.file_manager.remove_named_file(NAMED_FILE)
    MacieReview.CLIENT_FACTORY = lambda *, model, api_key: client()
    try:
        paths.paths_manager.add_named_paths_from_file(name=GROUP, file_path=wrapper)
        paths.file_manager.add_named_file(name=NAMED_FILE, path=data)
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


def _without_jev(findings: dict) -> dict:
    f = copy.deepcopy(findings)
    f.pop("jev", None)
    return f


def test_csvpaths_macie_jev_off_without_review(tmp_path, monkeypatch) -> None:
    _config(tmp_path=tmp_path, monkeypatch=monkeypatch, review=None)
    result = _run(tmp_path=tmp_path)
    jev = result.csvpath.variables["macie_findings"]["jev"]
    assert jev["status"] == "off"
    assert [n["identifier"] for n in jev["not_checked"]] == ["NAME", "ADDRESS"]
    assert jev["detections"] == []
    assert _Client.sent == []
    assert (
        f"macie jev: ADDRESS, NAME not checked: {MacieReview.NOT_NAMED}"
        in result.get_printouts("macie")
    )
    path = os.path.join(result.run_dir, "_extra_data", "macie")
    assert not any(n.startswith("jev.") for n in os.listdir(path))


def test_csvpaths_macie_jev_finds_names_and_addresses(tmp_path, monkeypatch) -> None:
    _config(tmp_path=tmp_path, monkeypatch=monkeypatch, review=None)
    plain = _run(tmp_path=tmp_path).csvpath.variables["macie_findings"]
    _config(tmp_path=tmp_path, monkeypatch=monkeypatch, review="NAME, ADDRESS")
    result = _run(tmp_path=tmp_path)
    findings = result.csvpath.variables["macie_findings"]
    #
    # the Macie-shaped findings are the same with the check as without it
    #
    assert _without_jev(findings) == _without_jev(plain)
    jev = findings["jev"]
    assert jev["detectedBy"] == "jev"
    assert jev["status"] == "complete"
    assert jev["threshold"] == 0.7
    assert jev["model"] == "jev-1.14.0"
    by_type = {d["type"]: d for d in jev["detections"]}
    assert by_type["NAME"]["count"] == 4
    assert by_type["NAME"]["columns"][0]["columnName"] == "full_name"
    assert by_type["ADDRESS"]["count"] == 3
    assert by_type["ADDRESS"]["columns"][0]["column"] == 3
    assert jev["totalCount"] == 7
    assert jev["not_checked"] == []
    #
    # one request; ADDRESS is asked only of the address column, which has
    # postal codes: the others are screened out
    #
    assert len(_Client.sent) == 1
    questions = list(_Client.sent[0].values())
    assert sum("Identifier: ADDRESS" in q for q in questions) == 1
    assert sum("Identifier: NAME" in q for q in questions) == 4
    for q in questions:
        for value in ("Akua", "Mansa", "Springfield", "62704", "EMP-123456"):
            assert value not in q
    printouts = result.get_printouts("macie")
    assert "macie jev NAME column 2 full_name: 4 cells (likely, 0.95)" in printouts
    assert any(
        p.startswith("macie jev: complete, 5 questions, 2 columns found")
        for p in printouts
    )
    assert result.csvpath.is_valid
    path = os.path.join(result.run_dir, "_extra_data", "macie")
    records = [n for n in os.listdir(path) if n.startswith("jev.")]
    assert len(records) == 1
    with open(os.path.join(path, records[0]), encoding="utf-8") as f:
        record = json.load(f)
    assert record["status"] == "complete"
    assert sorted(record["request"]["questions"]) == sorted(
        record["response"]["answers"]
    )


def test_csvpaths_macie_jev_name_only(tmp_path, monkeypatch) -> None:
    _config(tmp_path=tmp_path, monkeypatch=monkeypatch, review="NAME")
    result = _run(tmp_path=tmp_path)
    jev = result.csvpath.variables["macie_findings"]["jev"]
    assert [d["type"] for d in jev["detections"]] == ["NAME"]
    assert jev["not_checked"] == [
        {"identifier": "ADDRESS", "reason": MacieReview.NOT_NAMED}
    ]
    assert all("Identifier: NAME" in q for q in _Client.sent[0].values())
    #
    # naming only NAME and ADDRESS starts no review of findings
    #
    assert "review" not in result.csvpath.variables["macie_findings"]["csvpath"]


def test_csvpaths_macie_jev_failure_keeps_the_run(tmp_path, monkeypatch) -> None:
    _config(tmp_path=tmp_path, monkeypatch=monkeypatch, review="NAME, ADDRESS")
    result = _run(tmp_path=tmp_path, client=_Failing)
    jev = result.csvpath.variables["macie_findings"]["jev"]
    assert jev["status"] == "failed"
    assert jev["reason"] == "ConnectionError: no route to host"
    assert jev["detections"] == []
    assert sorted(n["identifier"] for n in jev["not_checked"]) == ["ADDRESS", "NAME"]
    assert (
        "macie jev: ADDRESS, NAME not checked: ConnectionError: no route to host"
        in result.get_printouts("macie")
    )
    assert any("macie jev: NAME, ADDRESS not checked" in f"{e}" for e in result.errors)
    #
    # decided 2026-11-18: not checked, loudly; the run stays valid
    #
    assert result.csvpath.is_valid
