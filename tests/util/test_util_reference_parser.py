import unittest
from csvpath.util.references.reference_parser import ReferenceParser


class TestUtilReferenceParser(unittest.TestCase):
    def test_ref_parser_1(self):
        ref = ReferenceParser("$many.results.2024-01-01_00-24-01:first")
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "results"
        assert ref.names[0] == "2024-01-01_00-24-01"
        assert ref.name_one_tokens[0] == "first"

        ref = ReferenceParser("$many.results.2024-01-01_.Firstest")
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "results"
        assert ref.names[0] == "2024-01-01_"
        assert ref.names[2] == "Firstest"

        ref = ReferenceParser("$many.results.2024-01-01_:first.Firstest")
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "results"
        assert ref.names[0] == "2024-01-01_"
        assert ref.name_one_tokens[0] == "first"
        assert ref.name_three == "Firstest"

        ref = ReferenceParser("$many#things.results.2024-01-01_:first.Secondist#third")
        assert ref.root_major == "many"
        assert ref.root_minor == "things"
        assert ref.datatype == "results"
        assert ref.names[0] == "2024-01-01_"
        assert ref.names[1] is None
        assert ref.names[2] == "Secondist"
        assert ref.names[3] == "third"

        ref = ReferenceParser("$many#things.results.2024-01-01_:first.third#fourth")
        assert ref.root_major == "many"
        assert ref.root_minor == "things"
        assert ref.datatype == "results"
        assert ref.names[0] == "2024-01-01_"
        assert ref.names[2] == "third"
        assert ref.names[3] == "fourth"

        #
        # csvpaths references
        #
        ref = ReferenceParser("$many.csvpaths.Sooo")
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "csvpaths"
        assert ref.name_one == "Sooo"
        assert ref.names[0] == "Sooo"
        assert ref.names[1] is None
        assert ref.names[2] is None
        assert ref.names[3] is None

        #
        # non-local variables references (a.k.a. "reference" references)
        #
        ref = ReferenceParser("$many#first.variables.avar.atrack")
        assert ref.root_major == "many"
        assert ref.root_minor == "first"
        assert ref.datatype == "variables"
        assert ref.names[0] == "avar"
        assert ref.names[2] == "atrack"
