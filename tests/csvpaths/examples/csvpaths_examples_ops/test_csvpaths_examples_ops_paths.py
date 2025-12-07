import time
import unittest
import os
import pytest
from datetime import datetime, timezone
from csvpath import CsvPaths
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.config import Config
from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu

INVOICES = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices"
ASSETS = (
    f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}assets"
)
MAR = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Mar"
JAN = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Jan"
FEB = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Feb"
INI = (
    f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}config{os.sep}ops-config.ini"
    if os.sep == "/"
    else f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}config{os.sep}ops-win-config.ini"
)
OINI = os.environ[Config.CSVPATH_CONFIG_FILE_ENV]
ACME = f"{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme"


class TestCsvPathsExamplesPathsOps(unittest.TestCase):

    PATHS = CsvPaths()

    @classmethod
    def setup_class(cls):
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = INI
        TestCsvPathsExamplesPathsOps.PATHS.config.add_to_config(
            "errors", "csvpath", "raise, collect, print"
        )
        TestCsvPathsExamplesPathsOps.PATHS.config.add_to_config(
            "errors", "csvpaths", "raise, collect, print"
        )
        #
        # five files, seven registrations. 1 second between first and rest. another
        # second between the rest and the last.
        #
        dirname = MAR
        TestCsvPathsExamplesPathsOps.PATHS.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":6/:8/:9/:filename"
        )
        time.sleep(0.25)

        dirname = JAN
        TestCsvPathsExamplesPathsOps.PATHS.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":6/:8/:9/:filename"
        )
        time.sleep(0.25)

        dirname = ACME
        TestCsvPathsExamplesPathsOps.PATHS.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":6/:8/:9/:filename"
        )
        time.sleep(0.25)

        dirname = FEB
        TestCsvPathsExamplesPathsOps.PATHS.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":6/:8/:9/:filename"
        )

    @classmethod
    def teardown_class(cls):
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = OINI

    def top(self):
        try:
            cfg = os.getenv(Config.CSVPATH_CONFIG_FILE_ENV)
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = INI
            paths = CsvPaths()
            paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
            paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
            paths.file_manager.add_named_file(
                name="acme-invoices",
                path=f"{INVOICES}{os.sep}2025{os.sep}Feb{os.sep}Acme_invoices_2025-01-25.csv",
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
            return paths, cfg
        except Exception as e:
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = OINI
            raise e

    def test_paths_can_run_paths_2(self):
        paths, cfg = self.top()
        try:
            #
            # run from the second csvpath in the named-paths group
            #
            paths.collect_paths(
                pathsname="$clean-invoices.csvpaths.step-two:from",
                filename="acme-invoices",
            )
            results = paths.results_manager.get_named_results("clean-invoices")
            assert results is not None
            assert len(results) == 2
        finally:
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = OINI

    def test_paths_can_run_paths_3(self):
        paths, cfg = self.top()
        try:
            #
            # run from the second csvpath in the named-paths group
            #
            paths.collect_paths(
                pathsname="$clean-invoices.csvpaths.step-two",
                filename="acme-invoices",
            )
            results = paths.results_manager.get_named_results("clean-invoices")
            assert results is not None
            assert len(results) == 1
        finally:
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = OINI
