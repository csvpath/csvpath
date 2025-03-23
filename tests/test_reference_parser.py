import unittest
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.results_reference_finder import ResultsReferenceFinder
from csvpath import CsvPaths


class TestReferenceParser(unittest.TestCase):
    def test_find_in_dir_names(self):
        paths = CsvPaths()
        last = True
        names = [
            "2024-03-03_01-01-03",
            "2024-03-04_01-05-01",
            "2024-03-04_03-51-07",
            "2024-03-04_03-40-16",
            "2024-03-04_05-25-10",
            "2024-03-05_01-08-15",
            "2024-03-06_01-02-27",
            "2024-03-07_01-10-09",
            "2024-03-04_07-21-10",
            "2024-03-04_00-11-24",
        ]
        refinder = ResultsReferenceFinder(paths)
        instance = "2024-03-03_01-"
        name = refinder._find_in_dir_names(instance, names, last)
        assert name == "2024-03-03_01-01-03"

        instance = "2024-03-04_"
        name = refinder._find_in_dir_names(instance, names, last)
        assert name == "2024-03-04_07-21-10"

        instance = "2024-03-"
        name = refinder._find_in_dir_names(instance, names, last)
        assert name == "2024-03-07_01-10-09"

        last = False
        instance = "2024-"
        name = refinder._find_in_dir_names(instance, names, last)
        assert name == "2024-03-03_01-01-03"

        instance = "2024-03-04"
        name = refinder._find_in_dir_names(instance, names, last)
        assert name == "2024-03-04_00-11-24"

    def test_ref_parser_1(self):
        ref = ReferenceParser("$many.csvpaths.first")
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "csvpaths"
        assert ref.names[0] == "first"
        assert ref.names[1] is None

        ref = ReferenceParser("$many#first.variables.avar.atrack")
        assert ref.root_major == "many"
        assert ref.root_minor == "first"
        assert ref.datatype == "variables"
        assert ref.names[0] == "avar"
        assert ref.names[2] == "atrack"

        ref = ReferenceParser("$many.results.2024-01-01_00-24-01.first")
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "results"
        assert ref.names[0] == "2024-01-01_00-24-01"
        assert ref.names[2] == "first"

        ref = ReferenceParser("$many.results.2024-01-01_*.first")
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "results"
        assert ref.names[0] == "2024-01-01_*"
        assert ref.names[2] == "first"

        ref = ReferenceParser("$many.results.2024-01-01_:first.first")
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "results"
        assert ref.names[0] == "2024-01-01_:first"
        assert ref.names[2] == "first"

        ref = ReferenceParser("$many#things.results.2024-01-01_:first.second#third")
        assert ref.root_major == "many"
        assert ref.root_minor == "things"
        assert ref.datatype == "results"
        assert ref.names[0] == "2024-01-01_:first"
        assert ref.names[1] is None
        assert ref.names[2] == "second"
        assert ref.names[3] == "third"

        ref = ReferenceParser(
            "$many#things.results.2024-01-01_:first#second.third#fourth"
        )
        assert ref.root_major == "many"
        assert ref.root_minor == "things"
        assert ref.datatype == "results"
        assert ref.names[0] == "2024-01-01_:first"
        assert ref.names[1] == "second"
        assert ref.names[2] == "third"
        assert ref.names[3] == "fourth"
