import unittest
import pytest
from csvpath.matching.productions import Expression
from csvpath.matching.util.exceptions import DataException, MatchException
from csvpath import CsvPath, CsvPaths, CsvPathResult
from csvpath.matching.matcher import Matcher


class RaisingChild:
    def __init__(self, ex: Exception):
        print(f"RaisingChild.__init__: ex: {ex}")
        ex.datum = "some data"
        self.ex = ex

    def matches(self, *, skip=[]) -> bool:
        print(f"RaisingChild.matches: raising: {self.ex}")
        raise self.ex


class TestExpressions(unittest.TestCase):
    def test_expression_errors1(self):
        """creates an error that rises to the CsvPath"""
        path = CsvPath()
        matcher = Matcher(csvpath=path, data="[yes()]")
        expr = Expression(matcher=matcher, name="dummy")
        de = DataException()
        print(f"test_expression_errors1: de: {de}")
        child = RaisingChild(de)
        expr.children.append(child)
        with pytest.raises(DataException):
            expr.matches(skip=[])
        assert "stop" in path.config.CSVPATH_ON_ERROR
        assert "fail" in path.config.CSVPATH_ON_ERROR
        assert len(path.errors) == 1
        assert not path.is_valid
        assert path.stopped is True

    def test_expression_errors2(self):
        """creates an error that is bubbled up to the CsvPaths's csvpath results"""
        paths = CsvPaths()
        path = paths.csvpath()
        matcher = Matcher(csvpath=path, data="[yes()]")
        results = CsvPathResult(csvpath=path, file_name="...", paths_name="......")

        expr = Expression(matcher=matcher, name="dummy")
        de = DataException()
        print(f"test_expression_errors1: de: {de}")
        child = RaisingChild(de)
        expr.children.append(child)
        with pytest.raises(DataException):
            expr.matches(skip=[])
        assert "stop" in path.config.CSVPATH_ON_ERROR
        assert "fail" in path.config.CSVPATH_ON_ERROR
        assert len(path.errors) == 1
        print(f"path._errors: {path._errors}")
        assert path._errors is None
        assert path._error_collector is not None
        assert not path.is_valid
        assert path.stopped is True
        print(f"results: {results}, {results.errors}")
        assert results.has_errors()
        assert len(results.errors) == 1
