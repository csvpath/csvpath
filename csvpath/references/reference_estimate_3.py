import logging
import math
from dataclasses import dataclass, asdict

#
# What a reference's query() and resolve() will probably read, as a score and
# its parts (specs/references_v3/spec/references_v3_cost_estimates.md,
# approved by David 2026-11-17). This module holds the result types, the
# score and the weights; the finders build the reads.
#

QUERY = "query"
RESOLVE = "resolve"
PARTS = (QUERY, RESOLVE)

EXACT = "exact"
UPPER_BOUND = "upper_bound"
ESTIMATE = "estimate"
BASES = (EXACT, UPPER_BOUND, ESTIMATE)

LISTING_KINDS = ("name_listing", "run_listing")
SQL_KINDS = ("sql_query",)
FILE_KINDS = (
    "ledger",
    "named_file_manifest",
    "group_manifest",
    "run_manifest",
    "instance_manifest",
    "definition",
    "errors_json",
    "vars_json",
    "meta_json",
    "version_file",
    "data_file",
    "readme",
    "log",
)
KINDS = FILE_KINDS + LISTING_KINDS + SQL_KINDS


@dataclass(frozen=True)
class Read:
    """reads of one kind that a part of a reference makes"""

    part: str
    kind: str
    count: int
    basis: str
    because: str

    def __post_init__(self) -> None:
        if self.part not in PARTS:
            raise ValueError(f"part must be one of {PARTS}, not {self.part!r}")
        if self.kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}, not {self.kind!r}")
        if not isinstance(self.count, int) or isinstance(self.count, bool) or self.count < 0:
            raise ValueError(f"count must be an int >= 0, not {self.count!r}")
        if self.basis not in BASES:
            raise ValueError(f"basis must be one of {BASES}, not {self.basis!r}")
        if not isinstance(self.because, str) or self.because.strip() == "":
            raise ValueError("because must name the part of the reference")


class CostWeights:
    """weight per read, by backend: a file read and a listing. Under
    [references] sql = on, ledger, manifest and listing reads are SQL queries;
    content files keep their backend's weight. The defaults are honest
    guesses, not measurements. [references] cost_weights overrides them, e.g.
    `s3:10:20, sftp:5:5, sql:2` (backend:read:listing, or sql:query)."""

    DEFAULTS = {
        "local": (1, 1),
        "sftp": (5, 5),
        "s3": (10, 20),
        "azure": (10, 20),
        "gcs": (10, 20),
    }
    SQL_QUERY = 2
    SQL_SERVED = (
        "ledger",
        "named_file_manifest",
        "group_manifest",
        "run_manifest",
        "instance_manifest",
    ) + LISTING_KINDS

    def __init__(self, *, overrides: str | None = None) -> None:
        self.backends = dict(self.DEFAULTS)
        self.sql_query = self.SQL_QUERY
        if overrides is not None and str(overrides).strip() != "":
            self._apply(str(overrides))

    @classmethod
    def for_config(cls, config) -> "CostWeights":
        if config is None:
            raise ValueError("config cannot be None")
        return cls(overrides=config.get(section="references", name="cost_weights"))

    def _apply(self, overrides: str) -> None:
        for item in overrides.split(","):
            parts = [p.strip() for p in item.strip().split(":")]
            if parts == [""]:
                continue
            try:
                if parts[0] == "sql" and len(parts) == 2:
                    self.sql_query = self._number(parts[1])
                elif len(parts) == 3:
                    self.backends[parts[0]] = (
                        self._number(parts[1]),
                        self._number(parts[2]),
                    )
                else:
                    raise ValueError("expected backend:read:listing or sql:query")
            except ValueError as e:
                msg = f"[references] cost_weights cannot use {item.strip()!r}: {e}"
                logging.getLogger(type(self).__name__).error(msg)
                raise ValueError(msg) from e

    @staticmethod
    def _number(text: str) -> float:
        value = float(text)
        if value < 0:
            raise ValueError("a weight cannot be negative")
        return value

    def weight(self, *, kind: str, backend: str, sql: bool = False) -> float:
        """the weight of one read of `kind` on `backend`"""
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}, not {kind!r}")
        if kind == "sql_query" or (sql and kind in self.SQL_SERVED):
            return self.sql_query
        if backend not in self.backends:
            raise ValueError(f"no cost weights for backend {backend!r}")
        read, listing = self.backends[backend]
        return listing if kind in LISTING_KINDS else read

    def to_dict(self) -> dict:
        return {
            "backends": {b: {"read": r, "listing": li} for b, (r, li) in self.backends.items()},
            "sql_query": self.sql_query,
        }


class ReferenceEstimate3:
    """the estimate for one reference: scores, reads, reasons"""

    MAX_SCORE = 10
    SCORE_1_UP_TO = 10
    STEP = 4

    def __init__(
        self,
        *,
        reference: str,
        reads: list,
        why: list,
        backend: str,
        weights: CostWeights,
        sql: bool = False,
        would_raise: str | None = None,
    ) -> None:
        if not reference:
            raise ValueError("reference cannot be None or empty")
        if reads is None or why is None:
            raise ValueError("reads and why cannot be None")
        if any(not isinstance(r, Read) for r in reads):
            raise TypeError("reads must be Read records")
        if weights is None:
            raise ValueError("weights cannot be None")
        weights.weight(kind="ledger", backend=backend)  # an unknown backend raises
        self.reference = reference
        self.reads = list(reads)
        self.why = list(why)
        self.backend = backend
        self.weights = weights
        self.sql = sql
        self.would_raise = would_raise

    @classmethod
    def score_for(cls, weighted: float) -> int:
        """the 1..MAX_SCORE bucket of a weighted read total: 1 is up to 10,
        and each step up is x4"""
        if weighted is None or weighted < 0:
            raise ValueError("weighted reads must be >= 0")
        if weighted <= cls.SCORE_1_UP_TO:
            return 1
        steps = math.ceil(math.log(weighted / cls.SCORE_1_UP_TO, cls.STEP))
        return min(cls.MAX_SCORE, 1 + steps)

    def weighted(self, part: str | None = None) -> float:
        """weighted reads for one part, or for both when part is None"""
        if part is not None and part not in PARTS:
            raise ValueError(f"part must be one of {PARTS} or None")
        return sum(
            r.count * self.weights.weight(kind=r.kind, backend=self.backend, sql=self.sql)
            for r in self.reads
            if part is None or r.part == part
        )

    @property
    def query_score(self) -> int:
        return self.score_for(self.weighted(QUERY))

    @property
    def resolve_score(self) -> int:
        return self.score_for(self.weighted(RESOLVE))

    @property
    def score(self) -> int:
        # resolve() runs query() first, so a resolving caller pays both
        # (David, 2026-11-17)
        return self.score_for(self.weighted())

    def reads_for(self, part: str) -> dict:
        """{kind: count} for one part"""
        if part not in PARTS:
            raise ValueError(f"part must be one of {PARTS}")
        out = {}
        for r in self.reads:
            if r.part == part:
                out[r.kind] = out.get(r.kind, 0) + r.count
        return out

    @property
    def query_reads(self) -> dict:
        return self.reads_for(QUERY)

    @property
    def resolve_reads(self) -> dict:
        return self.reads_for(RESOLVE)

    @property
    def estimated(self) -> list:
        """the reads that are not exact counts, as text"""
        return [
            f"{r.kind} x{r.count} ({r.basis.replace('_', ' ')}, {r.because})"
            for r in self.reads
            if r.basis != EXACT
        ]

    def to_dict(self) -> dict:
        return {
            "reference": self.reference,
            "score": self.score,
            "query_score": self.query_score,
            "resolve_score": self.resolve_score,
            "max_score": self.MAX_SCORE,
            "would_raise": self.would_raise,
            "backend": self.backend,
            "sql": self.sql,
            "weighted": {
                QUERY: self.weighted(QUERY),
                RESOLVE: self.weighted(RESOLVE),
            },
            "reads": [asdict(r) for r in self.reads],
            "why": list(self.why),
            "weights": self.weights.to_dict(),
        }

    @staticmethod
    def _describe(reads: dict) -> str:
        if not reads:
            return "0"
        return " + ".join(f"{count} {kind}" for kind, count in reads.items())

    def summary(self) -> str:
        lines = [self.reference]
        if self.would_raise:
            lines.append(f"  would raise: {self.would_raise}")
        lines.append(
            f"  score {self.score} (of {self.MAX_SCORE})   query {self.query_score}"
            f"   resolve {self.resolve_score}   [{self.backend}"
            f"{', sql' if self.sql else ''}]"
        )
        lines.append(f"  query:   {self._describe(self.query_reads)}")
        lines.append(f"  resolve: {self._describe(self.resolve_reads)}")
        for i, line in enumerate(self.why):
            lines.append(f"  {'why:' if i == 0 else '    '}     {line}")
        for line in self.estimated:
            lines.append(f"  estimated: {line}")
        return "\n".join(lines)


class ExpressionEstimate3:
    """an expression's estimate: one per side, each complete on its own
    (David's note: "a reference expression results in two fully separate
    estimates")"""

    def __init__(self, *, expression: str, left, right) -> None:
        if not expression:
            raise ValueError("expression cannot be None or empty")
        for side in (left, right):
            if not isinstance(side, (ReferenceEstimate3, ExpressionEstimate3)):
                raise TypeError("a side must be a ReferenceEstimate3 or ExpressionEstimate3")
        self.expression = expression
        self.left = left
        self.right = right

    def to_dict(self) -> dict:
        return {
            "expression": self.expression,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }

    def summary(self) -> str:
        indent = lambda text: "\n".join("    " + line for line in text.splitlines())  # noqa: E731
        return "\n".join(
            [
                self.expression,
                "  left:",
                indent(self.left.summary()),
                "  right:",
                indent(self.right.summary()),
            ]
        )
