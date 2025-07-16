import unittest
import os

from datetime import datetime
from datetime import timedelta, timezone
from csvpath import CsvPaths
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.results_reference_finder_2 import (
    ResultsReferenceFinder2 as ResultsReferenceFinder,
)
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.references.ref_utils import ReferenceUtility as refu
from csvpath.matching.util.expression_utility import ExpressionUtility as exut
from tests.csvpaths.builder import Builder

FILES = {
    "food": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv",
    "test": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}test.csv",
}
NAMED_PATHS_DIR = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}"
)
FOOD = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}food.csvpaths"


class TestResultsCsvPathsReferenceFinder(unittest.TestCase):
    def setup(self):
        paths = Builder().build()
        paths.config.add_to_config("errors", "csvpath", "raise, print")
        #
        # remove everything
        #
        paths.results_manager.remove_named_results("food")
        paths.paths_manager.remove_named_paths("food")
        paths.file_manager.remove_named_file("food")
        paths.file_manager.remove_named_file("test")
        #
        # check that we're cleaned out
        #
        assert paths.results_manager.get_number_of_results("food") == 0
        assert paths.paths_manager.number_of_named_paths("food") == 0
        assert not paths.file_manager.has_named_file("food")
        assert not paths.file_manager.has_named_file("test")
        #
        # re-add
        #
        paths.paths_manager.add_named_paths(name="food", from_file=FOOD)
        paths.file_manager.set_named_files(FILES)
        #
        # run once with 2 results collected
        #
        paths.collect_paths(filename="food", pathsname="food")
        assert paths.results_manager.get_number_of_results("food") == 2
        return paths

    def test_results_ref_finder_num_pos(self):
        paths = self.setup()
        results1 = ResultsReferenceFinder(
            paths, reference="$food.results.:today"
        ).query()
        psi = len(results1)
        paths.fast_forward_paths(filename="food", pathsname="food")
        results2 = ResultsReferenceFinder(
            paths, reference="$food.results.:today"
        ).query()
        results2.ref.next == ["results_range_ordinal"]
        assert psi + 1 == len(results2)

    def test_results_ref_finder_date(self):
        paths = self.setup()
        #
        # the test above, and possibly others, runs food. we clear that and expect 1 result.
        #
        paths.results_manager.remove_named_results("food")
        assert paths.results_manager.get_number_of_results("food") == 0
        paths.fast_forward_paths(filename="food", pathsname="food")

        r = "$food.results.:all"
        results = ResultsReferenceFinder(paths, reference=r).query()
        print(f">> test_results_ref_finder_date: r: {r}, results: {results.files}\n")
        assert len(results.files) == 1

        adate = datetime.now(timezone.utc)
        adatestr = adate.strftime("%Y")
        r = f"$food.results.{adatestr}"
        results = ResultsReferenceFinder(paths, reference=r).query()
        print(f">> test_results_ref_finder_date: r: {r}, results: {results.files}\n")
        assert len(results.files) == 1

        r = "$food.results.2024-:after"
        results = ResultsReferenceFinder(paths, reference=r).query()
        print(f">> test_results_ref_finder_date: r: {r}, results: {results.files}\n")
        assert len(results.files) == 1

        adate = datetime.now(timezone.utc)
        adatestr = adate.strftime("%Y-%m-%d")
        r = f"$food.results.{adatestr}:all"
        results = ResultsReferenceFinder(paths, reference=r).query()
        print(f">> test_results_ref_finder_date: r: {r}, results: {results.files}\n")
        assert len(results.files) == 1

        r = "$food.results.2025-07-07:all"
        results = ResultsReferenceFinder(paths, reference=r).query()
        print(f">> test_results_ref_finder_date: r: {r}, results: {results.files}\n")
        assert len(results.files) == 0

        r = "$food.results.2025-07-07:after"
        results = ResultsReferenceFinder(paths, reference=r).query()
        print(f">> test_results_ref_finder_date: r: {r}, results: {results.files}\n")
        assert len(results.files) == 1

        r = "$food.results.2025-07-07:before"
        results = ResultsReferenceFinder(paths, reference=r).query()
        print(f">> test_results_ref_finder_date: r: {r}, results: {results.files}\n")
        assert len(results.files) == 0

    def test_results_ref_finder_instance(self):
        paths = self.setup()
        i = paths.results_manager.get_number_of_results("food")
        assert i > 0
        r = "$food.results.:today:last"
        results = ResultsReferenceFinder(paths, reference=r).query()
        assert len(results.files) > 0

        r = "$food.results.:today:last.candy check"
        results = ResultsReferenceFinder(paths, reference=r).query()
        assert len(results.files) > 0
        assert results.files[0].endswith("candy check")

        r = "$food.results.:today:last.ca"
        results = ResultsReferenceFinder(paths, reference=r).query()
        assert len(results.files) == 0

        r = "$food.results.:today:last.candy check:data"
        results = ResultsReferenceFinder(paths, reference=r).query()
        assert len(results.files) == 1
        assert results.files[0].endswith("data.csv")

    def test_results_ref_finder_last_changes(self):
        paths = self.setup()
        assert paths.results_manager.get_number_of_results("food") == 2

        results = ResultsReferenceFinder(
            paths, reference="$food.results.:today:last"
        ).query()
        assert len(results) == 1

        file1 = results.files[0]
        chk = ResultsReferenceFinder(paths, reference="$food.results.:0").query()
        assert len(chk) == 1
        assert results.files[0] == chk.files[0]
        assert results.ref.next == ["results_range_ordinal_instance"]

        paths.fast_forward_paths(filename="food", pathsname="food")

        results = ResultsReferenceFinder(
            paths, reference="$food.results.:today:last"
        ).query()
        assert len(results.files) == 1
        file2 = results.files[0]
        assert file1 != file2
        chk = ResultsReferenceFinder(paths, reference="$food.results.:1").query()
        assert len(results.files) == 1
        chk = results.files[0]
        assert file2 == chk

        results = ResultsReferenceFinder(
            paths, reference="$food.results.:today"
        ).query()

        assert file1 in results.files
        assert file1 == results.files[0]

        results = ResultsReferenceFinder(
            paths, reference="$food.results.:today:first"
        ).query()
        assert len(results.files) == 1
        file3 = results.files[0]
        assert file3 == file1

    def test_results_ref_finder_today(self):
        paths = self.setup()
        ps = ResultsReferenceFinder(paths, reference="$food.results.:today").query()
        assert len(ps) == 1
        paths.fast_forward_paths(filename="food", pathsname="food")
        paths.fast_forward_paths(filename="food", pathsname="food")
        paths.fast_forward_paths(filename="food", pathsname="food")
        #
        # should have three more results
        #
        ps = ResultsReferenceFinder(paths, reference="$food.results.:today").query()
        assert len(ps) == 4

        #
        # first a baseline default-last
        #
        resultsA = paths.results_manager.get_named_results("food")
        assert resultsA
        assert len(resultsA) == 2

        """ """
        maniA = resultsA[0].run_manifest
        #
        #
        #
        resultsB = paths.results_manager.get_named_results("$food.results.:1")
        assert resultsB
        assert len(resultsB) == 2
        maniB = resultsB[0].run_manifest

        resultsC = paths.results_manager.get_named_results("$food.results.:2")
        assert resultsC
        assert len(resultsC) == 2
        maniC = resultsC[0].run_manifest

        resultsD = paths.results_manager.get_named_results("$food.results.:3")
        assert resultsD
        assert len(resultsD) == 2
        maniD = resultsD[0].run_manifest

        assert maniA["run_uuid"] == maniD["run_uuid"]  # most recent
        assert maniB["run_uuid"] != maniC["run_uuid"] != maniD["run_uuid"]
        #
        #
        #
        B = exut.to_datetime(maniB["time"])
        C = exut.to_datetime(maniC["time"])
        D = exut.to_datetime(maniD["time"])
        assert B < C
        assert C < D
        """ """

    def test_results_ref_finder_manifest_2(self):
        paths = self.setup()
        paths.fast_forward_paths(filename="food", pathsname="food")
        paths.fast_forward_paths(filename="food", pathsname="food")

        result = paths.results_manager.get_named_results(
            "$food.results.:today:last.candy check"
        )
        mani1 = result.manifest

        mani2 = paths.results_manager.get_specific_named_result_manifest(
            "food", "candy check"
        )
        assert mani1["uuid"] == mani2["uuid"]
