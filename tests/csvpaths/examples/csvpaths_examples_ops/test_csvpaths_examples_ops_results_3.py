import time
import unittest
import os
import pytest
from csvpath import CsvPaths

INVOICES = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices"
ASSETS = (
    f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}assets"
)
MAR = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Mar"
JAN = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Jan"
FEB = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Feb"
CSV = f"{INVOICES}{os.sep}2025{os.sep}Feb{os.sep}Acme_invoices_2025-01-25.csv"
ACME = f"{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme"


class TestCsvPathsExamplesResultsOps_3(unittest.TestCase):
    def test_results_references_ops_3(cls):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, print")
        #
        # five files, seven registrations. 1 second between first and rest. another
        # second between the rest and the last.
        #
        dirname = MAR
        paths.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":6/:8/:9/:filename"
        )
        time.sleep(0.25)

        dirname = JAN
        paths.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":6/:8/:9/:filename"
        )
        time.sleep(0.25)

        dirname = ACME
        paths.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":6/:8/:9/:filename"
        )
        time.sleep(0.25)

        dirname = FEB
        paths.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":6/:8/:9/:filename"
        )

        paths.file_manager.add_named_file(
            name="acme-invoices",
            path=CSV,
        )
        #
        # we don't know the order the files returned from the dirname pointer.
        # that makes a diffence in some tests below.
        #
        paths.file_manager.add_named_files_from_dir(
            name="acme-invoices", dirname=f"{INVOICES}"
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

        paths.collect_paths(
            pathsname="clean-invoices", filename="$acme-invoices.files.:3"
        )
        #
        # run the clean-invoices named-paths group against the data generated in the last run
        # in feb starting at the second step.
        #
        #
        # again, can't rely on the order of the files add by directory above.
        #
        rmani = paths.results_manager.get_last_named_result(
            name="clean-invoices"
        ).run_manifest
        run_home = rmani["run_home"]
        month = os.path.dirname(run_home)
        month = os.path.basename(month)
        #
        #
        #
        paths.collect_paths(
            pathsname="clean-invoices",
            filename=f"$clean-invoices.results.acme/invoices/2025/{month}/202:last.step-two",
        )
