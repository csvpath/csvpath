"""JevReviewer: the questions it builds from ColumnFacts, and how it maps
Jev's answers to review entries. Jev is never called: a fake client
stands in for the SDK's, through the reviewer's client_factory."""

import pytest

from csvpath.macie.column_facts import ColumnFacts
from csvpath.macie.jev_reviewer import JevReviewer


class _Usage:
    def __init__(self, i: int, o: int) -> None:
        self.input_tokens = i
        self.output_tokens = o


class _Answer:
    def __init__(self, d: dict) -> None:
        self.d = d

    def model_dump(self) -> dict:
        return dict(self.d)


class _Response:
    def __init__(self, answers: dict) -> None:
        self.model = "jev-1.14.0"
        self.usage = _Usage(100 * len(answers), 10 * len(answers))
        self.answers = {k: _Answer(v) for k, v in answers.items()}


class _Client:
    """records what it is sent; answers from a function of the question"""

    def __init__(self, answer, calls: list) -> None:
        self.answer = answer
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *a) -> None:
        return None

    def system_one(self, *, state, questions):
        self.calls.append({"state": state, "questions": questions})
        if isinstance(self.answer, Exception):
            raise self.answer
        #
        # the reviewer sends the SDK's Choice objects; the fake answers
        # from their text
        #
        return _Response({k: self.answer(q.instructions) for k, q in questions.items()})


def _choice(choice: str, likely: float) -> dict:
    rest = (1.0 - likely) / 2
    return {
        "type": "choice",
        "choice": choice,
        "confidence": 0.9,
        "probabilities": {"likely": likely, "doubtful": rest, "unrelated": rest},
    }


def _reviewer(answer, *, max_questions: int = 50) -> tuple[JevReviewer, list]:
    calls = []
    factory_calls = []

    def factory(*, model, api_key):
        factory_calls.append((model, api_key))
        return _Client(answer, calls)

    r = JevReviewer(key="k", max_questions=max_questions, client_factory=factory)
    return r, calls


def _facts(name: str, column: int, header: str, cells: list[str], why=None):
    f = ColumnFacts(identifier=name, column=column, column_name=header, why=why)
    for c in cells:
        f.add(cell=c, occurrences=1)
    return f


SSN = "USA_SOCIAL_SECURITY_NUMBER"
PLACEHOLDER = _facts(
    SSN, 7, "ref_no", ["123-45-6789"] * 40, why="a keyword is in the cell"
)
REAL = _facts(
    SSN,
    3,
    "ssn",
    ["309-04-7794", "166-46-2907", "716-90-7411"],
    why="the column header holds a keyword",
)
COLUMNS = ["order_id", "customer", "ssn", "sku", "qty", "ship_date", "ref_no"]


def test_macie_jev_meaning() -> None:
    assert JevReviewer.meaning(identifier=SSN) == "usa social security number"
    assert JevReviewer.meaning(identifier="EmployeeId") == "employee id"
    assert JevReviewer.meaning(identifier="CREDIT_CARD_NUMBER_(NO_KEYWORD)") == (
        "credit card number (no keyword)"
    )
    with pytest.raises(ValueError):
        JevReviewer.meaning(identifier=" ")


def test_macie_jev_question() -> None:
    q = JevReviewer.question(
        facts=PLACEHOLDER, file="orders.csv", columns=COLUMNS, rows=40
    )
    assert q.splitlines() == [
        "Identifier: USA_SOCIAL_SECURITY_NUMBER (usa social security number).",
        "File: orders.csv. Columns: order_id, customer, ssn, sku, qty, ship_date, ref_no.",
        "Flagged column: ref_no (column 7).",
        "Flagged in 40 of 40 rows; 1 distinct flagged values.",
        "Facts the scan computed about the flagged values:",
        "  - Every one of the 40 flagged values is the same value.",
        "Why the scan flagged them: a keyword is in the cell.",
        "Masked samples of flagged cells:",
        '  "###-##-####"',
        "Is it likely that the flagged values in the ref_no column are real: "
        "usa social security number?",
    ]
    #
    # no value reaches the question
    #
    assert "123-45-6789" not in q


def test_macie_jev_question_bad_input() -> None:
    with pytest.raises(TypeError):
        JevReviewer.question(facts={}, file="f", columns=[], rows=1)
    with pytest.raises(TypeError):
        JevReviewer.question(facts=REAL, file=None, columns=[], rows=1)
    with pytest.raises(TypeError):
        JevReviewer.question(facts=REAL, file="f", columns="a,b", rows=1)
    for rows in [-1, True, "3"]:
        with pytest.raises(ValueError):
            JevReviewer.question(facts=REAL, file="f", columns=[], rows=rows)


def test_macie_jev_review_complete() -> None:
    def answer(q: str) -> dict:
        return (
            _choice("unrelated", 0.06)
            if "ref_no column" in q
            else _choice("likely", 0.91)
        )

    r, calls = _reviewer(answer)
    out = r.review(
        facts=[PLACEHOLDER, REAL], file="orders.csv", columns=COLUMNS, rows=40
    )
    assert out["status"] == JevReviewer.COMPLETE
    assert out["reason"] is None
    assert out["model"] == "jev-1.14.0"
    assert (out["questions"], out["input_tokens"], out["output_tokens"]) == (2, 200, 20)
    assert [
        (e["columnName"], e["verdict"], e["confidence"]) for e in out["entries"]
    ] == [
        ("ref_no", "unrelated", 0.06),
        ("ssn", "likely", 0.91),
    ]
    assert out["entries"][0]["facts"] == [
        "Every one of the 40 flagged values is the same value."
    ]
    #
    # one request for the file, with the state and one choice() per item
    #
    assert len(calls) == 1
    assert calls[0]["state"] == JevReviewer.STATE
    assert sorted(calls[0]["questions"]) == ["q1", "q2"]
    sent = calls[0]["questions"]["q1"]
    assert type(sent).__name__ == "Choice"
    assert sorted(sent.criteria) == ["doubtful", "likely", "unrelated"]
    assert out["request"]["questions"]["q1"].startswith("Identifier: USA_SOCIAL")
    assert out["response"]["answers"]["q2"]["choice"] == "likely"


def test_macie_jev_review_max_questions() -> None:
    r, calls = _reviewer(lambda q: _choice("likely", 0.9), max_questions=1)
    out = r.review(
        facts=[PLACEHOLDER, REAL], file="orders.csv", columns=COLUMNS, rows=40
    )
    assert out["status"] == JevReviewer.PARTIAL
    assert "review_max_questions is 1" in out["reason"]
    assert len(out["entries"]) == 1
    assert out["not_reviewed"] == [
        {"identifier": SSN, "column": 3, "columnName": "ssn"}
    ]
    assert len(calls[0]["questions"]) == 1


def test_macie_jev_review_nothing_to_ask() -> None:
    r, calls = _reviewer(lambda q: _choice("likely", 0.9))
    out = r.review(facts=[], file="f.csv", columns=[], rows=0)
    assert out["status"] == JevReviewer.COMPLETE
    assert out["questions"] == 0
    assert calls == []


@pytest.mark.parametrize(
    "answer, reason",
    [
        (ConnectionError("no route to host"), "ConnectionError: no route to host"),
        (lambda q: {"type": "noul", "noul": 0.5}, "no choice answer"),
        (lambda q: _choice("maybe", 0.5), "unknown choice 'maybe'"),
        (
            lambda q: {"type": "choice", "choice": "likely", "probabilities": {}},
            "no probability",
        ),
    ],
)
def test_macie_jev_review_failed(answer, reason: str) -> None:
    #
    # a review that cannot be done is a status with the reason; the
    # findings are untouched by it (David, 2026-11-15)
    #
    r, _ = _reviewer(answer)
    out = r.review(facts=[REAL], file="f.csv", columns=COLUMNS, rows=3)
    assert out["status"] == JevReviewer.FAILED
    assert reason in out["reason"]
    assert out["entries"] == []


def test_macie_jev_reviewer_bad_input() -> None:
    for kw in [
        {"key": ""},
        {"key": "k", "model": " "},
        {"key": "k", "model": "jev-latest"},
        {"key": "k", "max_questions": 0},
        {"key": "k", "max_questions": True},
    ]:
        with pytest.raises(ValueError):
            JevReviewer(**kw)
    with pytest.raises(TypeError):
        JevReviewer(key="k", client_factory="not callable")
    r, _ = _reviewer(lambda q: _choice("likely", 0.9))
    with pytest.raises(TypeError):
        r.review(facts=[{}], file="f", columns=[], rows=1)


def test_macie_jev_reviewer_default_client_is_the_sdk() -> None:
    #
    # built, not used: no network
    #
    r = JevReviewer(key="k")
    client = r.client_factory(model=r.model, api_key=r.key)
    assert type(client).__name__ == "TypeSafeClient"
    client.close()
