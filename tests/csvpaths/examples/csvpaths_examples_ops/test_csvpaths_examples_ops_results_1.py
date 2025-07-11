import time
import unittest
import os
import pytest
from csvpath import CsvPaths
from csvpath.util.path_util import PathUtility as pathu

INVOICES = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices"
ASSETS = (
    f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}assets"
)
MAR = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Mar"
JAN = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Jan"
FEB = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Feb"
CSV = f"{INVOICES}{os.sep}2025{os.sep}Feb{os.sep}Acme_invoices_2025-01-25.csv"
ACME = f"{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme"


class TestCsvPathsExamplesResultsOps_1(unittest.TestCase):
    def test_results_references_ops_1(self):
        name = "invoices"
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, print")
        #
        # five files, seven registrations. 1 second between first and rest. another
        # second between the rest and the last.
        #
        dirname = MAR
        paths.file_manager.add_named_files_from_dir(
            dirname, name=name, template=":6/:8/:9/:filename"
        )
        time.sleep(0.25)

        dirname = JAN
        paths.file_manager.add_named_files_from_dir(
            dirname, name=name, template=":6/:8/:9/:filename"
        )
        time.sleep(0.25)

        dirname = ACME
        paths.file_manager.add_named_files_from_dir(
            dirname, name=name, template=":6/:8/:9/:filename"
        )
        time.sleep(0.25)

        dirname = FEB
        paths.file_manager.add_named_files_from_dir(
            dirname, name=name, template=":6/:8/:9/:filename"
        )

        paths.file_manager.add_named_file(name="acme-invoices", path=CSV)
        #
        # we don't know the order the files returned from the dirname pointer.
        # that makes a diffence in some tests below.
        #
        paths.file_manager.add_named_files_from_dir(
            name="acme-invoices", dirname=INVOICES
        )
        #
        # but because we don't necessarily want all the files under 1 named-path name we can use a
        # named-paths template. the template will create a results tree like:
        #
        #   archive/acme/invoices/2025/feb/2025-03-21_12-24-48/data.csv
        #
        paths.paths_manager.add_named_paths_from_file(
            name="clean-invoices",
            file_path=f"{ASSETS}{os.sep}clean-invoices.csvpath",
            template=":6/invoices/:8/:9/:run_dir",
        )
        #
        # main test here
        #
        paths.collect_paths(pathsname="clean-invoices", filename="acme-invoices")
        arc = paths.config.archive_path
        arc = os.path.join(arc, "clean-invoices")
        arc = os.path.join(arc, "acme/invoices/2025/Jan/")
        arc = pathu.resep(arc)
        mani = paths.file_manager.get_manifest("acme-invoices")
        rmani = paths.results_manager.get_last_named_result(
            name="clean-invoices"
        ).run_manifest
        assert mani
        assert mani[len(mani) - 1]["file"] == rmani["named_file_path"]
