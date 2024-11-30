import unittest
import pytest
from csvpath.matching.productions import Expression
from csvpath.matching.util.exceptions import DataException, MatchException
from csvpath import CsvPath, CsvPaths
from csvpath.managers.results.result import Result
from csvpath.matching.matcher import Matcher


class RaisingChild:
    def __init__(self, ex: Exception):
        ex.datum = "some data"
        self.ex = ex

    def matches(self, *, skip=[]) -> bool:
        raise self.ex


class TestExpressions(unittest.TestCase):
    def test_expression_errors1(self):
        """creates an error that rises to the CsvPath"""
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise", "stop", "fail", "collect"]
        path.parse("$tests/test_resources/test.csv[*][yes()]")
        matcher = Matcher(csvpath=path, data="[yes()]")
        expr = Expression(matcher=matcher, name="dummy")
        de = DataException()
        child = RaisingChild(de)
        expr.children.append(child)
        matcher.expressions.append([expr, None])
        with pytest.raises(Exception):
            matcher.matches()
        assert "stop" in path.config.csvpath_errors_policy
        assert "fail" in path.config.csvpath_errors_policy
        assert path.errors
        assert len(path.errors) == 1
        assert not path.is_valid
        assert path.stopped is True

    def test_expression_errors2(self):
        """creates an error that is bubbled up to the CsvPaths's csvpath results"""
        paths = CsvPaths()
        path = paths.csvpath()
        path.config.csvpath_errors_policy = ["raise", "stop", "fail", "collect"]
        path.parse("$tests/test_resources/test.csv[*][yes()]")
        matcher = Matcher(csvpath=path, data="[yes()]")
        results = Result(
            csvpath=path,
            file_name="...",
            paths_name="......",
            run_index=1,
            run_time=None,
            run_dir="",
        )
        expr = Expression(matcher=matcher, name="dummy")
        de = DataException()
        child = RaisingChild(de)
        expr.children.append(child)
        matcher.expressions.append([expr, None])
        with pytest.raises(MatchException):
            matcher.matches()
        assert "stop" in path.config.csvpath_errors_policy
        assert "fail" in path.config.csvpath_errors_policy
        #
        # why was this here? we are adding path to result
        # result adds itself as error collector. path hands off
        # the error to its error_collector. why would we expect
        # path to have a copy?
        #
        # assert len(path.errors) == 1
        #
        # another misunderstanding. path is returning its
        # error collector's errors, so there is 1
        #
        # assert path._errors is None
        assert path._error_collector is not None
        assert not path.is_valid
        assert path.stopped is True
        assert results.has_errors() is True
        assert len(results.errors) == 1
