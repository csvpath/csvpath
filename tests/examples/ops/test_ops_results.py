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
from csvpath.util.references.results_reference_finder_2 import (
    ResultsReferenceFinder2 as ResultsReferenceFinder,
)

# from csvpath.util.references.files_reference_finder import FilesReferenceFinder
from csvpath.util.config import Config
from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu

INVOICES = "tests/examples/ops/data/customers/acme/invoices"
ASSETS = "tests/examples/ops/assets"


class TestResultsOps(unittest.TestCase):

    PATHS = CsvPaths()

    @classmethod
    def setup_class(cls):
        os.environ[
            Config.CSVPATH_CONFIG_FILE_ENV
        ] = "tests/examples/ops/config/ops-config.ini"
        TestResultsOps.PATHS.config.add_to_config(
            "errors", "csvpath", "raise, collect, print"
        )
        TestResultsOps.PATHS.config.add_to_config(
            "errors", "csvpaths", "raise, collect, print"
        )
        #
        # five files, seven registrations. 1 second between first and rest. another
        # second between the rest and the last.
        #
        dirname = "tests/examples/ops/data/customers/acme/invoices/2025/Mar"
        TestResultsOps.PATHS.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":5/:7/:8/:filename"
        )
        time.sleep(0.25)

        dirname = "tests/examples/ops/data/customers/acme/invoices/2025/Jan"
        TestResultsOps.PATHS.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":5/:7/:8/:filename"
        )
        time.sleep(0.25)

        dirname = "tests/examples/ops/data/customers/acme"
        TestResultsOps.PATHS.file_manager.add_named_files_from_dir(
            dirname, name="invoices", template=":5/:7/:8/:filename"
        )
        time.sleep(0.25)

        dirname = "tests/examples/ops/data/customers/acme/invoices/2025/Feb"
        TestResultsOps.PATHS.file_manager.add_named_files_from_dir(
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

    def test_references_results_can_run_4(self):
        paths, cfg = self.top()
        try:
            #
            # run the clean-invoices named-paths group against the 4th version of
            # bytes registered as 'acme-invoices'
            #
            paths.collect_paths(
                pathsname="clean-invoices", filename="$acme-invoices.files.:3"
            )
            #
            # we don't know for sure the filesystem order so using 3 is not straightforward.
            # we can get the month from the run dir_path and use that.
            #
            rmani = paths.results_manager.get_last_named_result(
                name="clean-invoices"
            ).run_manifest
            run_home = rmani["run_home"]
            month = os.path.dirname(run_home)
            month = os.path.basename(month)
            #
            # test for results mani has "named_file_path": "...Acme_invoices_2025-01-27.csv...",
            #
            # ---------------- keep with above so they can be run singley
            #
            # run the clean-invoices named-paths group against the data generated in the last run
            # by the second step -- its data.csv. i don't need to deal with the template because i'm
            # identifying the run using 'today:last'.
            #
            paths.collect_paths(
                pathsname="clean-invoices",
                filename=f"$clean-invoices.results.acme/invoices/2025/{month}/:today:last.step-two",
            )
        finally:
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = "config/config.ini"

    def test_references_results_can_run_6(self):
        paths, cfg = self.top()
        try:
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
        finally:
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = "config/config.ini"

    def test_references_get_results(self):
        paths, cfg = self.top()
        d = datetime.now().astimezone(timezone.utc)
        datestr = d.strftime("%Y-%m-%d")
        try:
            #
            # count the number of existing results that will be found below. we need that number
            # in order to know how to pointer to a specific one of our own runs.
            #
            psi = 0
            try:
                results = ResultsReferenceFinder(paths).resolve(
                    "$clean-invoices.results.acme/invoices/2025/Feb"
                )
                psi = len(results)
            except Exception:
                ...
                # this can fail if there are no results already because we are just running this one test.
                # that's not a big deal. it just means psi is 0.
            #
            # run the clean-invoices named-paths group against the bytes registered under
            # 'acme-invoices' that came from a file named 2025-02-invoices.csv on or after 2025-02-15
            #
            paths.collect_paths(
                pathsname="clean-invoices",
                filename=f"$acme-invoices.files.Acme_invoices_2025-01-25_csv.{datestr}:after",
            )
            results2 = paths.results_manager.get_named_results("clean-invoices")
            assert results2 is not None
            assert len(results2) == 3

            paths.clean()
            paths.collect_paths(
                pathsname="$clean-invoices.csvpaths.step-two",
                filename=f"$acme-invoices.files.Acme_invoices_2025-01-25_csv.{datestr}:after",
            )
            results3 = paths.results_manager.get_named_results("clean-invoices")
            assert results3 is not None
            assert len(results3) == 1

            #
            # prob
            #
            results4 = paths.results_manager.get_named_results(
                f"$clean-invoices.results.acme/invoices/2025/Feb:{psi}"
            )
            assert results4 is not None
            assert len(results4) == 3

            #
            # we're running just step-two so we expect 1 result
            #
            psi1 = psi + 1
            ref = f"$clean-invoices.results.acme/invoices/2025/Feb:{psi1}"
            results5 = paths.results_manager.get_named_results(ref)
            assert results5 is not None
            assert len(results5) == 1

            result6 = paths.results_manager.get_named_results(
                f"$clean-invoices.results.acme/invoices/2025/Feb:{psi}.step-three"
            )
            assert result6 is not None
            assert result6.identity_or_index == "step-three"

        finally:
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = "config/config.ini"
