"""JevDetector: the NAME and ADDRESS questions it builds from
ColumnShapes, which columns it asks about, and how it maps Jev's answers.
Jev is never called: a fake client stands in for the SDK's."""

import pytest

from csvpath.macie.column_shapes import ColumnShapes
from csvpath.macie.jev_detector import JevDetector


class _Usage:
    input_tokens = 250
    output_tokens = 40


class _Answer:
    def __init__(self, d: dict) -> None:
        self.d = d

    def model_dump(self) -> dict:
        return dict(self.d)


class _Response:
    def __init__(self, answers: dict) -> None:
        self.model = "jev-1.14.0"
        self.usage = _Usage()
        self.answers = {k: _Answer(v) for k, v in answers.items()}


class _Client:
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
        return _Response({k: self.answer(q.instructions) for k, q in questions.items()})


def _choice(likely: float) -> dict:
    rest = (1.0 - likely) / 2
    return {
        "type": "choice",
        "choice": "likely" if likely >= 0.5 else "doubtful",
        "confidence": 0.9,
        "probabilities": {"likely": likely, "doubtful": rest, "unrelated": rest},
    }


def _detector(answer, *, max_questions: int = 50) -> tuple[JevDetector, list]:
    calls = []
    d = JevDetector(
        key="k",
        max_questions=max_questions,
        client_factory=lambda *, model, api_key: _Client(answer, calls),
    )
    return d, calls


def _shapes(column: int, name: str, cells: list[str]) -> ColumnShapes:
    s = ColumnShapes(column=column, column_name=name)
    for c in cells:
        s.add(cell=c)
    return s


NAMES = _shapes(2, "full_name", ["Akua Mansa", "Omar Haddad", "Sara Lund", ""])
ADDRESSES = _shapes(
    3, "address", ["12 Main St, Springfield, IL 62704", "9 Oak St, Austin, TX 78701"]
)
STREETS = _shapes(4, "street", ["1234 Main St", "9 Oak St"])
EMPTY = _shapes(5, "spare", ["", ""])


def test_macie_jev_question_sends_shapes_only() -> None:
    q = JevDetector.question(
        shapes=NAMES, identifier="NAME", file="people.csv", columns=["id", "full_name"]
    )
    assert "Identifier: NAME (a person's full name" in q
    assert "Column: full_name." in q
    assert "Rows: 4; filled: 3; distinct: 3." in q
    assert "`Aaaa Aaaaa` (1)" in q
    assert q.endswith("Does this column hold people's full names?")
    for value in ("Akua", "Mansa", "Haddad"):
        assert value not in q


def test_macie_jev_question_bad_input() -> None:
    with pytest.raises(ValueError):
        JevDetector.question(shapes=NAMES, identifier="SSN", file="f", columns=[])
    with pytest.raises(TypeError):
        JevDetector.question(shapes=None, identifier="NAME", file="f", columns=[])


def test_macie_jev_plan_screens_addresses_and_empty_columns() -> None:
    d, _ = _detector(lambda q: _choice(0.9))
    ask, not_asked = d.plan(
        shapes=[NAMES, ADDRESSES, STREETS, EMPTY], identifiers=["NAME", "ADDRESS"]
    )
    assert [(i, s.column) for i, s in ask] == [
        ("NAME", 2),
        ("NAME", 3),
        ("NAME", 4),
        ("ADDRESS", 3),
    ]
    reasons = {(n["identifier"], n["column"]): n["reason"] for n in not_asked}
    assert reasons[("NAME", 5)] == "the column is empty"
    assert reasons[("ADDRESS", 4)] == JevDetector.NO_POSTCODE
    assert reasons[("ADDRESS", 2)] == JevDetector.NO_POSTCODE


def test_macie_jev_detect_uses_the_threshold() -> None:
    def answer(q: str) -> dict:
        if "Column: full_name." in q and "Identifier: NAME" in q:
            return _choice(0.95)
        if "Column: address." in q and "Identifier: ADDRESS" in q:
            return _choice(0.88)
        #
        # a near miss, as in the experiment: likely, but under 0.7
        #
        return _choice(0.61)

    d, calls = _detector(answer)
    result = d.detect(
        shapes=[NAMES, ADDRESSES],
        identifiers=["NAME", "ADDRESS"],
        file="people.csv",
        columns=["id", "full_name", "address"],
    )
    assert result["status"] == "complete"
    assert result["questions"] == 3
    assert len(calls) == 1
    found = [
        (c["identifier"], c["column"], c["count"])
        for c in result["columns"]
        if c["found"]
    ]
    assert found == [("NAME", 2, 3), ("ADDRESS", 3, 2)]
    near = [c for c in result["columns"] if not c["found"]]
    assert [(c["identifier"], c["column"], c["confidence"]) for c in near] == [
        ("NAME", 3, 0.61)
    ]
    assert near[0]["count"] == 0
    assert result["threshold"] == 0.7
    assert result["input_tokens"] == 250
    assert sorted(result["request"]["questions"]) == sorted(
        result["response"]["answers"]
    )


def test_macie_jev_detect_partial_past_max_questions() -> None:
    d, _ = _detector(lambda q: _choice(0.9), max_questions=1)
    result = d.detect(
        shapes=[NAMES, STREETS], identifiers=["NAME"], file="f", columns=[]
    )
    assert result["status"] == "partial"
    assert result["questions"] == 1
    assert result["not_asked"][-1]["reason"].startswith("past review_max_questions")


def test_macie_jev_detect_failure_is_a_status() -> None:
    d, _ = _detector(ConnectionError("no route to host"))
    result = d.detect(shapes=[NAMES], identifiers=["NAME"], file="f", columns=[])
    assert result["status"] == "failed"
    assert result["reason"] == "ConnectionError: no route to host"
    assert result["columns"] == []


def test_macie_jev_detect_nothing_to_ask() -> None:
    d, calls = _detector(lambda q: _choice(0.9))
    result = d.detect(shapes=[STREETS], identifiers=["ADDRESS"], file="f", columns=[])
    assert result["status"] == "complete"
    assert result["questions"] == 0
    assert calls == []


@pytest.mark.parametrize("threshold", [0, 1.5, "0.7", True])
def test_macie_jev_detect_bad_threshold(threshold) -> None:
    d, _ = _detector(lambda q: _choice(0.9))
    with pytest.raises(ValueError):
        d.detect(
            shapes=[NAMES],
            identifiers=["NAME"],
            file="f",
            columns=[],
            threshold=threshold,
        )


def test_macie_jev_detect_bad_identifier() -> None:
    d, _ = _detector(lambda q: _choice(0.9))
    with pytest.raises(ValueError):
        d.plan(shapes=[NAMES], identifiers=["PHONE_NUMBER"])
