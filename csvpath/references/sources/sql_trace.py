import time
from contextlib import contextmanager
from dataclasses import dataclass, field

from csvpath.util.config_exception import ConfigurationException


@dataclass(frozen=True)
class SqlStatement:
    """one SQL read a reference made: the statement as the engine's
    dialect gets it, its bound parameters, the rows it returned and how
    long it took."""

    reference: str | None
    phase: str | None
    sql: str
    params: dict
    rows: int
    ms: float

    def line(self) -> str:
        return (
            f"{self.reference} {self.phase}: {self.sql} | {self.params} | "
            f"{self.rows} rows | {self.ms:.1f} ms"
        )


@dataclass
class SqlTrace:
    """the SQL the v3 references ran while a capture was open, for seeing
    how simple or complex the SQL behind a reference is. It only records
    when [references] sql is on or shadow; with sql off no SQL runs and
    the trace stays empty. See SqlTracing.capture()."""

    statements: list = field(default_factory=list)

    def add(self, statement: SqlStatement) -> None:
        if not isinstance(statement, SqlStatement):
            raise TypeError("statement must be a SqlStatement")
        self.statements.append(statement)

    @property
    def repeats(self) -> int:
        """statements that ran again with the same SQL and parameters"""
        seen = set()
        repeats = 0
        for s in self.statements:
            key = (s.sql, tuple(sorted(s.params.items())))
            if key in seen:
                repeats += 1
            seen.add(key)
        return repeats

    def summary(self) -> str:
        if not self.statements:
            return "no SQL ran ([references] sql is off, or nothing was read)"
        distinct = len({s.sql for s in self.statements})
        rows = sum(s.rows for s in self.statements)
        ms = sum(s.ms for s in self.statements)
        return (
            f"{len(self.statements)} statements, {distinct} distinct, "
            f"{self.repeats} repeats, {rows} rows, {ms:.1f} ms"
        )

    def to_dicts(self) -> list[dict]:
        return [s.__dict__.copy() for s in self.statements]


class SqlTracing:
    """the trace state of one SqlReferenceSource: the reference and phase
    being read for (set by the finders), the open captures, and the
    [references] sql_trace logging switch, which is looked up on every
    statement so it can be turned on and off while a process runs
    (csvpaths.config.add_to_config(), or an ini edit and config.reload()).

    Only the reference source's own reads are recorded: it is not a
    listener on the engine, which the SQL listeners' writes and other
    CsvPaths on the thread share (issue #774)."""

    ON = ("on", "yes", "true")
    OFF = ("off", "no", "false", "")

    def __init__(self, *, csvpaths) -> None:
        if csvpaths is None:
            raise ValueError("csvpaths cannot be None")
        self._csvpaths = csvpaths
        self._captures: list[SqlTrace] = []
        self.reference: str | None = None
        self.phase: str | None = None
        # the current reference's statements, for the log's total line
        self.current = SqlTrace()

    def set_context(self, *, reference: str, phase: str) -> None:
        """the reference and phase the next reads are for. A query starts a
        new total."""
        if not phase:
            raise ValueError("phase cannot be None or empty")
        if phase == "query" or reference != self.reference:
            self.current = SqlTrace()
        self.reference = reference
        self.phase = phase

    @contextmanager
    def capture(self):
        """every statement read while the block runs, from any finder over
        this source (an expression's sides included)."""
        trace = SqlTrace()
        self._captures.append(trace)
        try:
            yield trace
        finally:
            self._captures.remove(trace)

    def logging_on(self) -> bool:
        """[references] sql_trace, read on every call (not cached)"""
        v = self._csvpaths.config.get(section="references", name="sql_trace")
        v = "" if v is None else str(v).strip().lower()
        if v in self.ON:
            return True
        if v in self.OFF:
            return False
        raise ConfigurationException(
            f"[references] sql_trace must be on or off, not {v!r}"
        )

    @property
    def active(self) -> bool:
        return bool(self._captures) or self.logging_on()

    def record(self, *, sql: str, params: dict, rows: int, started: float) -> None:
        """one statement read. `started` is time.perf_counter() before it
        ran."""
        statement = SqlStatement(
            reference=self.reference,
            phase=self.phase,
            sql=" ".join(str(sql).split()),
            params=dict(params or {}),
            rows=rows,
            ms=(time.perf_counter() - started) * 1000,
        )
        for trace in self._captures:
            trace.add(statement)
        self.current.add(statement)
        if self.logging_on():
            self._csvpaths.logger.info("SQL trace: %s", statement.line())

    def log_total(self) -> None:
        """the current reference's total, when logging is on. It ends the
        reference: the next total starts from zero, and a read outside a
        finder is not tagged with the last reference (reviewer on #775)."""
        if self.current.statements and self.logging_on():
            self._csvpaths.logger.info(
                "SQL trace: %s total: %s", self.reference, self.current.summary()
            )
        self.current = SqlTrace()
        self.reference = None
        self.phase = None
