import unittest
import pytest
import os
from csvpath import CsvPaths
from csvpath.util.references.files_reference_finder_2 import FilesReferenceFinder2
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.reference_results import ReferenceResults


class TestCsvPathsReferencesFilesReferencees(unittest.TestCase):
    def test_csvpaths_references_files_path_date_ordinal(self) -> None:
        paths = CsvPaths()
        #
        # config.add_to_config doesn't save. paths.add_to_config does save. if
        # we save here we both screw up which ever ini is being used and also delete our test files
        #
        paths.config.add_to_config(
            "inputs", "files", "tests/csvpaths/test_resources/inputs/named_files"
        )
        ref = "$Cars.files.Autom:2025-:last"
        # ref = "$Cars.files.Autom:2025-:all"
        # ref = "$Cars.files.Autom"
        # ref = "$Cars.files.:all"
        finder = FilesReferenceFinder2(paths, reference=ref)
        results = finder.query()
        files = results.files
        assert len(files) == 1

    def test_csvpaths_references_files_extended(self) -> None:
        #
        # this test is in reponse to a concern from FlightPath: NOT A BUG > "Cannot be extended" with: 2024-:all.2025-
        # (should allow range and ordinal) — we only get prompted when the reference is correct so if you have a date
        # in name_three but no range or ordinal you aren’t complete and don’t get the prompt. It probably should not
        # say cannot be extended, but atm we don’t update the prompts till they change, so it can happen
        #
        paths = CsvPaths()
        #
        # config.add_to_config doesn't save. paths.add_to_config does save. if
        # we save here we both screw up which ever ini is being used and also delete our test files
        #
        paths.config.add_to_config(
            "inputs", "files", "tests/csvpaths/test_resources/inputs/named_files"
        )
        ref = "$Cars.files.2024-:all.2025-"
        ref = "$Cars.files.2024-:after.2025-:before"
        finder = FilesReferenceFinder2(paths, reference=ref)
        results = finder.query()
        files = results.files
        # files arrived after first day of 2025, so outside date range
        assert len(files) == 0

        ref = "$Cars.files.2024-:all.2025-:after"
        finder = FilesReferenceFinder2(paths, reference=ref)
        results = finder.query()
        files = results.files
        # this says all files from 2024 + 2025
        # files arrived after first day of 2025, so within date range
        assert len(files) == 3
