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
# What the finder will refuse is checked from the reference alone: arguments
# (by building each function, which reads nothing), unknown names, and each
# datatype's own rules. A definite raise, or a possible one, turns every
# count into an upper bound, since where it raises is not estimated.
#
# First cut: versions per name are an estimate (only the manifests say which
# registrations are live), and most counts beyond the ledger are upper
# bounds.
#
POINTERS = ("first", "last", "index")
DEFINITION_FILES = ("definition",)
# functions that build name_one's path rather than select or read; ':name()'
# is costed on its own (a manifest reread at resolve)
PATH_BUILDERS = ("regex", "choice", "name")


class FilesEstimator3:
    # what differs between FILES and CSVPATHS (CsvpathsEstimator3)
    MANIFEST_KIND = "named_file_manifest"
    NAME_KEY = "named_file_name"
    ROOT_CONFIG = "inputs_files_path"
    LEDGER_METHOD = "files_ledger"
    NOUN = "named-files"
    NOT_A_VERSION = ("failed",)
    DATATYPE = "files"
    # name_one gates the FILES finder takes (reference_v3 :type()/:status() GATEs)
    NAME_ONE_GATES = ("type", "status", "lifecycle", "template")

    def __init__(self, *, finder) -> None:
        if finder is None:
            raise ValueError("finder cannot be None")
        self.finder = finder
        self.csvpaths = finder.csvpaths
        self.reference = finder.ref.parsed
        # the normalization query() applies, so the estimate sees the same
        # reference whether or not query() ran first ('beta/:manifest()';
        # reviewer on #793). It is idempotent.
        finder._attach_trailing_manifest(
            name_one=self.reference.name_one, implies_star=False
        )
        if self.reference.name_three is not None:
            self.reference.name_three.star_body_as_all()
        self.reads = []
        self.why = []
        self.would_raise = None

    def estimate(self) -> ReferenceEstimate3:
        root = getattr(self.csvpaths.config, self.ROOT_CONFIG)
        ledger = self._ledger(root)
        root_problem = self.finder._root_major_problem()
        if root_problem is not None:
            # query() raises building the root, before it reads anything
            self.would_raise = f"query: {root_problem}"
        elif self.finder._bare_log_call(self.reference) is not None:
            if isinstance(self.reference.root_major, Star3):
                self._read(part=RESOLVE, kind="log", count=1, basis=UPPER_BOUND, because=":log()")
            else:
                self.would_raise = "query: :log() requires root_major '*'"
        else:
            self._estimate(ledger)
        if root_problem is None:
            self._check_legality(ledger)
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
            return getattr(source, self.LEDGER_METHOD)() or []
        return (
            FilesystemReferenceSource.read_json(
                path=Nos(root).join("manifest.json"),
                logger=getattr(self.finder.csvpaths, "logger", None),
            )
            or []
        )

    def _versions_by_name(self, ledger: list) -> dict:
        by_name = {}
        for entry in ledger:
            name = entry.get(self.NAME_KEY)
            if name is None:
                continue
            by_name.setdefault(name, 0)
            if str(entry.get("status") or "").lower() not in self.NOT_A_VERSION:
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
        entries = self._entries_by_name(ledger)
        names = self._names_in_play(by_name)
        literal = isinstance(self.reference.root_major, str)
        n_names = len(names)
        all_names = len(by_name)
        records = len(ledger)
        calls = self._calls()
        call_names = [c.name for c in calls]
        three = self.reference.name_three
        three_calls = list(three.functions) if three else []
        if not literal and "manifest" in [c.name for c in three_calls]:
            # a name_three ':manifest()' under a traversal root lists the
            # named-files to find each version's manifest.json, at query
            # and again at resolve
            self._read(part=QUERY, kind="name_listing", count=1, basis=UPPER_BOUND, because="a name_three :manifest()")
            self._read(part=RESOLVE, kind="name_listing", count=1, basis=UPPER_BOUND, because="a name_three :manifest()")
            # and reads manifests to find each entry: the live index (every
            # named-file's) plus the entry's own
            self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=all_names + n_names, basis=UPPER_BOUND, because="a name_three :manifest()")
        if n_names > 1:
            self.why.append(f"'{self.reference.root_major}' over {n_names} {self.NOUN}")
        # a ':definition()' chain: definition.json, not the manifest
        if "definition" in self._path_function_names() and not self._is_bare_definition() and three is None:
            self._definition_chain_costs(literal=literal, n_names=n_names)
            return
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
            self._manifest_chain_costs(calls=calls, own_entries=entries.get(self.reference.root_major, 0), records=records)
            return
        if "manifest" in call_names and not literal:
            # ':manifest()' with a name_three reads the ledger and the live index
            self._read(part=QUERY, kind="ledger", count=1, basis=UPPER_BOUND, because=":manifest()")
            self._read(part=QUERY, kind=self.MANIFEST_KIND, count=all_names, basis=UPPER_BOUND, because="the live index")
        # version traversal
        gates = [c for c in calls + three_calls if self._is_gate(c)]
        ledger_gates = [g for g in gates if self._is_ledger_field(g)]
        if ledger_gates:
            # a ledger field gate rereads the ledger per record, and builds
            # the live index (a name listing and every manifest)
            self._read(part=QUERY, kind="ledger", count=1 + records, basis=UPPER_BOUND, because=f":{ledger_gates[0].name}(...)")
            self._read(part=QUERY, kind="name_listing", count=1, basis=UPPER_BOUND, because="the live index")
            self._read(part=QUERY, kind=self.MANIFEST_KIND, count=all_names, basis=UPPER_BOUND, because="the live index")
        definition_gates = [c for c in calls + three_calls if self._is_definition_gate(c)]
        manifests = n_names + all_names if (gates and not literal) else n_names
        if not literal:
            self._read(part=QUERY, kind="name_listing", count=2 if gates else 1, basis=UPPER_BOUND, because=str(self.reference.root_major))
        if definition_gates and three is None:
            self._read(part=QUERY, kind="definition", count=n_names, basis=UPPER_BOUND, because=f":{definition_gates[0].name}(...)")
            return
        self._read(
            part=QUERY,
            kind=self.MANIFEST_KIND,
            count=manifests,
            basis=EXACT if (literal and not gates) else UPPER_BOUND,
            because=f"each of the {self.NOUN}' manifests",
        )
        if "name" in self._path_function_names():
            # a ':name()' segment matches against the name's manifest again
            self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=n_names, basis=UPPER_BOUND, because=":name()")
        selected = self._selected(calls=calls + three_calls, names=names, by_name=by_name)
        fields = self._value_fields(calls + three_calls)
        definition_fields = [c for c in calls + three_calls if self._is_definition_field(c) and c.arg is None]
        if definition_fields:
            # a definition field after a version reads the definition; under
            # '*' it finds the name again first
            self._read(part=RESOLVE, kind="definition", count=selected + n_names, basis=UPPER_BOUND, because=f":{definition_fields[0].name}()")
            if not literal:
                self._read(part=RESOLVE, kind="name_listing", count=1, basis=UPPER_BOUND, because=f":{definition_fields[0].name}()")
                self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=selected + all_names, basis=UPPER_BOUND, because=f":{definition_fields[0].name}()")
            return
        if fields:
            self._field_costs(fields=fields, selected=selected, literal=literal, n_names=all_names)
            self._version_costs(three=three, call_names=call_names, literal=literal, n_names=n_names, selected=selected)
            return
        if self._version_costs(three=three, call_names=call_names, literal=literal, n_names=n_names, selected=selected):
            return
        if three is None and not any(n in POINTERS for n in call_names):
            # a name_one result is the named-file, not a version: no file read
            return
        if three is None and literal and set(call_names) & {"all", "groups"}:
            # a name_one pointer after a grouping wildcard picks one version
            # per group, and each resolves to its manifest entry: one read of
            # the name's manifest per version (5.21 "name_one, file pointer")
            self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=selected, basis=UPPER_BOUND, because="a name_one pointer per group")
            return
        if three is None and not literal:
            # a name_one pointer under '*' rereads the names at resolve
            self._read(part=RESOLVE, kind="name_listing", count=1, basis=UPPER_BOUND, because="a name_one pointer")
            self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=2 * n_names, basis=UPPER_BOUND, because="a name_one pointer")
            return
        if three is not None and isinstance(three.body, str) and three.body.isdigit():
            # a literal index selects one version at most
            selected = min(selected, 1)
        if selected > 1:
            # whether several versions reach resolve depends on how the
            # name's files are laid out (paths, registrations per path),
            # which the ledger does not show: the same shape raises on one
            # name and not another. So the 5.3 raise is always "may".
            self.would_raise = f"may raise -- resolve: up to {selected} version files at once (compendium 5.3)"
        # one version file is read, after the name's manifest; a second one
        # raises (compendium 5.3)
        if literal:
            self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=1, basis=UPPER_BOUND, because="the version's entry")
        self._read(part=RESOLVE, kind="version_file", count=1, basis=UPPER_BOUND, because="the version's file")
        self.why.append("a version resolves to its file, one at a time")

    def _entries_by_name(self, ledger: list) -> dict:
        """every ledger entry per name, versions or not"""
        entries = {}
        for entry in ledger:
            name = entry.get(self.NAME_KEY)
            if name is not None:
                entries[name] = entries.get(name, 0) + 1
        return entries

    def _is_bare_definition(self) -> bool:
        return self.finder._is_bare_pointer_reference(self.reference, "definition")

    def _definition_chain_costs(self, *, literal: bool, n_names: int) -> None:
        """':definition()' with a filter or a field: each name's definition"""
        if not literal:
            self._read(part=QUERY, kind="name_listing", count=1, basis=UPPER_BOUND, because=str(self.reference.root_major))
        definition = next(p for p in self.reference.name_one.path if isinstance(p, FunctionCall3) and p.name == "definition")
        if definition.arg is not None:
            self._read(part=QUERY, kind="definition", count=max(1, n_names), basis=UPPER_BOUND, because=f"{definition}")
        if self.reference.name_one.functions:
            if not literal:
                self._read(part=RESOLVE, kind="name_listing", count=n_names, basis=UPPER_BOUND, because=":definition() fields")
            self._read(part=RESOLVE, kind="definition", count=max(1, n_names), basis=UPPER_BOUND, because=":definition() fields")
        self.why.append(":definition() reads each name's definition.json")

    def _manifest_chain_costs(self, *, calls: list, own_entries: int, records: int) -> None:
        """a literal name's ':manifest()' chain: its entries, each of which a
        field, gate or range may reread"""
        self._read(part=QUERY, kind=self.MANIFEST_KIND, count=1, basis=EXACT, because=":manifest()")
        if any(self._is_ledger_field(c) and c.arg is not None for c in calls):
            self._read(part=QUERY, kind="ledger", count=1 + records, basis=UPPER_BOUND, because="a ledger field gate")
        self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=max(1, own_entries), basis=UPPER_BOUND, because=":manifest() entries")
        if any(self._is_ledger_field(c) and c.arg is None for c in calls):
            self._read(part=RESOLVE, kind="ledger", count=max(1, own_entries), basis=UPPER_BOUND, because="a ledger field")

    def _field_costs(self, *, fields: list, selected: int, literal: bool, n_names: int) -> None:
        """a value field rereads the name's manifest per selected version;
        under '*' it relists the names and reads each manifest again"""
        count = selected if literal else selected + n_names
        self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=count, basis=UPPER_BOUND, because=f":{fields[-1].name}()")
        if not literal:
            self._read(part=RESOLVE, kind="name_listing", count=1, basis=UPPER_BOUND, because=f":{fields[-1].name}()")
        if any(self._is_ledger_field(f) for f in fields):
            self._read(part=RESOLVE, kind="ledger", count=selected, basis=UPPER_BOUND, because=f":{fields[-1].name}()")

    def _version_costs(self, *, three, call_names: list, literal: bool, n_names: int, selected: int) -> bool:
        """a datatype's own resolve for selected versions; True when it has
        estimated them. FILES reads version files (below)."""
        return False

    def _definition_field_costs(self, *, call, literal: bool, n_names: int) -> None:
        if not literal:
            self._read(part=QUERY, kind="name_listing", count=1, basis=UPPER_BOUND, because=str(self.reference.root_major))
        if call.arg is not None:
            # a filter on each name's definition
            self._read(part=QUERY, kind="definition", count=n_names, basis=UPPER_BOUND, because=f":{call.name}(...)")
        if not literal:
            # each name's definition, relisting the names to find them
            self._read(part=RESOLVE, kind="name_listing", count=n_names, basis=UPPER_BOUND, because=f":{call.name}()")
            self._read(part=RESOLVE, kind="definition", count=n_names, basis=UPPER_BOUND, because=f":{call.name}()")
            return
        self._read(part=RESOLVE, kind="definition", count=1, basis=UPPER_BOUND if call.arg is not None else EXACT, because=f":{call.name}()")

    #
    # what the finder will refuse, from the reference alone
    #
    def _check_legality(self, ledger: list) -> None:
        self._ledger_cache = ledger
        reason = self._definite_raise(ledger)
        if reason is None and (self.would_raise is None or self.would_raise.startswith("may")):
            # a structural "may" outranks a resolve-time one: it may raise
            # before anything is read
            possible = self._possible_raise()
            reason = f"may raise -- {possible}" if possible is not None else None
        if reason is None:
            return
        self.would_raise = reason
        # where it raises is not estimated: every count becomes a bound
        # an estimate stays one: it is no bound to begin with (#798)
        self.reads = [Read(part=r.part, kind=r.kind, count=r.count, basis=r.basis if r.basis == ESTIMATE else UPPER_BOUND, because=r.because) for r in self.reads]

    def _all_calls(self) -> list:
        name_one = self.reference.name_one
        calls = [p for p in name_one.path if isinstance(p, FunctionCall3)] + list(name_one.functions)
        if self.reference.name_three is not None:
            calls += list(self.reference.name_three.functions)
        if isinstance(self.reference.root_major, FunctionCall3):
            calls.append(self.reference.root_major)
        return calls

    def _definite_raise(self, ledger: list) -> "str | None":
        try:
            # a foreign function, then two value-supplying functions, raise
            # first, as in query(); they read nothing
            self.finder._check_datatype_functions(self.reference)
            self.finder._check_wildcards(self.reference)
            self.finder._check_one_value(self.reference)
        except ReferenceException3 as e:
            return f"query: {e}"
        for call in self._all_calls():
            if call.name == "definition":
                # the finder reads a ':definition()' filter itself, not by
                # building it; its argument is built
                call = call.arg
                if not isinstance(call, FunctionCall3):
                    continue
            try:
                # builds and checks the arguments; it reads nothing
                self.finder._build(call)
            except Exception as e:
                return f"query: {e}"
        path_names = self._path_function_names()
        name_one = self.reference.name_one
        chains = [[p.name for p in name_one.path if isinstance(p, FunctionCall3)] + [c.name for c in name_one.functions]]
        if self.reference.name_three is not None:
            chains.append([c.name for c in self.reference.name_three.functions])
        for chain in chains:
            if sum(chain.count(n) for n in ("from", "after")) > 1 or sum(chain.count(n) for n in ("to", "before")) > 1:
                return "query: two range bounds in the same direction are not legal"
            if sum(chain.count(n) for n in POINTERS) > 1:
                return "query: at most one pointer function per chain"
        if "definition" in path_names and any(self._is_selector(c) for c in self.reference.name_one.functions):
            return "query: ':definition()' is not versioned, so it takes no pointer, range or date bound"
        if self.reference.name_three is not None and set(path_names + [c.name for c in name_one.functions]) & {"readme", "log"}:
            return "query: ':readme()' and ':log()' stand alone; they take no name_three"
        # ':readme()' with anything else in name_one, or a worksheet marker
        # (FILES _check_readme_is_alone(); CSVPATHS, which subclasses this
        # estimator, rejects the same shapes); a bare one under any root
        # goes on
        if "readme" in path_names + [c.name for c in name_one.functions] and (
            len(name_one.path) + len(name_one.functions) > 1 or name_one.name_two is not None
        ):
            return "query: ':readme()' must be the sole content of name_one"
        if "definition" in path_names:
            # a ':definition()' chain reads definition.json: no manifest
            # fields, no ':manifest()'
            if "manifest" in path_names:
                return "query: ':manifest()' is not supported in a ':definition()' chain"
            for call in self.reference.name_one.functions:
                cls = ReferenceFunctionFactory.get_registered_class(call.name)
                if cls is not None and cls.SOURCE == "manifest" and getattr(cls, "BARE_SOURCE", None) != "definition":
                    return f"query: ':{call.name}()' is not in a {self.NOUN[:-1]}'s definition.json"
        return self._datatype_raise(ledger)

    def _possible_raise(self) -> "str | None":
        """FILES: a field with an argument attached to name_one selects or
        gates only where the finder takes it there"""
        for call in self._calls():
            cls = ReferenceFunctionFactory.get_registered_class(call.name)
            if cls is None or cls.SOURCE in (None, "clock") or call.arg is None:
                # a clock value with an argument is a path segment
                # ('orders/:year(2026)'), not a field
                continue
            if call.name not in self.NAME_ONE_GATES:
                return f"':{call.name}(...)' on name_one; field functions usually go in name_three"
        path_names = self._path_function_names()
        names = [c.name for c in self._calls()]
        if len(names) != len(set(names)):
            return "a function repeated on name_one"
        if any(self._is_window(c) for c in self._calls()):
            return "a window on name_one; it usually goes in name_three"
        if path_names[:1] == ["definition"]:
            # a definition chain takes definition fields and filters
            for call in self.reference.name_one.functions:
                if not (self._is_definition_field(call) or call.name == "template"):
                    return f"':{call.name}()' in a ':definition()' chain"
            return None
        if path_names[:1] == ["manifest"]:
            return None
        # the FILES finder refuses many combinations on name_one (about a
        # dozen structural rules); the common legal ones are a single
        # selector or gate, so anything more is uncertain
        named = 1 if "name" in path_names else 0
        if len(self._calls()) + named >= 2:
            self._loose_shape()
            return "several functions on name_one; the FILES finder takes only some combinations"
        if (
            self.reference.name_three is not None
            and not self._ledger_gate_on_name_one()
            and any(self._is_gate(c) or self._is_window(c) for c in self._calls())
        ):
            return "a name_one gate or window with a name_three; the FILES finder takes only some combinations"
        return None

    @staticmethod
    def _is_selector(call) -> bool:
        """a pointer or a context setter (':all()', ranges, date bounds,
        ':having()'): it selects versions"""
        cls = ReferenceFunctionFactory.get_registered_class(call.name)
        return call.name in POINTERS or (cls is not None and cls.ROLE == Function3.CONTEXT_SETTER)

    def _ledger_gate_on_name_one(self) -> bool:
        """name_one is exactly one argued ledger field, e.g. ':status("failed")'"""
        calls = self._calls()
        return len(calls) == 1 and calls[0].arg is not None and self._is_ledger_field(calls[0])

    def _loose_shape(self) -> None:
        """an unusual shape: bound the reads it may make loosely, beyond
        what its family estimate gave"""
        n = max(1, len(self._names_in_play(self._versions_by_name(self._ledger_cache))))
        for kind in ("name_listing", "definition", self.MANIFEST_KIND):
            self._read(part=RESOLVE, kind=kind, count=n + 1, basis=UPPER_BOUND, because="an unusual shape")
        self.why.append("an unusual shape: its reads are bounded loosely")

    def _datatype_raise(self, ledger: list) -> "str | None":
        """FILES' own refusals"""
        root = self.reference.root_major
        if isinstance(root, str) and root not in self._entries_by_name(ledger):
            return f"query: no named-file '{root}' in the ledger"
        path_names = self._path_function_names()
        if path_names[:1] == ["manifest"] and "all" in [c.name for c in self.reference.name_one.functions]:
            return "query: ':manifest():all()' is not supported; a bare ':manifest()' is every record (#710)"
        if isinstance(root, FunctionCall3) and self.finder._is_bare_pointer_reference(self.reference, "readme"):
            return "query: ':readme()' under a pattern root is not supported"
        three = self.reference.name_three
        functions = [c.name for c in self.reference.name_one.functions]
        selectors = POINTERS + ("all", "from", "to")
        if "definition" in path_names and (three is not None or (not isinstance(root, str) and set(functions) & set(selectors))):
            return "query: ':definition()' does not combine with name_three, or with a selector during '*' traversal"
        all_names = path_names + functions
        # a bare ':status()'/':lifecycle()' gate takes any name_three since
        # the name_one gap review (item G); it took only a lone pointer
        if three is not None and set(all_names) & set(POINTERS):
            return "query: a name_one pointer takes no name_three; put the version-selecting function in name_three"
        if three is not None and self.finder._bare_definition_field_call(self.reference.name_one) is not None:
            return "query: a definition field is not versioned, so it takes no name_three"
        if not set(path_names + functions) & {"manifest", "definition"}:
            for call in self._calls():
                cls = ReferenceFunctionFactory.get_registered_class(call.name)
                if call in self._value_fields([call]) and self.DATATYPE in (cls.KEY or {}) and getattr(cls, "BARE_SOURCE", None) != "definition":
                    return f"query: ':{call.name}()' is a field; name_one picks the file, name_three reads its fields"

        if path_names[:1] == ["manifest"] and three is not None:
            return "query: a ':manifest()' chain takes no name_three"
        #
        # a pointer after a name_one wildcard is legal ('orders/:flatten():last()'
        # always worked; ':flatten():last()' and ':all():last()' since the
        # name_one gap review, compendium 4.2, 6.27d). An ':all()' riding
        # after one still raises.
        #
        if set(path_names) & {"all", "groups", "flatten"} and "all" in functions:
            return "query: ':all()' after a name_one wildcard is not legal; put it in its own path segment or in name_three"
        if not set(path_names) & {"manifest", "definition"} and any(n in POINTERS + ("all",) for n in path_names + functions):
            if self._value_fields(self._calls()):
                return "query: name_one picks the file; a field goes in name_three, after a '.'"
        return None

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
                self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=1, basis=EXACT, because=":manifest()")
                return
            self._read(part=RESOLVE, kind="ledger", count=1, basis=EXACT, because=":manifest()")
            if not isinstance(self.reference.root_major, Star3):
                # a pattern root filters the set by each record's owner
                self._read(part=RESOLVE, kind="name_listing", count=1, basis=UPPER_BOUND, because="the live index")
                self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=all_names, basis=UPPER_BOUND, because="the live index")
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
            because="the ledger",
        )
        # anything beyond the bare set builds the live index at query
        self._read(part=QUERY, kind="name_listing", count=1, basis=UPPER_BOUND, because="the live index")
        self._read(part=QUERY, kind=self.MANIFEST_KIND, count=all_names, basis=UPPER_BOUND, because="the live index")
        # and a field or range may reread it per record
        self._read(part=RESOLVE, kind="ledger", count=max(1, 2 * records), basis=UPPER_BOUND, because=":manifest()")
        self._read(part=RESOLVE, kind="name_listing", count=max(1, records), basis=UPPER_BOUND, because="the live index")
        self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=2 * records + all_names, basis=UPPER_BOUND, because="the live index")
        self.why.append(f":manifest() reads the ledger set; live records also read each of the {self.NOUN}' manifests")

    def _selected(self, *, calls: list, names: list, by_name: dict) -> int:
        call_names = [c.name for c in calls]
        if "all" in call_names or "groups" in call_names:
            # a pointer after ':all()' or ':groups()' picks one version per
            # group, and there can be as many groups as versions. ':groups()'
            # counted as one pointer's worth until the name_one gap review
            # (2026-11-19), so '$acme.files.:groups().:last()' estimated no
            # raise and raised at resolve.
            return sum(by_name[n] for n in names)
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
    def _is_window(call) -> bool:
        """a clock window or a date bound: it narrows by time, which the
        ledger estimate does not"""
        cls = ReferenceFunctionFactory.get_registered_class(call.name)
        return cls is not None and (cls.SOURCE == "clock" or call.name in ("before", "after", "on"))

    @staticmethod
    def _is_definition_field(call) -> bool:
        cls = ReferenceFunctionFactory.get_registered_class(call.name)
        return cls is not None and cls.ROLE == Function3.VALUE and cls.SOURCE == "definition"

    def _is_definition_gate(self, call) -> bool:
        return self._is_definition_field(call) and call.arg is not None

    def _is_ledger_field(self, call) -> bool:
        """a field this datatype reads from its root ledger, not a manifest"""
        cls = ReferenceFunctionFactory.get_registered_class(call.name)
        if cls is None:
            return False
        return self.DATATYPE in (getattr(cls, "LEDGER_KEY", None) or {}) and self.DATATYPE not in (cls.KEY or {})

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
