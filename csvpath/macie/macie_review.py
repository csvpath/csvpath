import json
import logging
import os

from csvpath.util.nos import Nos

from .column_facts import ColumnFacts
from .column_shapes import ColumnShapes
from .jev_detector import JevDetector
from .jev_reviewer import JevReviewer
from .run_inputs import RunInputs
from .util.keyword_utility import KeywordUtility as keut


class MacieReview:
    """one run's Jev review (specs/macie/jev-review-build.md): which
    identifiers are reviewed, the ColumnFacts collected while the file is
    scanned, and, at report time, the review itself, its printouts, its
    entries in macie_findings, and its record in the run dir.

    Off unless config.ini [macie] review names identifiers:

        [macie]
        review = USA_SOCIAL_SECURITY_NUMBER, CREDIT_CARD_NUMBER
        review_model = jev-1.14.0
        review_max_questions = 50
        review_threshold = 0.7

    with the Jev key in [jev] key, as for the CVL jev() function.

    NAME and ADDRESS in review are not a review of findings: they turn on
    the Jev check for those identifiers (JevDetector), whose results are
    kept apart from the Macie-shaped findings, in a jev section."""

    RECORD = "review"
    JEV_RECORD = "jev"
    NOT_NAMED = "config.ini [macie] review does not name it"
    OFF = "off"
    #
    # tests set a fake client factory here; None is the SDK's client
    #
    CLIENT_FACTORY = None

    def __init__(self, *, config) -> None:
        self.identifiers = self._identifiers(config=config)
        self.config = config
        self.facts: dict[tuple[str, int], ColumnFacts] = {}

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @property
    def on(self) -> bool:
        """a review of findings: an identifier other than NAME and ADDRESS
        is named"""
        return len(self.identifiers - set(JevDetector.IDENTIFIERS)) > 0

    @classmethod
    def _identifiers(cls, *, config) -> set[str]:
        if config is None:
            return set()
        v = config.get(section="macie", name="review", default=None)
        if v is None:
            return set()
        if isinstance(v, list):
            names = [f"{n}".strip() for n in v]
        else:
            names = [n.strip() for n in f"{v}".split(",")]
        names = [n for n in names if n != ""]
        if "all" in [n.lower() for n in names]:
            #
            # not in the first build (David, 2026-11-15): reviewing is a
            # choice made per identifier
            #
            raise ValueError(
                "config.ini [macie] review must name identifiers; all is not supported"
            )
        return set(names)

    def reviews(self, *, name: str) -> bool:
        return name in self.identifiers

    def checks(self, *, name: str) -> bool:
        """True if the Jev check of NAME or ADDRESS is on for name"""
        return name in JevDetector.IDENTIFIERS and name in self.identifiers

    def collect(
        self, *, identifier, column: int, header: str, cell: str, occurrences: int
    ) -> None:
        """one flagged cell of a reviewed identifier"""
        key = (identifier.name, column)
        facts = self.facts.get(key)
        if facts is None:
            facts = ColumnFacts(
                identifier=identifier.name,
                column=column,
                column_name=header,
                why=self.why(identifier=identifier, header=header),
            )
            self.facts[key] = facts
        facts.add(cell=cell, occurrences=occurrences)

    @classmethod
    def why(cls, *, identifier, header: str) -> str:
        """why the scan flagged a column's cells, in words. Per column, from
        the header: a keyword in the header covers every cell"""
        variants = getattr(identifier, "variants", None) or []
        mode = getattr(identifier, "keyword_mode", "required")
        if (
            variants
            and mode != "absent"
            and keut.in_header(header=header, variants=variants)
        ):
            return "the column header holds a keyword"
        if not variants or mode == "none":
            return "the identifier needs no keyword"
        if mode == "absent":
            return "no keyword is near the value, as this identifier requires"
        return "a keyword is near the value in the cell, or the value needs none"

    def run(self, *, csvpath) -> dict:
        """reviews the facts collected; never raises for a review that cannot
        be done: that is status failed, with the reason"""
        facts = sorted(self.facts.values(), key=lambda f: (f.identifier, f.column))
        if not facts:
            #
            # nothing reviewed was found: nothing to ask, and no key needed
            #
            result = self._failed(reason=None, facts=[])
            result["status"] = JevReviewer.COMPLETE
            return result
        problem = self._key_problem()
        if problem is not None:
            return self._failed(reason=problem, facts=facts)
        try:
            reviewer = JevReviewer(
                key=self.config.get(section="jev", name="key"),
                model=self._model(),
                max_questions=self._max_questions(),
                #
                # read through the class: a function set on the class and
                # read through self would be bound to self
                #
                client_factory=type(self).CLIENT_FACTORY,
            )
        except (TypeError, ValueError) as e:
            self.logger().exception("Cannot set up the Jev review: %s", e)
            return self._failed(reason=f"{e}", facts=facts)
        return reviewer.review(
            facts=facts,
            file=self._file(csvpath=csvpath),
            columns=[f"{h}" for h in (csvpath.headers or [])],
            rows=self._rows(csvpath=csvpath),
        )

    def _key_problem(self) -> str | None:
        #
        # the CVL jev() function's check; imported here so a run without a
        # review never loads the SDK
        #
        from csvpath.matching.functions.jev.jev import Jev

        return Jev.key_problem(config=self.config)

    def _model(self) -> str:
        v = self.config.get(section="macie", name="review_model", default=None)
        return JevReviewer.MODEL if v is None else f"{v}".strip()

    def _threshold(self) -> float:
        v = self.config.get(section="macie", name="review_threshold", default=None)
        if v is None:
            return JevDetector.THRESHOLD
        try:
            f = float(f"{v}".strip())
        except ValueError as e:
            raise ValueError(
                f"config.ini [macie] review_threshold must be a number, not {v!r}"
            ) from e
        if not 0 < f <= 1:
            raise ValueError(
                f"config.ini [macie] review_threshold must be in (0, 1], not {f}"
            )
        return f

    def detect(
        self, *, csvpath, shapes: list[ColumnShapes], identifiers: list[str]
    ) -> dict:
        """the Jev check for the NAME and ADDRESS identifiers the csvpath
        holds. Each is checked only if [macie] review names it. Never raises
        for a check that cannot be done: that is status failed, with the
        reason, and the identifiers are not checked"""
        asked = [i for i in identifiers if i in self.identifiers]
        not_checked = [
            {"identifier": i, "reason": self.NOT_NAMED}
            for i in identifiers
            if i not in self.identifiers
        ]
        if not asked:
            result = self._jev_failed(reason=None, not_checked=not_checked)
            result["status"] = self.OFF
            return result
        problem = self._key_problem()
        if problem is not None:
            return self._jev_failed(
                reason=problem, not_checked=not_checked, asked=asked
            )
        try:
            detector = JevDetector(
                key=self.config.get(section="jev", name="key"),
                model=self._model(),
                max_questions=self._max_questions(),
                client_factory=type(self).CLIENT_FACTORY,
            )
            threshold = self._threshold()
        except (TypeError, ValueError) as e:
            self.logger().exception("Cannot set up the Jev check: %s", e)
            return self._jev_failed(reason=f"{e}", not_checked=not_checked, asked=asked)
        result = detector.detect(
            shapes=shapes,
            identifiers=asked,
            file=self._file(csvpath=csvpath),
            columns=[f"{h}" for h in (csvpath.headers or [])],
            threshold=threshold,
        )
        if result["status"] == JevReviewer.FAILED:
            not_checked += [
                {"identifier": i, "reason": result["reason"]} for i in asked
            ]
        result["not_checked"] = not_checked
        return result

    @classmethod
    def _jev_failed(
        cls, *, reason: str | None, not_checked: list[dict], asked: list[str] = ()
    ) -> dict:
        return {
            "status": JevReviewer.FAILED,
            "reason": reason,
            "model": None,
            "threshold": None,
            "questions": 0,
            "input_tokens": None,
            "output_tokens": None,
            "seconds": None,
            "columns": [],
            "not_asked": [],
            "not_checked": list(not_checked)
            + [{"identifier": i, "reason": reason} for i in asked],
            "request": None,
            "response": None,
        }

    @classmethod
    def attach_jev(cls, *, findings: dict, result: dict) -> dict:
        """adds the Jev check to macie_findings as its own jev section, kept
        apart from the Macie-shaped sensitiveData: these are a model's
        judgments of columns, not Macie's rules (David, 2026-11-19)"""
        detections = {}
        for c in result["columns"]:
            if not c["found"]:
                continue
            d = detections.setdefault(
                c["identifier"], {"type": c["identifier"], "count": 0, "columns": []}
            )
            d["count"] += c["count"]
            d["columns"].append(
                {
                    "column": c["column"],
                    "columnName": c["columnName"],
                    "count": c["count"],
                    "verdict": c["verdict"],
                    "confidence": c["confidence"],
                }
            )
        findings["jev"] = {
            "detectedBy": "jev",
            "status": result["status"],
            "reason": result["reason"],
            "model": result["model"],
            "threshold": result["threshold"],
            "questions": result["questions"],
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "seconds": result["seconds"],
            "totalCount": sum(d["count"] for d in detections.values()),
            "detections": list(detections.values()),
            "not_checked": result.get("not_checked", []),
            "not_asked": result["not_asked"],
        }
        return findings

    @classmethod
    def jev_printouts(cls, *, result: dict) -> list[str]:
        lines = []
        for c in result["columns"]:
            if c["found"]:
                lines.append(
                    f"macie jev {c['identifier']} column {c['column']} "
                    f"{c['columnName']}: {c['count']} cells "
                    f"({c['verdict']}, {c['confidence']})"
                )
        names = sorted({n["identifier"] for n in result.get("not_checked", [])})
        if result["status"] == JevReviewer.FAILED:
            lines.append(
                f"macie jev: {', '.join(names)} not checked: {result['reason']}"
            )
        elif result["status"] == cls.OFF:
            lines.append(f"macie jev: {', '.join(names)} not checked: {cls.NOT_NAMED}")
        else:
            tokens = (
                f", {result['input_tokens']} tokens in, {result['output_tokens']} out"
                if result["input_tokens"] is not None
                else ""
            )
            found = sum(1 for c in result["columns"] if c["found"])
            lines.append(
                f"macie jev: {result['status']}, {result['questions']} questions, "
                f"{found} columns found at {result['threshold']}, "
                f"{result['model']}{tokens}"
            )
            if names:
                lines.append(
                    f"macie jev: {', '.join(names)} not checked: {cls.NOT_NAMED}"
                )
            if result["status"] == JevReviewer.PARTIAL:
                lines.append(f"macie jev: {result['reason']}")
        return lines

    def _max_questions(self) -> int:
        v = self.config.get(section="macie", name="review_max_questions", default=None)
        if v is None:
            return JevReviewer.MAX_QUESTIONS
        try:
            return int(f"{v}".strip())
        except ValueError as e:
            raise ValueError(
                f"config.ini [macie] review_max_questions must be an int, not {v!r}"
            ) from e

    @classmethod
    def _file(cls, *, csvpath) -> str:
        #
        # in a group run the scanner reads the stored copy, whose name is
        # a content hash: the named-file name is what the file is known by
        #
        named = getattr(csvpath, "named_file_name", None)
        if isinstance(named, str) and named.strip() != "":
            return named.strip()
        scanner = getattr(csvpath, "scanner", None)
        name = getattr(scanner, "filename", None) if scanner else None
        return os.path.basename(f"{name}") if name else "unknown"

    @classmethod
    def _rows(cls, *, csvpath) -> int:
        lm = csvpath.line_monitor
        for v in (lm.data_line_count, lm.data_line_number):
            if isinstance(v, int) and v >= 0:
                return v
        return 0

    @classmethod
    def _failed(cls, *, reason: str | None, facts: list[ColumnFacts]) -> dict:
        return {
            "status": JevReviewer.FAILED,
            "reason": reason,
            "model": None,
            "questions": 0,
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
                for f in facts
            ],
            "request": None,
            "response": None,
        }

    @classmethod
    def attach(cls, *, findings: dict, result: dict) -> dict:
        """adds the review to macie_findings: a review list inside each
        reviewed detection, and the summary in the csvpath section. Every
        count, severity and cell stays as it was"""
        by_identifier = {}
        for e in result["entries"]:
            entry = {k: v for k, v in e.items() if k != "identifier"}
            by_identifier.setdefault(e["identifier"], []).append(entry)
        detections = list(findings["customDataIdentifiers"]["detections"])
        for category in findings["sensitiveData"]:
            detections.extend(category["detections"])
        for d in detections:
            name = d.get("name") or d.get("type")
            if name in by_identifier:
                d["review"] = by_identifier[name]
        findings["csvpath"]["review"] = {
            k: result[k]
            for k in (
                "status",
                "reason",
                "model",
                "questions",
                "input_tokens",
                "output_tokens",
                "seconds",
                "not_reviewed",
            )
        }
        return findings

    @classmethod
    def printouts(cls, *, result: dict) -> list[str]:
        lines = []
        for e in result["entries"]:
            facts = "; " + "; ".join(e["facts"]) if e["facts"] else ""
            lines.append(
                f"macie review {e['identifier']} column {e['column']} "
                f"{e['columnName']}: {e['verdict']} ({e['confidence']}){facts}"
            )
        if result["status"] == JevReviewer.FAILED:
            lines.append(f"macie review: failed: {result['reason']}")
        elif result["questions"] == 0 and not result["not_reviewed"]:
            lines.append("macie review: nothing to review")
        else:
            tokens = (
                f", {result['input_tokens']} tokens in, {result['output_tokens']} out"
                if result["input_tokens"] is not None
                else ""
            )
            seconds = (
                f", {result['seconds']} s" if result["seconds"] is not None else ""
            )
            lines.append(
                f"macie review: {result['status']}, {result['questions']} questions, "
                f"{result['model']}{seconds}{tokens}"
            )
            if result["status"] == JevReviewer.PARTIAL:
                lines.append(f"macie review: {result['reason']}")
        return lines

    @classmethod
    def record(cls, *, csvpath, result: dict, kind: str = RECORD) -> str | None:
        """writes the request and response to the run's
        _extra_data/macie/<kind>.<csvpath>.json in a group run: review for
        the review, jev for the NAME and ADDRESS check. None, and nothing
        written, outside one"""
        if kind not in (cls.RECORD, cls.JEV_RECORD):
            raise ValueError(f"kind must be review or jev, not {kind!r}")
        if csvpath.csvpaths is None or csvpath.named_paths_name is None:
            return None
        if csvpath.run_dir is None:
            return None
        target = RunInputs.macie_dir(run_dir=csvpath.run_dir)
        name = f"{csvpath.identity or 'csvpath'}"
        path = Nos(target).join(f"{kind}.{name}.json")
        RunInputs.write(path=path, text=json.dumps(result, indent=2) + "\n")
        return path
