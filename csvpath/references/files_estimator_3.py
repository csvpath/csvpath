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
# The FILES cost estimate (references_v3_cost_estimates.md, approved by
# David 2026-11-17). It reads the named-files ledger once and never lists a
# directory or opens a manifest; the ledger gives the names and, per name,
# its registrations (failures left out), which stand in for its versions.
#
# The read factors are the FILES finder's, measured with the read counter
# on the corpus:
# - a literal root reads that name's manifest; a '*', ':regex()' or
#   ':choice()' root lists the names and reads each one's manifest, and a
#   gate under '*' does that twice;
# - the ledger set ('*' or a pattern root with ':manifest()') reads the
#   ledger, and anything beyond the bare '*' set also builds the live index
#   (a name listing and every named-file manifest); a ledger-field gate
#   rereads the ledger per record;
# - a bare ':manifest()', ':definition()', definition field or ':readme()'
#   on a literal root reads that one file at resolve;
# - a version resolves to its file, one at a time (compendium 5.3); a value
#   field rereads the name's manifest per selected version.
#
# First cut: versions per name are an estimate (only the manifests say which
# registrations are live), and most counts beyond the ledger are upper
# bounds.
#
POINTERS = ("first", "last", "index")
DEFINITION_FILES = ("definition",)
PATH_BUILDERS = ("regex", "choice", "name")


class FilesEstimator3:
    def __init__(self, *, finder) -> None:
        if finder is None:
            raise ValueError("finder cannot be None")
        self.finder = finder
        self.csvpaths = finder.csvpaths
        self.reference = finder.ref.parsed
        self.reads = []
        self.why = []
        self.would_raise = None

    def estimate(self) -> ReferenceEstimate3:
        root = self.csvpaths.config.inputs_files_path
        ledger = self._ledger(root)
        if self.finder._bare_log_call(self.reference) is not None:
            if isinstance(self.reference.root_major, Star3):
                self._read(part=RESOLVE, kind="log", count=1, basis=UPPER_BOUND, because=":log()")
            else:
                self.would_raise = "query: :log() requires root_major '*'"
        else:
            self._estimate(ledger)
        return ReferenceEstimate3(
            reference=str(self.finder.ref.reference),
            reads=self.reads,
            why=self.why,
            backend=Nos(root).backend,
            weights=CostWeights.for_config(self.csvpaths.config),
            sql=self.csvpaths.config.references_sql == "on",
            would_raise=self.would_raise,
        )

    #
    # the ledger, read never written
    #
    def _ledger(self, root: str) -> list:
        source = self.finder.source
        if isinstance(source, SqlReferenceSource):
            return source.files_ledger() or []
        return FilesystemReferenceSource.read_json(Nos(root).join("manifest.json")) or []

    def _versions_by_name(self, ledger: list) -> dict:
        by_name = {}
        for entry in ledger:
            name = entry.get("named_file_name")
            if name is None:
                continue
            by_name.setdefault(name, 0)
            if str(entry.get("status") or "").lower() != "failed":
                by_name[name] += 1
        return by_name

    def _names_in_play(self, by_name: dict) -> list:
        root = self.reference.root_major
        if isinstance(root, Star3):
            return sorted(by_name)
        if isinstance(root, FunctionCall3):
            pattern = self.finder._build(root).pattern
            return sorted(n for n in by_name if re.search(pattern, n))
        return [root] if root in by_name else []

    #
    # the estimate
    #
    def _calls(self) -> list:
        name_one = self.reference.name_one
        segments = [
            p for p in name_one.path if isinstance(p, FunctionCall3) and p.name not in PATH_BUILDERS
        ]
        return segments + list(name_one.functions)

    def _estimate(self, ledger: list) -> None:
        by_name = self._versions_by_name(ledger)
        names = self._names_in_play(by_name)
        literal = isinstance(self.reference.root_major, str)
        n_names = len(names)
        all_names = len(by_name)
        records = len(ledger)
        calls = self._calls()
        call_names = [c.name for c in calls]
        three = self.reference.name_three
        three_calls = list(three.functions) if three else []
        if n_names > 1:
            self.why.append(f"'{self.reference.root_major}' over {n_names} named-files")
        # a definition-backed field as name_one's whole content
        definition_call = self.finder._bare_definition_field_call(self.reference.name_one)
        if definition_call is not None and three is None:
            self._definition_field_costs(call=definition_call, literal=literal, n_names=n_names)
            return
        # bare well-known files on name_one
        bare = self._bare_well_known(calls)
        if bare is not None and three is None:
            self._bare_costs(bare=bare, literal=literal, n_names=n_names, all_names=all_names)
            return
        if "manifest" in call_names and not literal and three is None:
            self._ledger_set_costs(calls=calls, all_names=all_names, records=records)
            return
        if "manifest" in call_names and literal and three is None:
            # the name's own manifest chain: its entries
            self._read(part=QUERY, kind="named_file_manifest", count=1, basis=EXACT, because=":manifest()")
            self._read(part=RESOLVE, kind="named_file_manifest", count=1, basis=UPPER_BOUND, because=":manifest()")
            return
        # version traversal
        gates = [c for c in calls + three_calls if self._is_gate(c)]
        windows = [
            c
            for c in calls + three_calls
            if (cls := ReferenceFunctionFactory.get_registered_class(c.name)) is not None
            and cls.SOURCE == "clock"
        ]
        if any(self._is_ledger_field(g) for g in gates):
            self._read(part=QUERY, kind="ledger", count=1, basis=UPPER_BOUND, because=f":{gates[0].name}(...)")
        definition_gates = [c for c in calls + three_calls if self._is_definition_gate(c)]
        manifests = n_names * (2 if (gates and not literal) else 1)
        if "manifest" in call_names:
            manifests = n_names
        if not literal:
            self._read(part=QUERY, kind="name_listing", count=2 if gates else 1, basis=UPPER_BOUND, because=str(self.reference.root_major))
        if definition_gates and three is None:
            self._read(part=QUERY, kind="definition", count=n_names, basis=UPPER_BOUND, because=f":{definition_gates[0].name}(...)")
            return
        self._read(
            part=QUERY,
            kind="named_file_manifest",
            count=manifests,
            basis=EXACT if (literal and not gates) else UPPER_BOUND,
            because="each named-file's manifest",
        )
        versions = sum(by_name[n] for n in names)
        selected = self._selected(calls=calls + three_calls, names=names, by_name=by_name)
        fields = self._value_fields(calls + three_calls)
        if fields:
            self._read(part=RESOLVE, kind="named_file_manifest", count=selected, basis=UPPER_BOUND, because=f":{fields[-1].name}()")
            if any(self._is_ledger_field(f) for f in fields):
                self._read(part=RESOLVE, kind="ledger", count=selected, basis=UPPER_BOUND, because=f":{fields[-1].name}()")
            return
        if three is None and not any(n in POINTERS for n in call_names):
            # a name_one result is the named-file, not a version: no file read
            return
        if three is None and not literal:
            # a name_one pointer under '*' rereads the names at resolve
            self._read(part=RESOLVE, kind="name_listing", count=1, basis=UPPER_BOUND, because="a name_one pointer")
            self._read(part=RESOLVE, kind="named_file_manifest", count=n_names, basis=UPPER_BOUND, because="a name_one pointer")
            return
        if selected > 1:
            gated = bool(gates) or bool(windows) or versions == 0
            message = f"resolve: {selected} version files at once (compendium 5.3)"
            self.would_raise = f"may raise -- {message}" if gated else message
        # one version file is read; a second one raises (compendium 5.3)
        self._read(part=RESOLVE, kind="version_file", count=1, basis=UPPER_BOUND, because="the version's file")
        self.why.append("a version resolves to its file, one at a time")

    def _definition_field_costs(self, *, call, literal: bool, n_names: int) -> None:
        if not literal:
            self._read(part=QUERY, kind="name_listing", count=1, basis=UPPER_BOUND, because=str(self.reference.root_major))
        if call.arg is not None:
            # a filter on each name's definition
            self._read(part=QUERY, kind="definition", count=n_names, basis=UPPER_BOUND, because=f":{call.name}(...)")
            self._read(part=RESOLVE, kind="definition", count=n_names, basis=UPPER_BOUND, because=f":{call.name}(...)")
            return
        if not literal and n_names > 1:
            self.would_raise = f"resolve: {n_names} definitions at once (compendium 5.3)"
            return
        self._read(part=RESOLVE, kind="definition", count=1, basis=EXACT if literal else UPPER_BOUND, because=f":{call.name}()")

    def _bare_well_known(self, calls: list) -> "str | None":
        if self.finder._is_bare_pointer_reference(self.reference, "manifest"):
            return "manifest"
        if self.finder._is_bare_pointer_reference(self.reference, "readme"):
            return "readme"
        if self.finder._is_bare_pointer_reference(self.reference, "definition"):
            return "definition"
        if len(calls) == 1 and self._is_definition_field(calls[0]) and calls[0].arg is None:
            return "definition"
        return None

    def _bare_costs(self, *, bare: str, literal: bool, n_names: int, all_names: int) -> None:
        if bare == "manifest":
            if literal:
                self._read(part=RESOLVE, kind="named_file_manifest", count=1, basis=EXACT, because=":manifest()")
                return
            self._read(part=RESOLVE, kind="ledger", count=1, basis=EXACT, because=":manifest()")
            if not isinstance(self.reference.root_major, Star3):
                # a pattern root filters the set by each record's owner
                self._read(part=RESOLVE, kind="name_listing", count=1, basis=UPPER_BOUND, because="the live index")
                self._read(part=RESOLVE, kind="named_file_manifest", count=all_names, basis=UPPER_BOUND, because="the live index")
            return
        kind = "readme" if bare == "readme" else "definition"
        if literal:
            self._read(part=RESOLVE, kind=kind, count=1, basis=EXACT, because=f":{bare}()")
            return
        self._read(part=QUERY, kind="name_listing", count=1, basis=UPPER_BOUND, because=str(self.reference.root_major))
        if n_names > 1:
            self.would_raise = f"resolve: {n_names} {kind} files at once (compendium 5.3)"
            return
        self._read(part=RESOLVE, kind=kind, count=1, basis=UPPER_BOUND, because=f":{bare}()")

    def _ledger_set_costs(self, *, calls: list, all_names: int, records: int) -> None:
        gates = [c for c in calls if self._is_gate(c)]
        self._read(
            part=QUERY,
            kind="ledger",
            count=1 + (records if gates else 0),
            basis=UPPER_BOUND if gates else EXACT,
            because="the files ledger",
        )
        if gates:
            self._read(part=QUERY, kind="name_listing", count=1, basis=UPPER_BOUND, because="the live index")
            self._read(part=QUERY, kind="named_file_manifest", count=all_names, basis=UPPER_BOUND, because="the live index")
        self._read(part=RESOLVE, kind="ledger", count=max(1, records), basis=UPPER_BOUND, because=":manifest()")
        self._read(part=RESOLVE, kind="name_listing", count=1, basis=UPPER_BOUND, because="the live index")
        self._read(part=RESOLVE, kind="named_file_manifest", count=all_names, basis=UPPER_BOUND, because="the live index")
        self.why.append(":manifest() reads the ledger set; live records also read each named-file's manifest")

    def _selected(self, *, calls: list, names: list, by_name: dict) -> int:
        call_names = [c.name for c in calls]
        if "flatten" in self._path_function_names() and any(n in POINTERS for n in call_names):
            return 1
        if any(n in POINTERS for n in call_names):
            return len(names)
        return sum(by_name[n] for n in names)

    def _path_function_names(self) -> list:
        return [p.name for p in self.reference.name_one.path if isinstance(p, FunctionCall3)]

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
    def _is_definition_field(call) -> bool:
        cls = ReferenceFunctionFactory.get_registered_class(call.name)
        return cls is not None and cls.ROLE == Function3.VALUE and cls.SOURCE == "definition"

    def _is_definition_gate(self, call) -> bool:
        return self._is_definition_field(call) and call.arg is not None

    @staticmethod
    def _is_ledger_field(call) -> bool:
        cls = ReferenceFunctionFactory.get_registered_class(call.name)
        return cls is not None and bool(getattr(cls, "LEDGER_KEY", None)) and not cls.KEY

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

    def _read(self, *, part: str, kind: str, count: int, basis: str, because: str) -> None:
        if count:
            self.reads.append(Read(part=part, kind=kind, count=count, basis=basis, because=because))
