import unittest
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.results_reference_finder import ResultsReferenceFinder
from csvpath import CsvPaths


class TestReferenceParser(unittest.TestCase):
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
