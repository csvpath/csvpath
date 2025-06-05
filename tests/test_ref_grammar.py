import unittest
import pytest
from csvpath.util.references.reference_grammar import QueryParser


class TestReferenceGrammar(unittest.TestCase):
    def test_reference_grammar(self):
        #
        # these are reasonably comprehensive. keep in mind that we're not disallowing all the
        # no-go combinations. some of that is left to the reference parser to handle. e.g.
        # $myfile.files.a/b/c:first:last doesn't make a ton of sense. we *may* allow it. but
        # something like $myfile.files.abc123abc123abc123abc123abc123abc123abc123abc123:after
        # is a no-go. fingerprints are exact references, not points in time/sequence. the
        # grammar will allow it, tho, so up to the RP and finders to control for that.
        #

        parser = QueryParser()
        file_queries = [
            "$mydata.files.abc123abc123abc123abc123abc123abc123abc123abc123",  # fingerprint
            "$mydata.files.data/input-csv",  # path only
            "$mydata.files.:5",  # index only
            "$mydata.files.:5:from",  # index and another token
            "$mydata.files.data/test_csv:all",  # with token
            "$mydata.files.data/test_csv:2",  # path with index
            "$mydata.files.2024-01-15_14-30-45",  # timestamp only
            "$mydata.files.:2024-01-15_14-30-45",  # timestamp token
            "$mydata.files.:2024-01-15_14-30-45:to",  # timestamp token
            "$mydata.files.data/test_csv:first:last",  # multiple tokens
            "$mydata.files.data/test_csv.2024-01-15_14-30-45",  # path and timestamp
            "$mydata.files.data/test_csv.2024-01-15_14-30-45:from",  # path, timestamp, and token
            "$mydata.files.data/test_csv:2024-01-15_00-.2024-01-30:to",  # path, timestamps, and tokens
            "$mydata.files.data/test_csv:2024-01-15_00-:from.2024-01-30:to",  # path, timestamps, and tokens
            "$mydata.files.data/test_csv:2024-01-15_00-:from.:2024-01-30:to",  # path, timestamps, and tokens
        ]

        # Test results reference examples
        results_queries = [
            "$job.results.process_data",  # identity only
            "$job.results.:today",  # today reference
            "$job.results.:today:last",  # today last
            "$job.results.:today:last.process_data",  # today last with identity
            "$job.results.:today:3",  # today with index
            "$job.results.2024-01-15_14-30-45:last.process_data",  # datetime last identity
            "$job.results.analysis/monthly/:today:last.summary",  # path today last identity
            "$job.results.analysis/monthly/work/papers/:today:last.summary",  # path today last identity
            "$job.results.analysis/monthly/work/papers/:today:last.summary:unmatched",  # path today last identity
            "$job.results.analysis/data:2",  # path with index
            "$job.results.analysis/data:2.summary",  # path index identity
            "$job.results.analysis/data:2:yesterday",  # path with 2 tokens
        ]

        # Test csvpaths reference examples
        csvpaths_queries = [
            "$mypaths.csvpaths.apathname:to",
            "$mypaths.csvpaths.apathname:from",
            "$mypaths.csvpaths.apathname:to.anotherpath:from",
            "$mypaths.csvpaths.apathname:from.anotherpath:to",
            "$mypaths.csvpaths.3",
            "$mypaths.csvpaths.:3",
        ]

        # Test local reference examples
        local_queries = [
            "$.csvpath.line_number",
            "$.variables.City.Boston",
            "$.variables.people",
            "$.headers.firstnames",
            "$.metadata.id",
            "$.headers.6",
        ]

        # Test queries that should fail
        failing_queries = [
            "$mydata.files.data/input.csv.2024-01-15_14-30-45",  # Too many dots - should fail
        ]

        print("\n\nTesting File References:")
        for i, query in enumerate(file_queries):
            result = parser.parse(query)
            print(f"[{i}]✓ {query} -> {result}\n")

        print("\nTesting Results References:")
        for i, query in enumerate(results_queries):
            result = parser.parse(query)
            print(f"[{i}]✓ {query} -> {result}\n")

        print("\nTesting Csvpaths References:")
        for i, query in enumerate(csvpaths_queries):
            result = parser.parse(query)
            print(f"[{i}]✓ {query} -> {result}\n")

        print("\nTesting Local References:")
        for i, query in enumerate(local_queries):
            result = parser.parse(query)
            print(f"[{i}]✓ {query} -> {result}\n")

        print("\nTesting Queries That Should Fail:")
        for i, query in enumerate(failing_queries):
            with pytest.raises(ValueError):
                result = parser.parse(query)
                print(f"[{i}]✗ {query} -> SHOULD HAVE FAILED but got: {result}\n")
