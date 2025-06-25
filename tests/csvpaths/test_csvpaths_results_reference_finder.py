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

FILES = {
    "food": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv",
    "test": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}test.csv",
}
NAMED_PATHS_DIR = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}"
)


class TestResultsCsvPathsReferenceFinder(unittest.TestCase):
    def setup(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.file_manager.set_named_files(FILES)
        paths.fast_forward_paths(filename="food", pathsname="food")
        return paths

    def test_results_ref_finder_num_pos(self):
        paths = self.setup()
        results1 = ResultsReferenceFinder(
            paths, reference="$food.results.:today"
        ).query()
        print(f"test_files_ref_finder_num_pos: results1: {results1.files}")

        psi = len(results1)
        paths.fast_forward_paths(filename="food", pathsname="food")
        results2 = ResultsReferenceFinder(
            paths, reference="$food.results.:today"
        ).query()
        print(f"test_files_ref_finder_num_pos: results2: {results2.files}")
        assert psi + 1 == len(results2)

    def test_files_ref_finder_last_changes(self):
        paths = self.setup()

        i = paths.results_manager.get_number_of_results("food")
        results = ResultsReferenceFinder(
            paths, reference="$food.results.:today:last"
        ).query()
        results1 = results.files[0]
        iminus = i - 1
        chk = ResultsReferenceFinder(
            paths, reference=f"$food.results.:{iminus}"
        ).query()
        chk = results.files[0]
        assert results1 == chk

        paths.fast_forward_paths(filename="food", pathsname="food")

        results = ResultsReferenceFinder(
            paths, reference="$food.results.:today:last"
        ).query()
        results2 = results.files[0]
        assert results1 != results2
        chk = ResultsReferenceFinder(paths, reference=f"$food.results.:{i}").query()
        chk = results.files[0]
        assert results2 == chk

        last = (
            ResultsReferenceFinder(paths, reference="$food.results.:today:last")
            .query()
            .files[0]
        )
        assert results2 == last
        files = (
            ResultsReferenceFinder(paths, reference="$food.results.:today")
            .query()
            .files
        )
        assert results1 in files
        assert results1 == files[-2]
        index1 = files.index(results1)
        index2 = files.index(
            ResultsReferenceFinder(paths, reference="$food.results.:today:first")
            .query()
            .files[0]
        )
        assert index2 <= index1
        assert index2 == 0

    def test_results_ref_finder_today(self):
        paths = self.setup()
        starting = 0
        try:
            ps = ResultsReferenceFinder(paths, reference="$food.results.:today").query()
            starting = len(ps)
        except Exception:
            # we get here if this test is run stand-alone
            ...
        paths.fast_forward_paths(filename="food", pathsname="food")
        paths.fast_forward_paths(filename="food", pathsname="food")
        paths.fast_forward_paths(filename="food", pathsname="food")
        #
        # should have three more results
        #
        ps = ResultsReferenceFinder(paths, reference="$food.results.:today").query()
        plusthree = len(ps)
        assert plusthree == starting + 3
        #
        # check results by index
        #
        starting1 = starting + 1
        starting2 = starting + 2
        ref1 = f"$food.results.:{starting}"
        ref2 = f"$food.results.:{starting1}"
        ref3 = f"$food.results.:{starting2}"
        #
        # first a baseline default-last
        #
        resultsA = paths.results_manager.get_named_results("food")
        assert resultsA
        assert len(resultsA) == 2
        maniA = resultsA[0].run_manifest
        #
        #
        #
        resultsB = paths.results_manager.get_named_results(ref1)
        assert resultsB
        assert len(resultsB) == 2
        maniB = resultsB[0].run_manifest

        resultsC = paths.results_manager.get_named_results(ref2)
        assert resultsC
        assert len(resultsC) == 2
        maniC = resultsC[0].run_manifest

        resultsD = paths.results_manager.get_named_results(ref3)
        assert resultsD
        assert len(resultsD) == 2
        maniD = resultsD[0].run_manifest

        assert maniA["run_uuid"] == maniD["run_uuid"]  # most recent
        assert maniB["run_uuid"] != maniC["run_uuid"] != maniD["run_uuid"]
        #
        #
        #
        # dtB = datetime.fromisoformat(maniB["time"])
        B = exut.to_datetime(maniB["time"])
        # dtC = datetime.fromisoformat(maniC["time"])
        C = exut.to_datetime(maniC["time"])
        # dtD = datetime.fromisoformat(maniD["time"])
        D = exut.to_datetime(maniD["time"])
        assert B < C
        assert C < D

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
