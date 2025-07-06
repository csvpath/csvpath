import unittest
import os
from csvpath import CsvPaths

from csvpath.util.references.files_reference_finder_2 import (
    FilesReferenceFinder2 as FilesReferenceFinder,
)


FILES = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_flightpath{os.sep}{'windows' if os.sep=='\\' else 'posix'}_references"


class TestCsvPathsExamplesFlightPathRefs(unittest.TestCase):
    def test_flightpath_1(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.config.add_to_config("inputs", "files", FILES)
        ref = "$test.files.tms_bars4:all"
        finder = FilesReferenceFinder(paths, reference=ref)
        res = finder.resolve()
        assert res is not None
        assert isinstance(res, list)
        assert len(res) == 2

    def test_flightpath_2(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.config.add_to_config("inputs", "files", FILES)
        ref = "$test.files.2025-05-10:before"
        finder = FilesReferenceFinder(paths, reference=ref)
        res = finder.resolve()
        assert res
        assert isinstance(res, list)
        assert len(res) == 4

    def test_flightpath_3(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.config.add_to_config("inputs", "files", FILES)
        ref = "$test.files.tms_bars4:all.2025-05-10:before"
        finder = FilesReferenceFinder(paths, reference=ref)
        res = finder.resolve()
        assert res
        assert isinstance(res, list)
        assert len(res) == 1

    def test_flightpath_4(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.config.add_to_config("inputs", "files", FILES)
        ref = "$test.files.2025-05-10_02-00-00:before"
        finder = FilesReferenceFinder(paths, reference=ref)
        res = finder.resolve()
        assert res
        assert isinstance(res, list)
        assert len(res) == 5
