from .files_estimator_3 import FilesEstimator3
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
#   result.
#


class CsvpathsEstimator3(FilesEstimator3):
    MANIFEST_KIND = "group_manifest"
    NAME_KEY = "named_paths_name"
    ROOT_CONFIG = "inputs_csvpaths_path"
    LEDGER_METHOD = "paths_ledger"
    NOUN = "named-paths groups"
    NOT_A_VERSION = ("unchanged",)

    def _field_costs(self, *, fields: list, selected: int, literal: bool) -> None:
        if literal:
            super()._field_costs(fields=fields, selected=selected, literal=literal)
            return
        self._read(part=RESOLVE, kind="name_listing", count=selected, basis=UPPER_BOUND, because=f":{fields[-1].name}()")
        self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=2 * selected, basis=UPPER_BOUND, because=f":{fields[-1].name}()")

    def _version_costs(self, *, three, call_names: list, literal: bool, n_names: int, selected: int) -> bool:
        if three is None:
            # a version is the group's manifest entry, already read
            return True
        # each selected statement rereads the group's manifest
        statements = self._statements(three=three, selected=selected)
        self._read(part=RESOLVE, kind=self.MANIFEST_KIND, count=statements, basis=UPPER_BOUND, because=f".{three}")
        return True

    def _statements(self, *, three, selected: int) -> int:
        # statements per version are not in the ledger: count a pointer or
        # an identity as one per version, anything else as a bound of the
        # versions' statement lists, estimated generously
        names = [c.name for c in three.functions]
        if three.body is not None or any(n in ("first", "last", "index") for n in names):
            return selected
        return max(selected, 1) * 4
