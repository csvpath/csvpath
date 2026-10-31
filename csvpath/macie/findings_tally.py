from .arn_utility import ArnUtility as arut
from .severity_levels import SeverityLevels


class IdentifierTally:
    """counts one identifier's occurrences in one file and keeps the first
    few locations. Counting never stops, so count and severity stay exact
    even after detail reporting stops at max_detail."""

    #
    # Macie keeps the locations of 1-15 occurrences per detection
    #
    MAX_CELLS = 15

    def __init__(
        self,
        *,
        name: str,
        severity: SeverityLevels,
        max_detail: int,
        arn: str | None = None,
        category: str | None = None,
    ) -> None:
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError("name must be a non-empty str")
        if not isinstance(severity, SeverityLevels):
            raise TypeError(f"severity must be SeverityLevels, not {type(severity)}")
        if (
            not isinstance(max_detail, int)
            or isinstance(max_detail, bool)
            or max_detail < 0
        ):
            raise ValueError(
                f"max_detail must be a non-negative int, not {max_detail!r}"
            )
        if arn is not None:
            arut.check(arn=arn)
        self.name = name
        self.severity = severity
        self.max_detail = max_detail
        self.arn = arn
        #
        # None for a custom identifier; a Macie category for a managed one
        #
        self.category = category
        self.count = 0
        self.detailed = 0
        self.cells = []

    def record(self, *, row: int, column: int, column_name: str) -> bool:
        """records one occurrence. True if it should get detail reporting."""
        for n, v in [("row", row), ("column", column)]:
            if not isinstance(v, int) or isinstance(v, bool) or v < 1:
                raise ValueError(f"{n} must be a positive int, not {v!r}")
        if not isinstance(column_name, str):
            raise TypeError(f"column_name must be a str, not {type(column_name)}")
        self.count += 1
        if len(self.cells) < self.MAX_CELLS:
            self.cells.append(
                {
                    "cellReference": None,
                    "column": column,
                    "columnName": column_name,
                    "row": row,
                }
            )
        if self.detailed < self.max_detail:
            self.detailed += 1
            return True
        return False

    def severity_now(self) -> str | None:
        return self.severity.severity(count=self.count)

    def to_detection(self) -> dict:
        d = {}
        if self.category is None:
            d["arn"] = self.arn
            d["name"] = self.name
        else:
            d["type"] = self.name
        d["count"] = self.count
        d["severity"] = self.severity_now()
        d["occurrences"] = {"cells": list(self.cells)}
        return d


class FindingsTally:
    """all identifiers' tallies for one file, and the global breaker. The
    breaker trips when the total reaches max_findings."""

    def __init__(
        self, *, max_findings: int, max_detail: int, source_arn: str | None = None
    ) -> None:
        for n, v in [("max_findings", max_findings), ("max_detail", max_detail)]:
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                raise ValueError(f"{n} must be a non-negative int, not {v!r}")
        if max_findings == 0:
            raise ValueError("max_findings must be at least 1")
        self.max_findings = max_findings
        self.max_detail = max_detail
        #
        # the Macie job or sensitivity inspection template the rules came
        # from. None for a handcrafted wrapper.
        #
        if source_arn is not None:
            arut.check(arn=source_arn)
        self.source_arn = source_arn
        self.tallies: dict[str, IdentifierTally] = {}
        self.total = 0
        self.stopped_at_line = None

    def add(self, *, tally: IdentifierTally) -> None:
        if not isinstance(tally, IdentifierTally):
            raise TypeError(f"tally must be an IdentifierTally, not {type(tally)}")
        if tally.name in self.tallies:
            raise ValueError(f"Identifier {tally.name} added twice")
        self.tallies[tally.name] = tally

    def record(self, *, name: str, row: int, column: int, column_name: str) -> bool:
        if name not in self.tallies:
            raise ValueError(f"No identifier named {name!r}")
        if self.tripped:
            raise ValueError(
                "The breaker has tripped: no more occurrences can be recorded"
            )
        detail = self.tallies[name].record(
            row=row, column=column, column_name=column_name
        )
        self.total += 1
        return detail

    @property
    def tripped(self) -> bool:
        return self.total >= self.max_findings

    def to_findings(self) -> dict:
        custom = [
            t for t in self.tallies.values() if t.category is None and t.count > 0
        ]
        managed = [
            t for t in self.tallies.values() if t.category is not None and t.count > 0
        ]
        categories = {}
        for t in managed:
            categories.setdefault(t.category, []).append(t)
        return {
            "customDataIdentifiers": {
                "detections": [t.to_detection() for t in custom],
                "totalCount": sum(t.count for t in custom),
            },
            "sensitiveData": [
                {
                    "category": category,
                    "detections": [t.to_detection() for t in ts],
                    "totalCount": sum(t.count for t in ts),
                }
                for category, ts in categories.items()
            ],
            "csvpath": {
                "source_arn": self.source_arn,
                "stopped": self.tripped,
                "stopped_at_line": self.stopped_at_line,
                "max_findings": self.max_findings,
                "max_detail": self.max_detail,
            },
        }

    @classmethod
    def detail_message(
        cls, *, name: str, occurrence: int, line: int, column: int, column_name: str
    ) -> str:
        #
        # line is CsvPath's 0-based physical line; Macie's row is line + 1.
        # the occurrence number keeps two occurrences in one cell distinct;
        # the error manager drops an error identical to an earlier one.
        #
        return (
            f"macie {name}: occurrence {occurrence}, line {line} (row {line + 1}), "
            f"column {column} {column_name}"
        )

    def summary_messages(self) -> list[str]:
        messages = []
        for t in self.tallies.values():
            noun = "occurrence" if t.count == 1 else "occurrences"
            severity = t.severity_now() or f"none (below {t.severity.levels[0][0]})"
            if t.count == 0:
                shown = "no detail"
            elif t.detailed < t.count:
                shown = f"detail shown for first {t.detailed}"
            else:
                shown = f"detail shown for all {t.count}"
            messages.append(
                f"macie {t.name}: {t.count} {noun}, severity {severity}, {shown}"
            )
        if self.tripped:
            messages.append(
                f"macie: stopped at line {self.stopped_at_line} after {self.total} "
                f"occurrences (max {self.max_findings}); results are partial and "
                f"severities are at least as shown"
            )
        return messages
