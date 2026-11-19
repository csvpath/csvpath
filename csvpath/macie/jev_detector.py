import time

from .column_shapes import ColumnShapes
from .jev_reviewer import JevReviewer


class JevDetector(JevReviewer):
    """asks Jev whether columns hold NAME or ADDRESS data, which Macie finds
    with machine learning and rules cannot
    (specs/macie/jev-names-addresses-design.md). One choice() question per
    column and identifier, from the column's shapes in the case-keeping
    mask, its header and the file's other headers: no value and no word is
    sent.

    These results are ours, not Macie's, and are kept apart from the
    Macie-shaped findings (David, 2026-11-19). A column is found when
    P(likely) is at least the threshold, 0.7 from the experiment
    (specs/macie/jev-names-experiment-2026-11-18.md); every filled cell in
    it is then counted. An ADDRESS question is asked only of columns whose
    shapes hold a postal code.

    Like the review, a check that cannot be done is a status, failed, with
    the reason: NAME and ADDRESS are then not checked, and the run stays
    valid."""

    IDENTIFIERS = {
        "NAME": (
            "a person's full name: a given name and a family name",
            "Does this column hold people's full names?",
        ),
        "ADDRESS": (
            "a postal address that includes a city or place and its postal code",
            "Does this column hold postal addresses?",
        ),
    }
    THRESHOLD = 0.7
    NO_POSTCODE = "no postal code in the column's shapes"
    STATE = """\
A data-loss-prevention scan is checking CSV columns for personal data.
Values are masked: each upper-case letter is A, each lower-case letter
is a, each digit is #; spaces and punctuation are kept. You see each
column's shapes, never its values. For each column you are told the
file, the column and the other columns in the file, how many rows are
filled and distinct, and the most common shapes with their counts."""
    CHOICES = {
        "likely": "the column very probably holds the kind of personal data named",
        "doubtful": "the column probably does not hold that kind of personal data",
        "unrelated": "the column clearly holds something else",
    }

    @classmethod
    def question(  # pylint: disable=W0221
        cls, *, shapes: ColumnShapes, identifier: str, file: str, columns: list[str]
    ) -> str:
        if not isinstance(shapes, ColumnShapes):
            raise TypeError(f"shapes must be ColumnShapes, not {type(shapes)}")
        if identifier not in cls.IDENTIFIERS:
            raise ValueError(
                f"identifier must be one of {sorted(cls.IDENTIFIERS)}, not {identifier!r}"
            )
        if not isinstance(file, str):
            raise TypeError(f"file must be a str, not {type(file)}")
        if not isinstance(columns, list):
            raise TypeError(f"columns must be a list, not {type(columns)}")
        meaning, ask = cls.IDENTIFIERS[identifier]
        listed = ", ".join(f"`{s}` ({n})" for s, n in shapes.top())
        distinct = (
            f"at least {shapes.distinct}"
            if shapes.distinct_capped
            else f"{shapes.distinct}"
        )
        name = shapes.column_name if shapes.column_name else f"column {shapes.column}"
        return (
            f"Identifier: {identifier} ({meaning}).\n"
            f"File: {file}. Column: {name}. "
            f"Columns in the file: {', '.join(f'{c}' for c in columns)}.\n"
            f"Rows: {shapes.rows}; filled: {shapes.filled}; distinct: {distinct}.\n"
            f"Most common shapes: {listed}.\n"
            f"{ask}"
        )

    def plan(
        self, *, shapes: list[ColumnShapes], identifiers: list[str]
    ) -> tuple[list[tuple[str, ColumnShapes]], list[dict]]:
        """the (identifier, column) pairs to ask, and those not asked with
        why: an empty column, no postal code, or past max_questions"""
        if not isinstance(shapes, list) or not all(
            isinstance(s, ColumnShapes) for s in shapes
        ):
            raise TypeError("shapes must be a list of ColumnShapes")
        unknown = [i for i in identifiers if i not in self.IDENTIFIERS]
        if unknown:
            raise ValueError(f"No Jev check for {unknown}")
        ask, not_asked = [], []
        for identifier in identifiers:
            for s in shapes:
                reason = None
                if s.filled == 0:
                    reason = "the column is empty"
                elif identifier == "ADDRESS" and not s.may_hold_postcodes():
                    reason = self.NO_POSTCODE
                if reason is None:
                    ask.append((identifier, s))
                else:
                    not_asked.append(
                        self._column(identifier=identifier, shapes=s, reason=reason)
                    )
        for identifier, s in ask[self.max_questions :]:
            not_asked.append(
                self._column(
                    identifier=identifier,
                    shapes=s,
                    reason=f"past review_max_questions ({self.max_questions})",
                )
            )
        return ask[: self.max_questions], not_asked

    @classmethod
    def _column(cls, *, identifier: str, shapes: ColumnShapes, reason: str) -> dict:
        return {
            "identifier": identifier,
            "column": shapes.column,
            "columnName": shapes.column_name,
            "reason": reason,
        }

    def detect(
        self,
        *,
        shapes: list[ColumnShapes],
        identifiers: list[str],
        file: str,
        columns: list[str],
        threshold: float = THRESHOLD,
    ) -> dict:
        """one request for the file"""
        if (
            not isinstance(threshold, (int, float))
            or isinstance(threshold, bool)
            or not 0 < threshold <= 1
        ):
            raise ValueError(f"threshold must be in (0, 1], not {threshold!r}")
        ask, not_asked = self.plan(shapes=shapes, identifiers=identifiers)
        result = {
            "status": self.COMPLETE,
            "reason": None,
            "model": self.model,
            "threshold": threshold,
            "questions": len(ask),
            "input_tokens": None,
            "output_tokens": None,
            "seconds": None,
            "columns": [],
            "not_asked": not_asked,
            "request": None,
            "response": None,
        }
        if any(n["reason"].startswith("past review_max_questions") for n in not_asked):
            result["status"] = self.PARTIAL
            result["reason"] = "some columns were not asked: review_max_questions"
        if not ask:
            return result
        questions = {
            f"q{i + 1}": self.question(
                shapes=s, identifier=identifier, file=file, columns=columns
            )
            for i, (identifier, s) in enumerate(ask)
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
            result["columns"] = [
                self._answered(
                    identifier=identifier,
                    shapes=s,
                    answer=answers.get(k),
                    qid=k,
                    threshold=threshold,
                )
                for k, (identifier, s) in zip(questions, ask)
            ]
        except Exception as e:
            #
            # not a failed run: NAME and ADDRESS are reported as not checked
            #
            self.logger().exception("Jev NAME and ADDRESS check failed: %s", e)
            result["status"] = self.FAILED
            result["reason"] = f"{type(e).__name__}: {e}"
            result["columns"] = []
        return result

    def _answered(
        self,
        *,
        identifier: str,
        shapes: ColumnShapes,
        answer,
        qid: str,
        threshold: float,
    ) -> dict:
        if not isinstance(answer, dict) or answer.get("type") != "choice":
            raise ValueError(f"Jev gave no choice answer to {qid}: {answer!r}")
        verdict = answer.get("choice")
        if verdict not in self.CHOICES:
            raise ValueError(f"Jev answered {qid} with an unknown choice {verdict!r}")
        probabilities = answer.get("probabilities") or {}
        likely = probabilities.get("likely")
        if not isinstance(likely, (int, float)) or isinstance(likely, bool):
            raise ValueError(f"Jev gave no probability of likely for {qid}")
        found = float(likely) >= threshold
        return {
            "identifier": identifier,
            "column": shapes.column,
            "columnName": shapes.column_name,
            "found": found,
            "count": shapes.filled if found else 0,
            "verdict": verdict,
            "confidence": round(float(likely), 3),
            "probabilities": {k: round(float(v), 3) for k, v in probabilities.items()},
            "facts": shapes.to_dict(),
        }
