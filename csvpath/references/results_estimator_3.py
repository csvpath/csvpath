import logging
import re

from .functions.function_3 import Function3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_3 import FunctionCall3, Star3
from .reference_estimate_3 import (
    EXACT,
    QUERY,
    RESOLVE,
    UPPER_BOUND,
    CostWeights,
    Read,
    ReferenceEstimate3,
)
from .sources.filesystem_reference_source import FilesystemReferenceSource
from .sources.sql_reference_source import SqlReferenceSource
from csvpath.util.nos import Nos

#
# The RESULTS cost estimate (references_v3_cost_estimates.md, approved by
# David 2026-11-17). It reads the archive ledger once -- one entry per
# instance, with its run_home, group and time -- and never lists or opens a
# manifest. From the ledger it counts the runs and instances in play, then
# applies the spec's read factors for what the reference does with them.
#
# First cut (David: "let's not worry about perfection"): pointers and index
# ranges narrow exactly; date windows and other ranges are not narrowed yet
# and are marked as upper bounds.
#
POINTERS = ("first", "last", "index")
INDEX_RANGES = ("from", "to")
WINDOWS = ("before", "after", "from", "to")
GROUPERS = ("all", "flatten", "groups")
WHOLE_FILE_ACCESSORS = {
    "errors": "errors_json",
    "vars": "vars_json",
    "meta": "meta_json",
    "data": "data_file",
    "unmatched": "data_file",
    "printouts": "data_file",
    "original": "data_file",
    "file": "data_file",
}
RECORD_SELECTORS = ("idchain", "message")
PATH_BUILDERS = ("regex", "choice", "name")


class ResultsEstimator3:
    def __init__(self, *, finder) -> None:
        if finder is None:
            raise ValueError("finder cannot be None")
        self.finder = finder
        self.csvpaths = finder.csvpaths
        self.reference = finder.ref.parsed
        self.reads = []
        self.why = []
        self.would_raise = None
        self.windowed = False

    #
    # entry point
    #
    def estimate(self) -> ReferenceEstimate3:
        archive = self.csvpaths.config.archive_path
        ledger = self._ledger(archive)
        self._read(QUERY, "ledger", 1, EXACT, "the archive ledger")
        runs = self._runs_by_group(ledger)
        groups = self._groups_in_play(runs)
        if len(groups) > 1:
            self.why.append(f"'{self.reference.root_major}' over {len(groups)} named-results groups")
        selected = {}
        for group in groups:
            in_path = self._runs_on_the_path(group=group, runs=runs[group], archive=archive)
            selected[group] = self._narrowed(in_path)
        self._name_one_costs(selected)
        self._name_three_costs(selected)
        if self.windowed:
            self._mark_upper_bounds()
        return ReferenceEstimate3(
            reference=str(self.finder.ref.reference),
            reads=self.reads,
            why=self.why,
            backend=Nos(archive).backend,
            weights=CostWeights.for_config(self.csvpaths.config),
            sql=self.csvpaths.config.references_sql == "on",
            would_raise=self.would_raise,
        )

    #
    # the ledger, read once and never written
    #
    def _ledger(self, archive: str) -> list:
        source = self.finder.source
        if isinstance(source, SqlReferenceSource):
            return source.results_ledger() or []
        return FilesystemReferenceSource.read_json(Nos(archive).join("manifest.json")) or []

    def _runs_by_group(self, ledger: list) -> dict:
        """{group: [run, ...]} in arrival order; a run is {home, time,
        identities}"""
        runs = {}
        for entry in ledger:
            group = entry.get("named_paths_name") or entry.get("named_results_name")
            home = entry.get("run_home")
            if group is None or home is None:
                continue
            by_home = runs.setdefault(group, {})
            run = by_home.setdefault(home, {"home": home, "time": entry.get("time"), "identities": []})
            run["identities"].append(entry.get("identity"))
        return {
            group: sorted(by_home.values(), key=lambda r: str(r["time"]))
            for group, by_home in runs.items()
        }

    def _groups_in_play(self, runs: dict) -> list:
        root = self.reference.root_major
        if isinstance(root, Star3):
            return sorted(runs)
        if isinstance(root, FunctionCall3):
            pattern = self.finder._build(root).pattern
            return sorted(g for g in runs if re.search(pattern, g))
        return [root] if root in runs else []

    #
    # name_one
    #
    def _calls(self) -> list:
        """name_one's selecting calls: function path segments (other than
        the path builders) and the trailing chain, in written order"""
        name_one = self.reference.name_one
        segments = [
            p for p in name_one.path if isinstance(p, FunctionCall3) and p.name not in PATH_BUILDERS
        ]
        return segments + list(name_one.functions)

    def _runs_on_the_path(self, *, group: str, runs: list, archive: str) -> list:
        name_one = self.reference.name_one
        path = [
            p
            for p in name_one.path
            if not (isinstance(p, FunctionCall3) and p.name not in PATH_BUILDERS)
        ]
        if not path or (len(path) == 1 and isinstance(path[0], Star3)):
            return runs
        if any(isinstance(p, FunctionCall3) and p.name in GROUPERS for p in name_one.path):
            self.why.append("the path's template levels are not narrowed in this estimate")
            return runs
        home = Nos(archive).join(group)
        try:
            pattern = self.finder._compile_path_pattern(
                path[:-1] if isinstance(path[-1], Star3) else path
            )
            run_slot = self.finder._pattern_is_run_slot(name_one=name_one, path=name_one.path)
            return [
                r
                for r in runs
                if self.finder._plain_path_matches(
                    run_home=r["home"], home=home, pattern=pattern, run_slot=run_slot
                )
            ]
        except Exception as e:
            # a shape this first cut does not narrow: every run, as a bound
            logging.getLogger(type(self).__name__).debug(f"path not narrowed: {e}")
            self.why.append(f"the path '{'/'.join(str(p) for p in path)}' is not narrowed in this estimate")
            return runs

    def _narrowed(self, runs: list) -> list:
        """runs after name_one's pointers and index ranges, per group"""
        calls = self._calls()
        names = [c.name for c in calls]
        lower = next((c for c in calls if c.name == "from" and isinstance(c.arg, int)), None)
        upper = next((c for c in calls if c.name == "to" and isinstance(c.arg, int)), None)
        if lower or upper:
            start = lower.arg if lower else 0
            stop = (upper.arg + 1 if upper.arg >= 0 else len(runs) + upper.arg + 1) if upper else None
            runs = runs[start:stop]
        if "last" in names:
            runs = runs[-1:]
        elif "first" in names:
            runs = runs[:1]
        elif "index" in names:
            index = next(c.arg for c in calls if c.name == "index")
            runs = [runs[index]] if isinstance(index, int) and -len(runs) <= index < len(runs) else []
        return runs

    def _name_one_costs(self, selected: dict) -> None:
        calls = self._calls()
        runs = sum(len(r) for r in selected.values())
        if self.reference.name_three is None and not any(
            c.name in ("manifest", "having") for c in calls
        ):
            # a run result reads its run's manifest
            self._read(QUERY, "run_manifest", runs, EXACT, "a run result")
        for call in calls:
            cls = ReferenceFunctionFactory.get_registered_class(call.name)
            if cls is None:
                continue
            if cls.SOURCE == "clock" or (call.name in WINDOWS and not isinstance(call.arg, int)):
                self.why.append(f":{call.name}() is a time window, not narrowed in this estimate")
                self.windowed = True
            elif call.name == "having":
                self._having_costs(call, selected)
            elif cls.ROLE == Function3.VALUE and cls.SOURCE == "manifest" and call.arg is not None:
                self._read(QUERY, "run_manifest", runs, EXACT, f":{call.name}(...)")
                self.why.append(f":{call.name}(...) reads each candidate run's manifest")
        if self.reference.name_three is None:
            value = [
                c
                for c in calls
                if (cls := ReferenceFunctionFactory.get_registered_class(c.name))
                and cls.ROLE == Function3.VALUE
                and cls.SOURCE == "manifest"
                and c.arg is None
            ]
            if value:
                self._read(RESOLVE, "run_manifest", runs, EXACT, f":{value[-1].name}()")

    def _having_costs(self, call, selected: dict) -> None:
        listings = sum(len(r) for r in selected.values())
        instances = sum(len(run["identities"]) for r in selected.values() for run in r)
        self._read(QUERY, "run_listing", listings, UPPER_BOUND, ":having()")
        self._read(QUERY, "instance_manifest", instances, EXACT, ":having()")
        content = call.arg if isinstance(call.arg, FunctionCall3) else None
        if content is not None and content.name in WHOLE_FILE_ACCESSORS:
            self._read(
                QUERY,
                WHOLE_FILE_ACCESSORS[content.name],
                instances,
                UPPER_BOUND,
                f":having(:{content.name}(...))",
            )
            self.why.append(
                f":having() by content reads candidates' {content.name} files during"
                " query; it stops at a run's first match, so this is the most"
            )

    #
    # name_three
    #
    def _name_three_costs(self, selected: dict) -> None:
        three = self.reference.name_three
        if three is None:
            return
        runs = [run for r in selected.values() for run in r]
        if not any(read.because == ":having()" for read in self.reads):
            self._read(QUERY, "run_listing", len(runs), UPPER_BOUND, f".{three}")
            self._read(
                QUERY,
                "instance_manifest",
                sum(len(run["identities"]) for run in runs),
                EXACT,
                f".{three}",
            )
            self.why.append(
                f"'.{three}' lists each run and reads each of its instance manifests"
            )
        picked = self._instances_picked(three, runs)
        names = [c.name for c in three.functions]
        accessor = next((n for n in names if n in WHOLE_FILE_ACCESSORS), None)
        if accessor is not None:
            call = next(c for c in three.functions if c.name == accessor)
            selects_records = any(n in RECORD_SELECTORS for n in names) or isinstance(
                call.arg, FunctionCall3
            )
            if picked > 1 and not selects_records:
                self.would_raise = (
                    f"resolve: {picked} whole {accessor} files at once (compendium"
                    " 5.3); resolve from one of query()'s results, or select records"
                )
            self._read(RESOLVE, WHOLE_FILE_ACCESSORS[accessor], picked, EXACT, f":{accessor}()")
            self.why.append(f":{accessor}() reads one file per instance at resolve")
            return
        value = [
            c
            for c in three.functions
            if (cls := ReferenceFunctionFactory.get_registered_class(c.name))
            and cls.ROLE == Function3.VALUE
            and cls.SOURCE == "manifest"
            and c.arg is None
        ]
        if value:
            self._read(RESOLVE, "instance_manifest", picked, EXACT, f":{value[-1].name}()")

    def _instances_picked(self, three, runs: list) -> int:
        names = [c.name for c in three.functions]
        if any(n in POINTERS for n in names):
            return len(runs)
        body = three.body
        if body is not None and not isinstance(body, Star3):
            return sum(1 for run in runs if str(body) in run["identities"])
        return sum(len(run["identities"]) for run in runs)

    #
    # bookkeeping
    #
    def _read(self, part: str, kind: str, count: int, basis: str, because: str) -> None:
        if count:
            self.reads.append(Read(part=part, kind=kind, count=count, basis=basis, because=because))

    def _mark_upper_bounds(self) -> None:
        """an unnarrowed window keeps every run, so each count beyond the
        ledger is at most this"""
        self.reads = [
            Read(part=r.part, kind=r.kind, count=r.count, basis=UPPER_BOUND, because=r.because)
            if r.basis == EXACT and r.kind != "ledger"
            else r
            for r in self.reads
        ]
