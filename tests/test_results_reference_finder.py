import unittest
import os
import datetime
from datetime import timedelta, timezone
from csvpath import CsvPaths
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.files_reference_finder import FilesReferenceFinder
from csvpath.util.references.results_reference_finder import ResultsReferenceFinder
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.references.ref_utils import ReferenceUtility as refu

FILES = {
    "food": f"tests{os.sep}test_resources{os.sep}named_files{os.sep}food.csv",
    "test": f"tests{os.sep}test_resources{os.sep}named_files{os.sep}test.csv",
}
NAMED_PATHS_DIR = f"tests{os.sep}test_resources{os.sep}named_paths{os.sep}"


class TestFilesReferenceFinder(unittest.TestCase):
    def setup(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.file_manager.set_named_files(FILES)
        paths.fast_forward_paths(filename="food", pathsname="food")
        return paths

    def test_files_ref_finder_num_pos(self):
        paths = self.setup()
        ps = ResultsReferenceFinder(paths).resolve_possibles("$food.results.:today")
        psi = len(ps)
        paths.fast_forward_paths(filename="food", pathsname="food")
        ps = ResultsReferenceFinder(paths).resolve_possibles("$food.results.:today")
        assert psi + 1 == len(ps)

    def test_files_ref_finder_last_changes(self):
        paths = self.setup()

        ps = ResultsReferenceFinder(paths).resolve_possibles(
            "$food.results.:today:last"
        )
        psi = len(ps)
        first_index = psi - 1

        paths.fast_forward_paths(filename="food", pathsname="food")

        ps = ResultsReferenceFinder(paths).resolve_possibles(
            "$food.results.:today:last"
        )
        psi = len(ps)
        last_index = psi - 1
        assert first_index == last_index - 1

        last = ResultsReferenceFinder(paths).resolve("$food.results.:today:last")
        first = ResultsReferenceFinder(paths).resolve(
            f"$food.results.:today:{first_index}"
        )

        assert ps[len(ps) - 2] == first
        assert ps[len(ps) - 1] == last

    def test_files_ref_finder_today(self):
        paths = self.setup()

        ps = ResultsReferenceFinder(paths).resolve_possibles("$food.results.:today")
        starting = len(ps)

        paths.fast_forward_paths(filename="food", pathsname="food")
        paths.fast_forward_paths(filename="food", pathsname="food")
        paths.fast_forward_paths(filename="food", pathsname="food")
        #
        # should have three more results
        #
        ps = ResultsReferenceFinder(paths).resolve_possibles("$food.results.:today")
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

        assert maniA["uuid"] == maniD["uuid"]
        assert maniB["uuid"] != maniC["uuid"] != maniD["uuid"]
        assert maniB["time"] < maniC["time"] < maniD["time"]

    def test_result_manifest_2(self):
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
