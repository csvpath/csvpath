import unittest
import pytest
import os
import json
from datetime import datetime
from datetime import timedelta, timezone
from csvpath import CsvPaths
from csvpath.util.references.files_reference_finder_2 import FilesReferenceFinder2
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.reference_results import ReferenceResults


class TestCsvPathsReferencesFilesReferenceFinder2(unittest.TestCase):
    def _mani(self) -> list:
        two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        today = datetime.now(timezone.utc)
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        mani = []
        mani.append({})
        mani[0]["file"] = "inputs/named_files/test/a/b/c/data.csv"
        mani[0]["time"] = f"{two_days_ago}"
        mani.append({})
        mani[1]["file"] = "inputs/named_files/test/a/e/f/data.csv"
        mani[1]["time"] = f"{yesterday}"
        mani.append({})
        mani[2]["file"] = "inputs/named_files/test/a/i/j/data.csv"
        mani[2]["time"] = f"{today}"
        mani.append({})
        mani[3]["file"] = "inputs/named_files/test/a/k/l/data.csv"
        mani[3]["time"] = f"{tomorrow}"
        return (mani, two_days_ago, yesterday, today)

    def test_range_of_date_limited_paths(self):
        mani, two_days_ago, yesterday, today = self._mani()

        csvpaths = CsvPaths()
        rrange = "before"

        datestr = yesterday.strftime("%Y-%m-%d")
        reference = f"$test.files.a:{datestr}:{rrange}"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        #
        # yesterday at the current time
        #
        thedate = datetime.now(timezone.utc) - timedelta(days=1)
        thedate = thedate - timedelta(minutes=10)

        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_range_of_date_limited_paths(
            results=results, rrange=rrange, thedate=thedate, mani=mani
        )

        assert results.files is not None
        assert len(results.files) == 1
        assert results.files[0] == mani[0]["file"]

    def test_name_one_within_time_box(self):
        mani, two_days_ago, yesterday, today = self._mani()
        csvpaths = CsvPaths()
        rrange = "yesterday"
        reference = "$test.files.:yesterday"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        #
        # yesterday at the current time minus 10 min
        #
        thedate = datetime.now(timezone.utc) - timedelta(days=1)
        thedate = thedate - timedelta(minutes=10)

        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_name_one_within_time_box(
            results=results, rrange=rrange, thedate=thedate, mani=mani
        )

        assert results.files is not None
        assert len(results.files) == 1
        assert results.files[0] == mani[1]["file"]

    def test_do_range_of_name_one_1a(self):
        mani, two_days_ago, yesterday, today = self._mani()
        csvpaths = CsvPaths()

        #
        # before. before is exclusive.
        #
        reference = "$test.files.a/i:before"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_range_of_name_one(results=results, rrange="before", mani=mani)

        assert results.files is not None
        assert len(results.files) == 2
        assert results.files[0] == mani[0]["file"]

    def test_do_range_of_name_one_1b(self):
        mani, two_days_ago, yesterday, today = self._mani()
        csvpaths = CsvPaths()

        #
        # to. to is inclusive.
        #
        reference = "$test.files.a/i:to"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_range_of_name_one(results=results, rrange="to", mani=mani)

        assert results.files is not None
        assert len(results.files) == 3
        assert results.files[0] == mani[0]["file"]

        #
        # from. from is inclusive.
        #
        reference = "$test.files.a/i:from"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_range_of_name_one(results=results, rrange="from", mani=mani)

        assert results.files is not None
        assert len(results.files) == 2
        assert results.files[0] == mani[2]["file"]

        #
        # after. after is exclusive.
        #
        reference = "$test.files.a/i:after"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_range_of_name_one(results=results, rrange="after", mani=mani)

        assert results.files is not None
        assert len(results.files) == 1
        assert results.files[0] == mani[3]["file"]

    def test_do_range_of_name_one_2(self):
        mani, two_days_ago, yesterday, today = self._mani()
        csvpaths = CsvPaths()

        #
        # yesterday at the current time
        #
        thedate = datetime.now(timezone.utc) - timedelta(days=1)
        thedate = thedate - timedelta(minutes=10)

        #
        # by dates
        #
        datestr = yesterday.strftime("%Y-%m-%d")

        #
        # before and after are both inclusive.
        #
        reference = f"$test.files.{datestr}:before"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_range_of_name_one(results=results, rrange="before", mani=mani)

        assert results.files is not None
        assert len(results.files) == 1
        assert results.files[0] == mani[0]["file"]

        #
        # before and after are both inclusive.
        #
        reference = f"$test.files.{datestr}:after"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_range_of_name_one(results=results, rrange="after", mani=mani)

        assert results.files is not None
        assert len(results.files) == 3
        assert results.files[0] == mani[1]["file"]

        #
        # to and from are both inclusive.
        #
        reference = f"$test.files.{datestr}:to"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_range_of_name_one(results=results, rrange="to", mani=mani)

        assert results.files is not None
        assert len(results.files) == 1
        assert results.files[0] == mani[0]["file"]

        #
        # to and from are both inclusive.
        #
        reference = f"$test.files.{datestr}:from"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_range_of_name_one(results=results, rrange="from", mani=mani)

        assert results.files is not None
        assert len(results.files) == 3
        assert results.files[0] == mani[1]["file"]

    def test_path_if_name_one_1(self):
        mani, two_days_ago, yesterday, today = self._mani()
        csvpaths = CsvPaths()
        reference = "$test.files.a"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_path_if_name_one(
            results=results, tokens=ref.name_one_tokens, mani=mani
        )
        assert results.files is not None
        assert len(results.files) == 4
        assert results.files[0] == mani[0]["file"]

    def test_path_if_name_one_2(self):
        mani, two_days_ago, yesterday, today = self._mani()
        csvpaths = CsvPaths()
        y = yesterday.strftime("%Y-%m-%d")
        reference = f"$test.files.a:{y}"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_path_if_name_one(
            results=results, tokens=ref.name_one_tokens, mani=mani
        )
        assert results.files is not None
        assert len(results.files) == 1
        assert results.files[0] == mani[1]["file"]

    def test_date_if_name_one(self):
        mani, two_days_ago, yesterday, today = self._mani()
        csvpaths = CsvPaths()
        y = yesterday.strftime("%Y-%m-%d")
        reference = f"$test.files.{y}"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_date_if_name_one(
            results=results, tokens=ref.name_one_tokens, mani=mani
        )
        assert results.files is not None
        assert len(results.files) == 1
        assert results.files[0] == mani[1]["file"]

    def test_do_ordinal_if(self):
        mani, two_days_ago, yesterday, today = self._mani()
        csvpaths = CsvPaths()
        reference = "$test.files.:last"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)

        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_ordinal_if(
            results=results,
            tokens=ref.name_one_tokens,
            mani=mani,
            name_exists=results.ref.name_one is not None,
        )

        assert results.files is not None
        assert len(results.files) == 1
        assert results.files[0] == mani[3]["file"]

        reference = "$test.files.:2"
        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)

        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_ordinal_if(
            results=results,
            tokens=ref.name_one_tokens,
            mani=mani,
            name_exists=results.ref.name_one is not None,
        )

        assert results.files is not None
        assert len(results.files) == 1
        assert results.files[0] == mani[2]["file"]

    def test_range_if_name_three(self):
        #
        # based on test_range_of_date_limited_paths
        #
        mani, two_days_ago, yesterday, today = self._mani()

        csvpaths = CsvPaths()
        rrange = "from"

        ffromstr = two_days_ago.strftime("%Y-%m-%d")
        ttostr = today.strftime("%Y-%m-%d")
        reference = f"$test.files.a:{ffromstr}:from.{ttostr}:to"

        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)
        #
        # yesterday at the current time
        #
        thedate = datetime.now(timezone.utc) - timedelta(days=2)
        thedate = thedate - timedelta(minutes=10)

        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_range_of_date_limited_paths(
            results=results, rrange=rrange, thedate=thedate, mani=mani
        )

        assert results.files is not None
        assert len(results.files) == 4
        assert results.files[0] == mani[0]["file"]

        finder._do_range_if_name_three(
            results=results, tokens=results.ref.name_three_tokens, mani=mani
        )
        assert results.files is not None
        assert len(results.files) == 2
        assert results.files[0] == mani[0]["file"]

    def test_path_range_arrival_ordinal_if_name_three(self):
        #
        # based on test_range_of_date_limited_paths
        #
        mani, two_days_ago, yesterday, today = self._mani()

        csvpaths = CsvPaths()

        ttostr = today.strftime("%Y-%m-%d")
        reference = f"$test.files.a/e:from.{ttostr}:first"

        ref = ReferenceParser(string=reference)
        results = ReferenceResults(csvpaths=csvpaths, ref=ref)

        results.files.append("inputs/named_files/test/a/e/f/data.csv")
        results.files.append("inputs/named_files/test/a/i/j/data.csv")
        results.files.append("inputs/named_files/test/a/k/l/data.csv")

        finder = FilesReferenceFinder2(csvpaths=csvpaths, ref=ref)
        finder._do_arrival_ordinal_if_name_three(
            results=results, tokens=ref.name_three_tokens, mani=mani
        )

        assert results.files is not None
        assert len(results.files) == 1
        assert results.files[0] == mani[2]["file"]
