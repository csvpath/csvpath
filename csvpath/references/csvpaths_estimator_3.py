from .csvpaths_reference_finder_3 import CsvpathsReferenceFinder3
from .files_estimator_3 import FilesEstimator3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_3 import FunctionCall3, Star3
from .reference_estimate_3 import RESOLVE, UPPER_BOUND

#
# The CSVPATHS cost estimate (references_v3_cost_estimates.md). It shares
# FILES' shape -- a root ledger, per-name manifests, the ledger set and its
# live index, definitions and readmes -- with these differences, measured
# with the read counter on the corpus:
# - the paths ledger has one entry per load; an unchanged reload is not a
#   version;
# - a version selected in name_one reads no content at resolve;
# - name_three selects statements, and each rereads the group's manifest;
# - a value field under a '*' root rereads the names and two manifests per
#   result;
# - every function goes only where its POSITIONS put it for csvpaths, so a
#   misplaced one is a definite raise (definition fields only "may raise").
#


class CsvpathsEstimator3(FilesEstimator3):
    MANIFEST_KIND = "group_manifest"
    NAME_KEY = "named_paths_name"
    ROOT_CONFIG = "inputs_csvpaths_path"
    LEDGER_METHOD = "paths_ledger"
    NOUN = "named-paths groups"
    NOT_A_VERSION = ("unchanged",)
    DATATYPE = "csvpaths"

    def _field_costs(self, *, fields: list, selected: int, literal: bool, n_names: int) -> None:
        if literal:
            super()._field_costs(fields=fields, selected=selected, literal=literal, n_names=n_names)
            return
        self._read(part=RESOLVE, kind="name_listing", count=selected, basis=UPPER_BOUND, because=f":{fields[-1].name}()")
        self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=2 * selected + n_names, basis=UPPER_BOUND, because=f":{fields[-1].name}()")
        if any(self._is_ledger_field(f) for f in fields):
            self._read(part=RESOLVE, kind="ledger", count=selected, basis=UPPER_BOUND, because=f":{fields[-1].name}()")


    def _possible_raise(self) -> "str | None":
        # most CSVPATHS rules are its functions' own POSITIONS, which match
        # the finder (measured), so they are definite (_datatype_raise);
        # these combinations are uncertain
        names = [c.name for c in self._calls()]
        if len(names) != len(set(names)):
            return "a function repeated on name_one"
        for i, name in enumerate(names):
            if name in ("manifest", "definition") and i > 0:
                return f"':{name}()' after other functions on name_one"
        return None

    def _datatype_raise(self, ledger: list) -> "str | None":
        """CSVPATHS' own refusals: no worksheets, and every function only
        where its POSITIONS put it for csvpaths"""
        if "#" in str(self.reference.name_one):
            return "query: CSVPATHS does not take a '#worksheet'"
        name_one = self.reference.name_one
        # a bare '*' is ':all()' (normative examples; finder tests)
        star = any(isinstance(p, Star3) for p in name_one.path)
        if star and not isinstance(self.reference.root_major, str) and "all" in [c.name for c in name_one.functions]:
            return "query: ':all()' does not combine with a '*' name_one during '*' traversal"
        if not star and not any(isinstance(p, FunctionCall3) for p in name_one.path) and not name_one.functions:
            return "query: CSVPATHS name_one is a version-selecting function chain, not a literal"
        try:
            # the finder's own static check: a definition field beside a
            # version selector (it reads nothing)
            CsvpathsReferenceFinder3._check_definition_field_has_no_version(self.reference.name_one)
        except Exception as e:
            return f"query: {e}"
        three = self.reference.name_three
        name_one = self.reference.name_one
        is_chain = bool(name_one.functions) or not isinstance(self.reference.root_major, str)
        calls = [c.name for c in self._calls()]
        # a ':definition(...)' filter is a chain too
        argued = any(c.name == "definition" and c.arg is not None for c in self._calls())
        is_chain = is_chain or len(calls) > 1 or argued
        # (a repeated function is uncertain instead: _possible_raise)
        if three is not None and "definition" in calls and is_chain and len(calls) == len(set(calls)):
            return "query: a ':definition()' chain, or one under '*', takes no name_three"
        if self.reference.name_three is not None and self.finder._bare_definition_field_call(self.reference.name_one):
            return "query: a definition field is not versioned, so it takes no name_three"
        for call in self._all_calls():
            # a definition field reads definition.json, so its positions do
            # not apply; another datatype's field already raised in
            # _definite_raise() (_check_datatype_functions(), #766)
            if self._is_definition_field(call) or call is self.reference.root_major:
                continue
            misplaced = self._misplaced(call)
            if misplaced is not None:
                return f"query: {misplaced}"
        return None

    def _misplaced(self, call) -> "str | None":
        cls = ReferenceFunctionFactory.get_registered_class(call.name)
        if cls is None:
            return None
        if self.DATATYPE not in cls.DATATYPES:
            return f"':{call.name}()' is not a {self.DATATYPE} function"
        positions = getattr(cls, "POSITIONS", {}).get(self.DATATYPE)
        three = self.reference.name_three
        position = "name_three" if three is not None and call in three.functions else "name_one"
        if positions is not None and position not in positions:
            return f"':{call.name}()' does not go in {position} for {self.DATATYPE}"
        return None

    def _version_costs(self, *, three, call_names: list, literal: bool, n_names: int, selected: int) -> bool:
        if three is None:
            # a version is the group's manifest entry, already read
            return True
        # each selected statement rereads the group's manifest; under '*' it
        # also relists the names and reads more manifests (measured up to
        # three per statement under a pattern root)
        statements = self._statements(three=three, selected=selected)
        if literal:
            self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=statements, basis=UPPER_BOUND, because=f".{three}")
            return True
        self._read(part=RESOLVE, kind="name_listing", count=statements, basis=UPPER_BOUND, because=f".{three}")
        self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=3 * statements, basis=UPPER_BOUND, because=f".{three}")
        return True

    def _selected(self, *, calls: list, names: list, by_name: dict) -> int:
        """the versions name_one selects. A name_three pointer picks a
        STATEMENT within each version (gap review N), not a version, so
        only name_one's functions count: '$x.csvpaths.*.:first()' is one
        statement of every version, not one version."""
        three = self.reference.name_three
        three_calls = list(three.functions) if three is not None else []
        own = [c for c in calls if not any(c is t for t in three_calls)]
        return super()._selected(calls=own, names=names, by_name=by_name)

    def _statements(self, *, three, selected: int) -> int:
        # statements per version are not in the ledger: count a pointer or
        # an identity as one per version, anything else as a bound of the
        # versions' statement lists, estimated generously
        names = [c.name for c in three.functions]
        if three.body is not None or any(n in ("first", "last", "index") for n in names):
            return selected
        return max(selected, 1) * 4
