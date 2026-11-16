import logging
import re
import time

from .column_facts import ColumnFacts


class JevReviewer:
    """asks Jev about a file's findings, one choice() question per
    identifier and column, and maps the answers to review entries
    (specs/macie/jev-review-build.md). Jev is told masked context only,
    the ColumnFacts; it never sees a value.

    The review annotates. It never changes a count, severity or cell, and
    a review that cannot be done is a status, "failed", with the reason:
    the findings are complete either way (David, 2026-11-15).

    The client comes from client_factory(model=, api_key=), a context
    manager with system_one(state=, questions=), so tests pass a fake.
    The default is the Jev SDK's TypeSafeClient."""

    #
    # the model the experiments ran on; jev-latest moves, so it is pinned
    #
    MODEL = "jev-1.14.0"
    MAX_QUESTIONS = 50
    TIMEOUT = 30.0
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    STATE = """\
A data-loss-prevention scan of a CSV file flagged values that may be
sensitive personal or financial data. You are reviewing the flags.
Values are masked: in every word that holds a digit, each letter is A
and each digit is #, with punctuation kept, so you see each value's
shape, never the value. Other words are shown as written. For each
flagged column you are told the file, the column and its neighbouring
columns, facts the scan computed about the flagged values, why the scan
flagged them, and masked samples of the cell text."""
    CHOICES = {
        "likely": "the flagged values are very probably real sensitive data of the kind named",
        "doubtful": "the flagged values are probably not that kind of sensitive data",
        "unrelated": "the flag is clearly a false alarm, e.g. ids, codes, or placeholders",
    }

    def __init__(
        self,
        *,
        key: str,
        model: str = MODEL,
        max_questions: int = MAX_QUESTIONS,
        client_factory=None,
    ) -> None:
        if not isinstance(key, str) or key.strip() == "":
            raise ValueError("key must be a non-empty str")
        if not isinstance(model, str) or model.strip() == "":
            raise ValueError("model must be a non-empty str")
        if model.strip() == "jev-latest":
            raise ValueError("model must be pinned, not jev-latest")
        if (
            not isinstance(max_questions, int)
            or isinstance(max_questions, bool)
            or max_questions < 1
        ):
            raise ValueError(
                f"max_questions must be a positive int, not {max_questions!r}"
            )
        if client_factory is not None and not callable(client_factory):
            raise TypeError("client_factory must be callable")
        self.key = key
        self.model = model.strip()
        self.max_questions = max_questions
        self.client_factory = client_factory or self._sdk_client

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def _sdk_client(cls, *, model: str, api_key: str):
        #
        # imported here so that a run without a review never loads the SDK
        #
        from typesafe_sdk import TypeSafeClient

        return TypeSafeClient(model=model, api_key=api_key, timeout=cls.TIMEOUT)

    @classmethod
    def meaning(cls, *, identifier: str) -> str:
        """USA_SOCIAL_SECURITY_NUMBER -> usa social security number;
        EmployeeId -> employee id"""
        if not isinstance(identifier, str) or identifier.strip() == "":
            raise ValueError("identifier must be a non-empty str")
        spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", identifier)
        return re.sub(r"[_\s]+", " ", spaced).strip().lower()

    @classmethod
    def question(
        cls, *, facts: ColumnFacts, file: str, columns: list[str], rows: int
    ) -> str:
        if not isinstance(facts, ColumnFacts):
            raise TypeError(f"facts must be ColumnFacts, not {type(facts)}")
        if not isinstance(file, str):
            raise TypeError(f"file must be a str, not {type(file)}")
        if not isinstance(columns, list):
            raise TypeError(f"columns must be a list, not {type(columns)}")
        if not isinstance(rows, int) or isinstance(rows, bool) or rows < 0:
            raise ValueError(f"rows must be a non-negative int, not {rows!r}")
        meaning = cls.meaning(identifier=facts.identifier)
        lines = [
            f"Identifier: {facts.identifier} ({meaning}).",
            f"File: {file}. Columns: {', '.join(f'{c}' for c in columns)}.",
            f"Flagged column: {facts.column_name} (column {facts.column}).",
            f"Flagged in {facts.cells} of {rows} rows; "
            f"{facts.distinct} distinct flagged values.",
        ]
        computed = facts.facts()
        if computed:
            lines.append("Facts the scan computed about the flagged values:")
            lines.extend(f"  - {f}" for f in computed)
        if facts.why:
            lines.append(f"Why the scan flagged them: {facts.why}.")
        lines.append("Masked samples of flagged cells:")
        lines.extend(f'  "{s}"' for s in facts.samples)
        lines.append(
            f"Is it likely that the flagged values in the {facts.column_name} "
            f"column are real: {meaning}?"
        )
        return "\n".join(lines)

    def review(
        self, *, facts: list[ColumnFacts], file: str, columns: list[str], rows: int
    ) -> dict:
        """one request for the file. The first max_questions items are asked;
        the rest are listed as not reviewed"""
        if not isinstance(facts, list) or not all(
            isinstance(f, ColumnFacts) for f in facts
        ):
            raise TypeError("facts must be a list of ColumnFacts")
        asked, skipped = facts[: self.max_questions], facts[self.max_questions :]
        result = {
            "status": self.COMPLETE if not skipped else self.PARTIAL,
            "reason": None,
            "model": self.model,
            "questions": len(asked),
            "input_tokens": None,
            "output_tokens": None,
            "seconds": None,
            "entries": [],
            "not_reviewed": [
                {
                    "identifier": f.identifier,
                    "column": f.column,
                    "columnName": f.column_name,
                }
                for f in skipped
            ],
            "request": None,
            "response": None,
        }
        if skipped:
            result["reason"] = (
                f"{len(skipped)} not reviewed: review_max_questions is {self.max_questions}"
            )
        if not asked:
            return result
        questions = {
            f"q{i + 1}": self.question(facts=f, file=file, columns=columns, rows=rows)
            for i, f in enumerate(asked)
        }
        result["request"] = {
            "state": self.STATE,
            "choices": self.CHOICES,
            "questions": questions,
        }
        try:
            from typesafe_sdk import Choice

            started = time.perf_counter()
            with self.client_factory(model=self.model, api_key=self.key) as client:
                response = client.system_one(
                    state=self.STATE,
                    questions={
                        k: Choice(instructions=v, criteria=self.CHOICES)
                        for k, v in questions.items()
                    },
                )
            result["seconds"] = round(time.perf_counter() - started, 2)
            answers = {k: a.model_dump() for k, a in response.answers.items()}
            result["response"] = {"model": response.model, "answers": answers}
            result["model"] = response.model
            result["input_tokens"] = response.usage.input_tokens
            result["output_tokens"] = response.usage.output_tokens
            result["entries"] = [
                self._entry(facts=f, answer=answers.get(k), qid=k)
                for k, f in zip(questions, asked)
            ]
        except Exception as e:
            #
            # the findings stand without the review: a status, loudly
            # reported by the caller, not a failed run
            #
            self.logger().exception("Jev review failed: %s", e)
            result["status"] = self.FAILED
            result["reason"] = f"{type(e).__name__}: {e}"
            result["entries"] = []
        return result

    def _entry(self, *, facts: ColumnFacts, answer, qid: str) -> dict:
        if not isinstance(answer, dict) or answer.get("type") != "choice":
            raise ValueError(f"Jev gave no choice answer to {qid}: {answer!r}")
        verdict = answer.get("choice")
        if verdict not in self.CHOICES:
            raise ValueError(f"Jev answered {qid} with an unknown choice {verdict!r}")
        probabilities = answer.get("probabilities") or {}
        likely = probabilities.get("likely")
        if not isinstance(likely, (int, float)) or isinstance(likely, bool):
            raise ValueError(f"Jev gave no probability of likely for {qid}")
        return {
            "identifier": facts.identifier,
            "column": facts.column,
            "columnName": facts.column_name,
            "verdict": verdict,
            "confidence": round(float(likely), 3),
            "probabilities": {k: round(float(v), 3) for k, v in probabilities.items()},
            "facts": facts.facts(),
        }
