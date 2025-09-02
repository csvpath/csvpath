import time
import unittest
import os
import pytest
from datetime import datetime, timezone
from csvpath import CsvPaths
from csvpath.util.references.results_reference_finder_2 import (
    ResultsReferenceFinder2 as ResultsReferenceFinder,
)

INVOICES = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices"
ASSETS = (
    f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}assets"
)
MAR = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Mar"
JAN = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Jan"
FEB = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme{os.sep}invoices{os.sep}2025{os.sep}Feb"
CSV = f"{INVOICES}{os.sep}2025{os.sep}Feb{os.sep}Acme_invoices_2025-01-25.csv"
ACME = f"{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_ops{os.sep}data{os.sep}customers{os.sep}acme"


class TestCsvPathsExamplesResultsOps_4(unittest.TestCase):
    
    def test_results_references_ops_4(cls):
        #
        # this test does not play well with others. clearing the archive
        # is required and isn't a big ask.
        #
        from tests.conftest import _clear_files
        _clear_files()
        
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

        d = datetime.now().astimezone(timezone.utc)
        datestr = d.strftime("%Y-%m-%d")
        #
        # count the number of existing results that will be found below. we need that number
        # in order to know how to point to a specific one of our own runs.
        #
        psi = 0
        ref = "$clean-invoices.results.acme/invoices/2025/Feb"
        try:
            finder = ResultsReferenceFinder(paths, reference=ref)
            results = finder.query()
            psi = len(results)
        except Exception:
            ...
            # this can fail if there are no results already because we are just running this one test.
            # that's not a big deal. it just means psi is 0.
        #
        # run the clean-invoices named-paths group against the bytes registered under
        # 'acme-invoices' that came from a file named 2025-02-invoices.csv on or after 2025-02-15
        #
        ref = f"$acme-invoices.files.Acme_invoices_2025-01-25_csv.{datestr}:after"
        #
        #
        #
        paths.collect_paths(pathsname="clean-invoices", filename=ref)
        results2 = paths.results_manager.get_named_results("clean-invoices")
        assert results2 is not None
        assert len(results2) == 3

        paths.clean()
        refpath = "$clean-invoices.csvpaths.step-two"
        reffile = f"$acme-invoices.files.Acme_invoices_2025-01-25_csv.{datestr}:after"
        paths.collect_paths(pathsname=refpath, filename=reffile)
        results3 = paths.results_manager.get_named_results("clean-invoices")
        assert results3 is not None
        assert len(results3) == 1

        #
        # prob
        #
        ref = f"$clean-invoices.results.acme/invoices/2025/Feb:{psi}"
        results4 = paths.results_manager.get_named_results(ref)
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

        ref = f"$clean-invoices.results.acme/invoices/2025/Feb:{psi}.step-three"
        result6 = paths.results_manager.get_named_results(ref)
        assert result6 is not None
        assert result6.identity_or_index == "step-three"
