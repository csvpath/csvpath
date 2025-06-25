import unittest
import pytest
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF
from csvpath.util.references.reference_grammar import QueryParser
from csvpath.util.references.reference_parser import ReferenceParser


class TestUtilReferenceGrammar(unittest.TestCase):
    def test_reference_grammar_files(self):
        #
        # these are reasonably comprehensive. keep in mind that we're not disallowing all the
        # no-go combinations. some of that is left to the reference parser to handle. e.g.
        # $myfile.files.a/b/c:first:last doesn't make a ton of sense. we *may* allow it. but
        # something like $myfile.files.abc123abc123abc123abc123abc123abc123abc123abc123:after
        # is a no-go. fingerprints are exact references, not points in time/sequence. the
        # grammar will allow it, tho, so up to the RP and finders to control for that.
        #
        parser = QueryParser(ref=ReferenceParser())
        file_queries = [
            "$mydata.files.abc123abc123abc123abc123abc123abc123abc123abc123",  # fingerprint
            "$mydata.files.data/input-csv",  # path only
            "$mydata.files.:5",  # index only
            "$mydata.files.:from:5",  # index and another token
            "$mydata.files.data/test_csv:all",  # with token
            "$mydata.files.data/test_csv:2",  # path with index
            "$mydata.files.2024-01-15_14-30-45",  # timestamp only
            "$mydata.files.data/test_csv:first",  # multiple tokens
            "$mydata.files.data/test_csv.2024-01-15_14-30-45",  # path and timestamp
            "$mydata.files.data/test_csv.2024-01-15_14-30-45:from",  # path, timestamp, and token
            "$mydata.files.data/test_csv:2024-01-15_00:from.2024-01-30:to",  # path, timestamps, and tokens
            "$mydata.files.data/test_csv:2024-01-15_00-:from.:2024-01-30:to",  # path, timestamps, and tokens
        ]
        for i, query in enumerate(file_queries):
            parser.parse(query)

    def test_reference_grammar_results(self):
        parser = QueryParser(ref=ReferenceParser())
        results_queries = [
            "$job.results.process_data",  # identity only
            "$job.results.:today",  # today reference
            "$job.results.:today:last",  # today last
            "$job.results.:today:last.process_data",  # today last with identity
            "$job.results.:today:3",  # today with index
            "$job.results.2024-01-15_14-30-45:last.process_data",  # datetime last identity
            "$job.results.analysis/monthly/:today:last.summary",  # path today last identity
            "$job.results.analysis/monthly/work/papers/:today:last.summary",  # path today last identity
            "$job.results.analysis/data:2",  # path with index
            "$job.results.analysis/data:2.summary",  # path index identity
        ]
        for i, query in enumerate(results_queries):
            parser.parse(query)

    def test_reference_grammar_results_2(self):
        q = "$job.results.analysis/monthly/work/papers/:today:last.summary:unmatched"  # path range ordinal identity
        parser = QueryParser(ref=ReferenceParser())
        parser.parse(q)

    def test_reference_grammar_csvpaths(self):
        parser = QueryParser(ref=ReferenceParser())
        csvpaths_queries = [
            "$mypaths.csvpaths.apathname:to",
            "$mypaths.csvpaths.apathname:from",
            "$mypaths.csvpaths.apathname:to.anotherpath:from",
            "$mypaths.csvpaths.apathname:from.anotherpath:to",
            "$mypaths.csvpaths.3",
            "$mypaths.csvpaths.:3",
        ]
        for i, query in enumerate(csvpaths_queries):
            parser.parse(query)

    def test_reference_grammar_local(self):
        parser = QueryParser(ref=ReferenceParser())
        parser.parse("$.csvpath.line_number")

        parser = QueryParser(ref=ReferenceParser())
        parser.parse("$.variables.City.Boston")

        parser = QueryParser(ref=ReferenceParser())
        parser.parse("$.variables.people")

        parser = QueryParser(ref=ReferenceParser())
        parser.parse("$.headers.firstnames")

        parser = QueryParser(ref=ReferenceParser())
        parser.parse("$.metadata.id")

        parser = QueryParser(ref=ReferenceParser())
        parser.parse("$.headers.6")

    def test_reference_grammar_fail(self):
        parser = QueryParser(ref=ReferenceParser())
        failing_queries = [
            "$mydata.files.data/input.csv.2024-01-15_14-30-45",  # Too many dots - should fail
            "$big_test.files.B:2025-:from:first",  # Too many tokens on name_one: date, from and first
            "$big_test.files.B:2025-:from.2025-",  # path + arrival + range name-three-date must end in range or range + ordinal
        ]
        for i, query in enumerate(failing_queries):
            with pytest.raises((ValueError, UnexpectedCharacters, UnexpectedEOF)):
                parser.parse(query)
