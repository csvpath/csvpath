import logging
import re

from .functions.function_3 import Function3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_3 import FunctionCall3, Star3
from .reference_estimate_3 import (
    ESTIMATE,
    EXACT,
    QUERY,
    RESOLVE,
    UPPER_BOUND,
    CostWeights,
    Read,
    ReferenceEstimate3,
)
from .reference_exceptions_3 import ReferenceException3
from .sources.filesystem_reference_source import FilesystemReferenceSource
from .sources.sql_reference_source import SqlReferenceSource
from csvpath.util.nos import Nos

#
# The RESULTS cost estimate (references_v3_cost_estimates.md, approved by
# David 2026-11-17). It reads the archive ledger once -- one entry per
# instance, with its run_home, group and time -- and never lists or opens a
# manifest. From the ledger it counts the runs and instances in play, then
# applies the read factors the RESULTS finder really has (measured against
# tests/references/cost/read_counter.py on the corpus):
#
# - compendium 6.28 order: a range applies first, then the gates and
#   :having(), then a pointer picks;
# - ranges and pointers apply per group, except after :flatten(), which
#   pools the runs;
# - a name_one gate reads each candidate run's manifest once, however many
#   gates; what comes after a gate (or :having(), or an unnarrowed time
#   window) is an upper bound, since the survivors are unknown;
# - :having() lists each candidate run and reads its instance manifests,
#   and a name_three after it lists the runs again;
# - any name_three lists each picked run and reads all its instance
#   manifests; a content accessor reads one file per picked instance at
#   resolve, and a value field rereads the picked instance manifests;
# - several whole files at once raise at resolve (compendium 5.3) before
#   anything is read.
#
# The estimator uses the RESULTS finder's own path matching (_build,
# _compile_path_pattern, _pattern_is_run_slot, _plain_path_matches) so its
# notion of "the runs on this path" cannot drift from query()'s. That is a
# deliberate coupling to private methods, kept in one place (_on_the_path).
#
POINTERS = ("first", "last", "index")
WINDOWS = ("before", "after", "from", "to")
GROUPERS = ("all", "flatten", "groups")
PATH_BUILDERS = ("regex", "choice", "name")
WHOLE_FILES = {
    "errors": "errors_json",
    "vars": "vars_json",
    "meta": "meta_json",
    "data": "data_file",
    "unmatched": "data_file",
    "printouts": "data_file",
    "original": "data_file",
    "file": "data_file",
}
# data files may not exist for an instance, so their counts are bounds
OPTIONAL_FILES = ("data", "unmatched", "printouts", "original", "file")
RECORD_SELECTORS = ("idchain", "message")
NAMED_FILES = {
    "errors.json": "errors_json",
    "vars.json": "vars_json",
    "meta.json": "meta_json",
    "manifest.json": "instance_manifest",
}


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
        self.uncertain = False
        self.windowed = False

    #
    # entry point
    #
    def estimate(self) -> ReferenceEstimate3:
        archive = self.csvpaths.config.archive_path
        problem = self._query_would_raise()
        if problem is not None:
            # query() raises somewhere along the way: what it would read up
            # to there is at most the normal query estimate, and resolve
            # never runs
            if self.finder._bare_log_call(self.reference) is None:
                self._estimate_runs(archive)
            self.reads = [
                Read(part=r.part, kind=r.kind, count=r.count, basis=UPPER_BOUND, because=r.because)
                for r in self.reads
                if r.part == QUERY
            ]
            self.would_raise = f"query: {problem}"
        elif self.finder._bare_log_call(self.reference) is not None:
            self._read(part=RESOLVE, kind="log", count=1, basis=EXACT, because=":log()")
            self.why.append(":log() reads the log file at resolve")
        elif self._is_bare_manifest_set():
            self._read(part=RESOLVE, kind="ledger", count=1, basis=EXACT, because=":manifest()")
            self.why.append("the whole :manifest() set is the ledger, read at resolve")
        else:
            self._estimate_runs(archive)
            if self.windowed:
                # an unnarrowed window may leave fewer runs than every count
                # beyond the ledger assumes
                self.reads = [
                    Read(part=r.part, kind=r.kind, count=r.count, basis=UPPER_BOUND, because=r.because)
                    if r.basis == EXACT and r.kind != "ledger"
                    else r
                    for r in self.reads
                ]
        return ReferenceEstimate3(
            reference=str(self.finder.ref.reference),
            reads=self.reads,
            why=self.why,
            backend=Nos(archive).backend,
            weights=CostWeights.for_config(self.csvpaths.config),
            sql=self.csvpaths.config.references_sql == "on",
            would_raise=self.would_raise,
        )

    def _query_would_raise(self) -> "str | None":
        """the static checks query() makes that this estimate can see"""
        try:
            # a foreign function, then two value-supplying functions, raise
            # first, as in query(); they read nothing
            self.finder._check_datatype_functions(self.reference)
            self.finder._check_wildcards(self.reference)
            self.finder._check_one_value(self.reference)
        except ReferenceException3 as e:
            return str(e)
        name_one = self.reference.name_one
        built = [p for p in name_one.path if isinstance(p, FunctionCall3)]
        built += list(name_one.functions)
        if self.reference.name_three is not None:
            built += list(self.reference.name_three.functions)
        for call in built:
            try:
                # builds and checks the arguments (e.g. ':month(13)',
                # ':hour(6)'), as query() does first; it reads nothing
                self.finder._build(call)
            except ReferenceException3 as e:
                return str(e)
        if self.finder._bare_log_call(self.reference) is not None:
            if not isinstance(self.reference.root_major, Star3):
                return ":log() requires root_major '*'"
            return None
        calls = self._calls()
        three = self.reference.name_three
        if any(c.name == "log" for c in calls):
            return ":log() must be standalone"
        bare_window = any(
            (cls := ReferenceFunctionFactory.get_registered_class(c.name)) is not None
            and cls.SOURCE == "clock"
            for c in calls
        )
        index_range = any(c.name in ("from", "to") and isinstance(c.arg, int) for c in calls)
        if bare_window and index_range:
            return "a bare time window cannot be combined with an index range"
        for call in calls + (list(three.functions) if three else []):
            if call.name != "having" or not isinstance(call.arg, FunctionCall3):
                continue
            if call.arg.name != "errors":
                return f":having() cannot take :{call.arg.name}() as content (compendium 6.39)"
            if call.arg.arg is None:
                return ":having(:errors()) does not say what the errors must have"
        if three is not None:
            names = [c.name for c in three.functions]
            for call in three.functions:
                if call.name == "having" and not isinstance(call.arg, FunctionCall3):
                    return ":having() by identity is not a name_three function"
                if call.name == "message":
                    return ":message() is not a name_three function; use :errors(:message(...))"
                if call.name == "file" and call.arg is None:
                    return ":file() needs a file name"
            if any(n in RECORD_SELECTORS for n in names) and not any(
                n in WHOLE_FILES for n in names
            ):
                return f":{next(n for n in names if n in RECORD_SELECTORS)}() needs :errors()"
        return None

    def _estimate_runs(self, archive: str) -> None:
        ledger = self._ledger(archive)
        self._read(part=QUERY, kind="ledger", count=1, basis=EXACT, because="the archive ledger")
        runs = self._runs_by_group(ledger)
        groups = self._groups_in_play(runs)
        if len(groups) > 1:
            self.why.append(
                f"'{self.reference.root_major}' over {len(groups)} named-results groups"
            )
        calls = self._calls()
        names = [c.name for c in calls]
        gates = [c for c in calls if self._is_gate(c)]
        having = [c for c in calls if c.name == "having"]
        windows = [c for c in calls if self._is_window(c)]
        if windows:
            self.uncertain = True
            self.windowed = True
            self.why.append(
                f":{windows[0].name}() is a time window, not narrowed in this estimate"
            )
        manifest = "manifest" in names
        set_root = not isinstance(self.reference.root_major, str)
        if manifest and set_root and not self._path_groupers():
            self._manifest_set_costs(groups=groups, runs=runs, gates=gates, names=names)
            return
        pools = self._pools(groups=groups, runs=runs, archive=archive)
        candidates = [self._ranged(pool, calls) for pool in pools]
        if gates or having:
            self.uncertain = True
        picked = [self._pointed(pool, calls) for pool in candidates]
        if set(self._path_function_names()) & {"all", "groups"} and picked != candidates:
            # a pointer after ':all()'/':groups()' picks one run per template
            # group, and the groups are not narrowed here: up to every
            # candidate. It counted one per named-results name, so
            # 'customers/:all()/*:last()' estimated 1 run manifest and read
            # 2 (name_one gap review, 2026-11-21).
            picked = candidates
            self.uncertain = True
            self.why.append("a pointer after a grouping wildcard picks one run per group")
        n_candidates = sum(len(p) for p in candidates)
        n_picked = sum(len(p) for p in picked)
        if gates:
            basis = ESTIMATE if "groups" in self._path_function_names() else EXACT
            self._read(
                part=QUERY,
                kind="run_manifest",
                count=n_candidates,
                basis=basis,
                because=f":{gates[0].name}(...)",
            )
            for gate in gates[1:]:
                # each further gate rereads its candidates' run manifests
                self._read(
                    part=QUERY,
                    kind="run_manifest",
                    count=n_candidates,
                    basis=UPPER_BOUND,
                    because=f":{gate.name}(...)",
                )
            self.why.append(f":{gates[0].name}(...) reads each candidate run's manifest")
        if having:
            self._having_costs(
                call=having[0],
                runs=[r for p in candidates for r in p],
                n_picked=n_picked,
            )
        three = self.reference.name_three
        if three is None:
            self._run_result_costs(
                n_picked=n_picked, manifest=manifest, gated=bool(gates), having=bool(having)
            )
            return
        self._name_three_costs(
            three=three,
            runs=[r for p in picked for r in p],
            relisted=bool(having),
        )

    #
    # the ledger, read once and never written
    #
    def _ledger(self, archive: str) -> list:
        source = self.finder.source
        if isinstance(source, SqlReferenceSource):
            return source.results_ledger() or []
        return (
            FilesystemReferenceSource.read_json(
                path=Nos(archive).join("manifest.json"),
                logger=getattr(self.finder.csvpaths, "logger", None),
            )
            or []
        )

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
            run = by_home.setdefault(
                home, {"home": home, "time": entry.get("time"), "identities": []}
            )
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
    def _path_function_names(self) -> list:
        return [p.name for p in self.reference.name_one.path if isinstance(p, FunctionCall3)]

    def _path_groupers(self) -> list:
        return [n for n in self._path_function_names() if n in GROUPERS]

    def _calls(self) -> list:
        """name_one's selecting calls: function path segments (other than
        the path builders) and the trailing chain, in written order"""
        name_one = self.reference.name_one
        segments = [
            p
            for p in name_one.path
            if isinstance(p, FunctionCall3) and p.name not in PATH_BUILDERS
        ]
        return segments + list(name_one.functions)

    @staticmethod
    def _is_gate(call) -> bool:
        cls = ReferenceFunctionFactory.get_registered_class(call.name)
        return (
            cls is not None
            and cls.ROLE == Function3.VALUE
            and cls.SOURCE == "manifest"
            and call.arg is not None
            and call.name != "manifest"
        )

    @staticmethod
    def _is_window(call) -> bool:
        cls = ReferenceFunctionFactory.get_registered_class(call.name)
        if cls is None:
            return False
        return cls.SOURCE == "clock" or (
            call.name in WINDOWS and not isinstance(call.arg, int)
        )

    def _is_bare_manifest_set(self) -> bool:
        """'$*.results.:manifest()' (or a ':regex()'/':choice()' root): the
        whole set, read from the ledger at resolve and not at query"""
        if isinstance(self.reference.root_major, str) or self.reference.name_three is not None:
            return False
        return self.finder._is_bare_pointer_reference(self.reference, "manifest")

    def _pools(self, *, groups: list, runs: dict, archive: str) -> list:
        """the runs on name_one's path, per group, or pooled across the
        groups after :flatten()"""
        per_group = [
            self._on_the_path(group=g, runs=runs[g], archive=archive) for g in groups
        ]
        if "flatten" in self._path_function_names():
            pooled = [r for pool in per_group for r in pool]
            return [sorted(pooled, key=lambda r: str(r["time"]))]
        return per_group

    def _on_the_path(self, *, group: str, runs: list, archive: str) -> list:
        name_one = self.reference.name_one
        path = [
            p
            for p in name_one.path
            if not (isinstance(p, FunctionCall3) and p.name not in PATH_BUILDERS)
        ]
        if not path or (len(path) == 1 and isinstance(path[0], Star3)):
            if "groups" in self._path_function_names():
                self.uncertain = True
            return runs
        if self._path_groupers():
            self.uncertain = True
            self.why.append("the path's template levels are not narrowed in this estimate")
            return runs
        home = Nos(archive).join(group)
        try:
            pattern = self.finder._compile_path_pattern(
                path[:-1] if isinstance(path[-1], Star3) else path
            )
            run_slot = self.finder._pattern_is_run_slot(
                name_one=name_one, path=name_one.path
            )
        except ReferenceException3 as e:
            logging.getLogger(type(self).__name__).warning(
                "path not narrowed in this estimate: %s", e
            )
            self.uncertain = True
            self.why.append("the path is not narrowed in this estimate")
            return runs
        return [
            r
            for r in runs
            if self.finder._plain_path_matches(
                run_home=r["home"], home=home, pattern=pattern, run_slot=run_slot
            )
        ]

    @staticmethod
    def _ranged(runs: list, calls: list) -> list:
        lower = next((c for c in calls if c.name == "from" and isinstance(c.arg, int)), None)
        upper = next((c for c in calls if c.name == "to" and isinstance(c.arg, int)), None)
        if not (lower or upper):
            return runs
        start = lower.arg if lower else 0
        if upper is None:
            stop = None
        elif upper.arg >= 0:
            stop = upper.arg + 1
        else:
            stop = len(runs) + upper.arg + 1
        return runs[start:stop]

    @staticmethod
    def _pointed(runs: list, calls: list) -> list:
        names = [c.name for c in calls]
        if "last" in names:
            return runs[-1:]
        if "first" in names:
            return runs[:1]
        index = next((c.arg for c in calls if c.name == "index"), None)
        if isinstance(index, int):
            return [runs[index]] if -len(runs) <= index < len(runs) else []
        return runs

    #
    # read factors
    #
    def _manifest_set_costs(self, *, groups: list, runs: dict, gates: list, names: list) -> None:
        """a ':manifest()' set form under a '*', ':regex()' or ':choice()'
        root, with a pointer, range or gate: the ledger, and each run's
        manifest for a gate"""
        all_runs = sum(len(runs[g]) for g in groups)
        if gates:
            self._read(
                part=QUERY,
                kind="run_manifest",
                count=all_runs,
                basis=UPPER_BOUND,
                because=f":{gates[0].name}(...)",
            )
        calls = self._calls()
        ranged = [c for c in calls if c.name in ("from", "to")]
        records = 1
        if ranged:
            # the set is one pool in arrival order, and a range rereads the
            # ledger for each record it selects
            pooled = sorted((r for g in groups for r in runs[g]), key=lambda r: str(r["time"]))
            records = len(self._ranged(pooled, calls)) or 1
        fields = self._value_fields(calls)
        if fields:
            self._read(
                part=RESOLVE,
                kind="run_manifest",
                count=records,
                basis=UPPER_BOUND,
                because=f":{fields[-1].name}()",
            )
        self._read(part=RESOLVE, kind="ledger", count=records, basis=UPPER_BOUND, because=":manifest()")
        self.why.append(":manifest() selects records from the ledger set")

    def _run_result_costs(self, *, n_picked: int, manifest: bool, gated: bool, having: bool) -> None:
        fields = self._value_fields(self._calls())
        if (gated or having) and (fields or manifest):
            # the survivors' value or manifest, read at resolve
            self._read(
                part=RESOLVE,
                kind="run_manifest",
                count=n_picked,
                basis=UPPER_BOUND,
                because=f":{(fields[-1].name if fields else 'manifest')}()",
            )
        if having:
            # :having() already read each candidate's manifest
            return
        if gated and manifest and not fields and n_picked > 1:
            self._raise_or_warn(
                message=f"resolve: up to {n_picked} whole run manifests at once (compendium 5.3)",
                definite=False,
            )
        if gated:
            # the gate read each candidate's manifest; the survivors' run
            # results are read again, and how many survive is unknown
            self._read(
                part=QUERY,
                kind="run_manifest",
                count=n_picked,
                basis=UPPER_BOUND,
                because="the gate's survivors",
            )
            return
        basis = UPPER_BOUND if self.uncertain else EXACT
        self._read(part=QUERY, kind="run_manifest", count=n_picked, basis=basis, because="a run result")
        if not manifest:
            if fields:
                self._read(
                    part=RESOLVE,
                    kind="run_manifest",
                    count=n_picked,
                    basis=basis,
                    because=f":{fields[-1].name}()",
                )
            return
        if n_picked > 1 and not fields:
            self._raise_or_warn(
                message=f"resolve: {n_picked} whole run manifests at once (compendium 5.3)",
                definite=not self.uncertain,
            )
            if not self.uncertain:
                return
        self._read(part=RESOLVE, kind="run_manifest", count=n_picked, basis=basis, because=":manifest()")

    def _having_costs(self, *, call, runs: list, n_picked: int) -> None:
        instances = sum(len(r["identities"]) for r in runs)
        self._read(part=QUERY, kind="run_listing", count=len(runs), basis=UPPER_BOUND, because=":having()")
        self._read(part=QUERY, kind="instance_manifest", count=instances, basis=EXACT, because=":having()")
        content = call.arg if isinstance(call.arg, FunctionCall3) else None
        if content is not None and content.name in WHOLE_FILES:
            self._read(
                part=QUERY,
                kind=WHOLE_FILES[content.name],
                count=instances,
                basis=UPPER_BOUND,
                because=f":having(:{content.name}(...))",
            )
            self.why.append(
                f":having() by content reads candidates' {content.name} files during"
                " query; it stops at a run's first match, so this is the most"
            )
        elif self.reference.name_three is None:
            # the survivors' run results: at most one per pointer, else all
            self._read(
                part=QUERY,
                kind="run_manifest",
                count=n_picked,
                basis=UPPER_BOUND,
                because=":having()",
            )

    def _name_three_costs(self, *, three, runs: list, relisted: bool) -> None:
        basis = UPPER_BOUND if self.uncertain else EXACT
        listings = len(runs)
        self._read(part=QUERY, kind="run_listing", count=listings, basis=UPPER_BOUND, because=f".{three}")
        if not relisted:
            self._read(
                part=QUERY,
                kind="instance_manifest",
                count=sum(len(r["identities"]) for r in runs),
                basis=basis,
                because=f".{three}",
            )
        self.why.append(f"'.{three}' lists each run and reads each of its instance manifests")
        calls = list(three.functions)
        names = [c.name for c in calls]
        gated = any(self._is_gate(c) for c in calls) or "having" in names
        picked = self._instances_picked(three=three, runs=runs)
        picked_basis = UPPER_BOUND if (self.uncertain or gated) else EXACT
        having = next((c for c in calls if c.name == "having"), None)
        if (
            having is not None
            and isinstance(having.arg, FunctionCall3)
            and having.arg.name in WHOLE_FILES
        ):
            self._read(
                part=QUERY,
                kind=WHOLE_FILES[having.arg.name],
                count=sum(len(r["identities"]) for r in runs),
                basis=UPPER_BOUND,
                because=f":having(:{having.arg.name}(...))",
            )
        accessor = next(
            (c for c in calls if c.name in WHOLE_FILES or c.name == "manifest"), None
        )
        if accessor is not None:
            selects = any(n in RECORD_SELECTORS for n in names) or (
                isinstance(accessor.arg, FunctionCall3)
                and accessor.arg.name in RECORD_SELECTORS
            )
            fields = self._value_fields(calls)
            if picked > 1 and not selects and not fields:
                definite = picked_basis == EXACT
                self._raise_or_warn(
                    message=(
                        f"resolve: {picked} whole {accessor.name} files at once (compendium"
                        " 5.3); resolve from one of query()'s results, or select records"
                    ),
                    definite=definite,
                )
                if definite:
                    return
            kind = (
                "instance_manifest" if accessor.name == "manifest" else WHOLE_FILES[accessor.name]
            )
            if accessor.name == "file" and isinstance(accessor.arg, str):
                kind = NAMED_FILES.get(accessor.arg, "data_file")
            count_basis = UPPER_BOUND if accessor.name in OPTIONAL_FILES else picked_basis
            self._read(
                part=RESOLVE, kind=kind, count=picked, basis=count_basis, because=f":{accessor.name}()"
            )
            self.why.append(f":{accessor.name}() reads one file per instance at resolve")
            return
        fields = self._value_fields(calls)
        if fields:
            self._read(
                part=RESOLVE,
                kind="instance_manifest",
                count=picked,
                basis=picked_basis,
                because=f":{fields[-1].name}()",
            )

    def _instances_picked(self, *, three, runs: list) -> int:
        names = [c.name for c in three.functions]
        if any(n in POINTERS for n in names):
            return len(runs)
        body = three.body
        if body is not None and not isinstance(body, Star3):
            return sum(1 for r in runs if str(body) in r["identities"])
        lower = next(
            (c for c in three.functions if c.name == "from" and isinstance(c.arg, int)), None
        )
        upper = next(
            (c for c in three.functions if c.name == "to" and isinstance(c.arg, int)), None
        )
        total = 0
        for r in runs:
            n = len(r["identities"])
            if lower or upper:
                start = lower.arg if lower else 0
                if upper is None:
                    stop = n
                elif upper.arg >= 0:
                    stop = upper.arg + 1
                else:
                    stop = n + upper.arg + 1
                n = max(0, min(stop, n) - start)
            total += n
        return total

    @staticmethod
    def _value_fields(calls: list) -> list:
        return [
            c
            for c in calls
            if (cls := ReferenceFunctionFactory.get_registered_class(c.name))
            and cls.ROLE == Function3.VALUE
            and cls.SOURCE == "manifest"
            and c.arg is None
            and c.name != "manifest"
        ]

    #
    # bookkeeping
    #
    def _read(self, *, part: str, kind: str, count: int, basis: str, because: str) -> None:
        if count:
            self.reads.append(
                Read(part=part, kind=kind, count=count, basis=basis, because=because)
            )

    def _raise_or_warn(self, *, message: str, definite: bool) -> None:
        """a definite raise is would_raise; one that depends on a gate or a
        window says "may raise" """
        self.would_raise = message if definite else f"may raise -- {message}"
