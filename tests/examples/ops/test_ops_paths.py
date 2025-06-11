import time
import unittest
import os
import pytest
from datetime import datetime, timezone
from csvpath import CsvPaths
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.files_reference_finder_2 import (
    FilesReferenceFinder2 as FilesReferenceFinder,
)

# from csvpath.util.references.files_reference_finder import FilesReferenceFinder
from csvpath.util.config import Config
from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu

INVOICES = "tests/examples/ops/data/customers/acme/invoices"
ASSETS = "tests/examples/ops/assets"


class TestPathsOps(unittest.TestCase):

    PATHS = CsvPaths()

    @classmethod
    def setup_class(cls):
        os.environ[
            Config.CSVPATH_CONFIG_FILE_ENV
        ] = "tests/examples/ops/config/ops-config.ini"
        TestPathsOps.PATHS.config.add_to_config(
            "errors", "csvpath", "raise, collect, print"
        )
        TestPathsOps.PATHS.config.add_to_config(
            "errors", "csvpaths", "raise, collect, print"
        )
        #
        # five files, seven registrations. 1 second between first and rest. another
        # second between the rest and the last.
        #
        dirname = "tests/examples/ops/data/customers/acme/invoices/2025/Mar"
        TestPathsOps.PATHS.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":5/:7/:8/:filename"
        )
        time.sleep(0.25)

        dirname = "tests/examples/ops/data/customers/acme/invoices/2025/Jan"
        TestPathsOps.PATHS.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":5/:7/:8/:filename"
        )
        time.sleep(0.25)

        dirname = "tests/examples/ops/data/customers/acme"
        TestPathsOps.PATHS.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":5/:7/:8/:filename"
        )
        time.sleep(0.25)

        dirname = "tests/examples/ops/data/customers/acme/invoices/2025/Feb"
        TestPathsOps.PATHS.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":5/:7/:8/:filename"
        )

    @classmethod
    def teardown_class(cls):
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = "config/config.ini"

    def top(self):
        try:
            cfg = os.getenv(Config.CSVPATH_CONFIG_FILE_ENV)
            os.environ[
                Config.CSVPATH_CONFIG_FILE_ENV
            ] = "tests/examples/ops/config/ops-config.ini"
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
                template=":5/invoices/:7/:8/:run_dir",
            )
            return paths, cfg
        except Exception as e:
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = "config/config.ini"
            raise e

    """
    def test_references_can_run_1(self):
        paths, cfg = self.top()
        try:
            # most basic run; tho, it will use the paths template, so the signature doesn't
            # change but it's not completely stock.
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
            #
            # nos does resep itself.
            #
            # we don't know which file is last from the filesystem so we cannot just say
            # arc should exist. we can read the manifest to see what last should be.
            #
            # nos = Nos(arc)
            # assert nos.dir_exists()
        finally:
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = "config/config.ini"
    """

    def test_references_can_run_paths_2(self):
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
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = "config/config.ini"

    def test_references_can_run_paths_3(self):
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
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = "config/config.ini"
