import unittest
from csvpath.util.references.reference_parser import ReferenceParser


class TestUtilReferenceParser(unittest.TestCase):
    def test_ref_parser_1(self):
        ref = ReferenceParser("$many.results.2024-01-01_00-24-01:first", csvpaths=None)
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "results"
        assert ref.name_one == "2024-01-01_00-24-01"
        assert ref.name_one_tokens[0] == "first"

        ref = ReferenceParser("$many.results.2024-01-01_.Firstest", csvpaths=None)
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "results"
        assert ref.name_one == "2024-01-01_"
        assert ref.name_three == "Firstest"

        ref = ReferenceParser("$many.results.2024-01-01_:first.Firstest", csvpaths=None)
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "results"
        assert ref.name_one == "2024-01-01_"
        assert ref.name_one_tokens[0] == "first"
        assert ref.name_three == "Firstest"

        ref = ReferenceParser("$many#things.results.2024-01-01_:first.Secondist#third", csvpaths=None)
        assert ref.root_major == "many"
        assert ref.root_minor == "things"
        assert ref.datatype == "results"
        assert ref.name_one == "2024-01-01_"
        assert ref.name_two is None
        assert ref.name_three == "Secondist"
        assert ref.name_four == "third"

        ref = ReferenceParser("$many#things.results.2024-01-01_:first.third#fourth", csvpaths=None)
        assert ref.root_major == "many"
        assert ref.root_minor == "things"
        assert ref.datatype == "results"
        assert ref.name_one == "2024-01-01_"
        assert ref.name_three == "third"
        assert ref.name_four == "fourth"

        #
        # csvpaths references
        #
        ref = ReferenceParser("$many.csvpaths.Sooo", csvpaths=None)
        assert ref.root_major == "many"
        assert ref.root_minor is None
        assert ref.datatype == "csvpaths"
        assert ref.name_one == "Sooo"
        assert ref.name_one == "Sooo"
        assert ref.name_two is None
        assert ref.name_three is None
        assert ref.name_four is None

        #
        # non-local variables references (a.k.a. "reference" references)
        #
        ref = ReferenceParser("$many#first.variables.avar.atrack", csvpaths=None)
        assert ref.root_major == "many"
        assert ref.root_minor == "first"
        assert ref.datatype == "variables"
        assert ref.name_one == "avar"
        assert ref.name_three == "atrack"
