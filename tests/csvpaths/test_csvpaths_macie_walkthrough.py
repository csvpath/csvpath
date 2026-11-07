"""A walkthrough of a Macie wrapper's life in a CsvPaths project, end to
end, as one linear test to read and step through. Run it with -s to see
each step's output:

    poetry run pytest -s tests/csvpaths/test_csvpaths_macie_walkthrough.py

It uses normative pair 09_text_allow_list, a classification job with a
custom data identifier (employee ids) and a text allow list, so the
group's assets show up. Pairs 10 and up use managed identifiers, the
stand-ins in csvpath/macie/rulesbase/managed_identifiers.json; to walk
one of those instead, change PAIR and WRAPPER. The assertions are
light; tests/csvpaths/test_csvpaths_macie.py and tests/macie/ test each
piece in detail. The steps:

    1. a CsvPaths project, local backend
    2. load the wrapper into a named-paths group: convert, copy the wrapper
       and its conversion report into the group home, store the allow list
       in the group's assets
    3. register the data as a named-file
    4. run the group
    5. the results: printouts, errors (one per detailed occurrence) and
       the findings, a Macie-style JSON document in the macie_findings
       variable

Step 4's run dir listing includes _extra_data/macie/: the run's copy of
the wrapper, its conversion report, the managed identifier catalog
snapshot and the allow list, with each file's sha256 in inputs.json, so
the run can be replicated with the exact rules it used
(specs/macie/rulesbase-design.md, P2b). A standalone CsvPath run copies
nothing and says so on the macie stream (P2c).
"""

import json
import os

from csvpath import CsvPaths

PAIR = os.path.join(
    "tests", "macie", "test_resources", "normative", "09_text_allow_list"
)
WRAPPER = os.path.join(PAIR, "hr-contractor-allow.macie.json")
DATA = os.path.join(PAIR, "data", "employees.csv")
GROUP = "macie_walkthrough"
NAMED_FILE = "macie_walkthrough_employees"


def _step(title: str) -> None:
    print(f"\n==== {title}")


def _tree(path: str) -> None:
    for root, _, files in sorted(os.walk(path)):
        for f in sorted(files):
            print("   ", os.path.relpath(os.path.join(root, f), path))


class TestMacieWalkthrough:
    def setup_method(self) -> None:
        self.paths = CsvPaths()
        self._clean()

    def teardown_method(self) -> None:
        self._clean()

    def _clean(self) -> None:
        self.paths.paths_manager.remove_named_paths(GROUP)
        self.paths.file_manager.remove_named_file(NAMED_FILE)

    def test_macie_walkthrough(self) -> None:
        paths = self.paths
        _step("1. the project")
        #
        # config.ini [macie] can set max_findings (the circuit breaker) and
        # max_detail (how many occurrences per identifier are printed and
        # recorded as errors). The pair's expected results use 3.
        #
        paths.config.set(section="macie", name="max_detail", value="3")
        print("    named-paths home:", paths.paths_manager.named_paths_dir)

        _step("2. load the Macie wrapper into a named-paths group")
        #
        # the paths manager sees the .macie.json suffix, converts the
        # wrapper with MacieGroupLoader / MacieConverter, refuses a shared
        # Macie csvpath id, stores the text allow lists, then loads the
        # csvpath like any other
        #
        paths.paths_manager.add_named_paths_from_file(name=GROUP, file_path=WRAPPER)
        home = paths.paths_manager.named_paths_home(GROUP)
        print("    group home:", home)
        _tree(home)
        csvpath = paths.paths_manager.get_named_paths(GROUP)[0]
        print("    the generated csvpath (first lines):")
        for line in csvpath.strip().splitlines()[:12]:
            print("     |", line)
        with open(f"{os.path.join(home, os.path.basename(WRAPPER))}.report.json") as f:
            report = json.load(f)
        print("    conversion report: skipped", len(report["skipped"]), "items;")
        print("    lists", report["lists"])
        assert len(paths.paths_manager.get_named_paths(GROUP)) == 1

        _step("3. register the data as a named-file")
        paths.file_manager.add_named_file(name=NAMED_FILE, path=DATA)
        print("    named-file:", NAMED_FILE, "from", DATA)

        _step("4. run the group")
        paths.collect_paths(filename=NAMED_FILE, pathsname=GROUP)
        result = paths.results_manager.get_named_results(GROUP)[0]
        print("    run dir:", result.run_dir)
        _tree(result.run_dir)
        #
        # the run's copy of its Macie inputs, for replication
        #
        inputs = os.path.join(result.run_dir, "_extra_data", "macie", "inputs.json")
        with open(inputs, encoding="utf-8") as f:
            recorded = json.load(f)
        print("    _extra_data/macie/inputs.json records:", sorted(recorded["files"]))
        assert recorded["group"] == GROUP

        _step("5. the results")
        print("    valid:", result.csvpath.is_valid)
        print("    matched lines (lines with a finding):", len(result.lines.to_list()))
        print("    printouts on the macie stream:")
        for p in result.get_printouts("macie"):
            print("     |", p)
        print("    errors (one per detailed occurrence):", len(result.errors))
        findings = result.csvpath.variables["macie_findings"]
        print("    findings (the macie_findings variable):")
        for line in json.dumps(findings, indent=2).splitlines()[:30]:
            print("     |", line)
        with open(os.path.join(PAIR, "expected", "findings.json")) as f:
            assert findings == json.load(f)
