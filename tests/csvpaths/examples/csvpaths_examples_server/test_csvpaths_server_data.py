import unittest
import os
from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.util.references.results_reference_finder_2 import ResultsReferenceFinder2
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}test.csv"


class TestCsvPathsNewCsvPaths(unittest.TestCase):
    def test_no_data_1(self):
        paths = Builder().build()
        paths.paths_manager.add_named_paths(
            name="fable",
            paths=[
                "~id:first~$[*][no()]",
                "~id:second source-mode:preceeding~$[*][yes()]",
                #                """~id:lookup~$[1*][ insert( 2, "category", get($categories.variables.categories, #2) )]"""
            ],
        )
        paths.file_manager.add_named_file(name="fable", path=PATH)
        t = paths.collect_paths(filename="fable", pathsname="fable")
        assert t
        print(f"t is: {t}")
        assert t.startswith("$fable.")

    def test_no_data_2(self):
        # this was seen to break in flightpath server with:
        #   FileNotFoundError: [Errno 2] No such file or directory: 'archive/test/2025-10-01_20-02-02/capitalization/data.csv'
        paths = Builder().build()
        paths.config.add_to_config(
            section="errors", key="csvpath", value="print,fail,collect"
        )
        paths.config.add_to_config(
            section="errors", key="csvpaths", value="print,collect"
        )

        print(f"paths.config.configpath: {paths.config.configpath}")

        paths.paths_manager.add_named_paths_from_file(
            name="fable",
            file_path=os.path.join(
                "tests",
                "csvpaths",
                "examples",
                "csvpaths_examples_server",
                "paths.csvpaths",
            ),
        )
        paths.file_manager.add_named_file(
            name="fable",
            path=os.path.join(
                "tests", "csvpaths", "examples", "csvpaths_examples_server", "file.txt"
            ),
        )
        t = paths.collect_paths(filename="fable", pathsname="fable")

        assert t
        print(f"t is: {t}")
        assert t.startswith("$fable.")
        finder = ResultsReferenceFinder2(paths, reference=t)
        path = finder.resolve()[0]
        path = Nos(path).join("capitalization")
        path = Nos(path).join("data.csv")
        assert Nos(path).exists()
