import unittest
import os
from csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from csvpath.matching.functions.boolean.any import Any
from csvpath.matching.productions import Expression

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
EMPTY = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}empty.csv"


class TestCsvPathFunctionsAny(unittest.TestCase):
    def test_function_bare_any(self):
        path = CsvPath()

        matcher = Matcher(csvpath=path, data="[]")
        path.headers = ["a"]
        e = Expression(matcher)
        a = Any(matcher, "any")
        e.children.append(a)
        matcher.expressions.append(
            [
                e,
            ]
        )

        matcher.line = [None]
        a._bare_any()
        assert a.match is False

        matcher.line = [""]
        a._bare_any()
        assert a.match is False

        path.variables["b"] = ""
        a._bare_any()
        assert a.match is False

        path.variables["b"] = "b"
        a._bare_any()
        assert a.match is True

        matcher.line = ["a"]
        del path.variables["b"]
        a._bare_any()
        assert a.match is True

    def test_function_any_function1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3]
            [
                @frog = any(headers(), "Frog")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["frog"] is True

    def test_function_any_function2(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ description: this is a test! ~
            ~ name: harry ~
            ~ fish: bluefish and bass temp: hot ~

            ${PATH}[3]
            [
                @found = any()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["found"] is True

    def test_function_any_function3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3]
            [
                @v = any(variables())
                @frog = any(headers(), "Frog")
                @found = any()
                @slug = any("slug")
                @bear = any(headers(),"Bear")
                @me = any("True")
                @h = any(headers())
                @v2 = any(variables())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["frog"] is True
        assert path.variables["found"] is True
        assert path.variables["slug"] is False
        assert path.variables["bear"] is False
        assert path.variables["v"] is False
        assert path.variables["v2"] is True
        assert path.variables["h"] is True

    def test_function_any_function4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${EMPTY}[1-2]
            [
                @found = any(headers())
                @notfound = not(any(headers()))
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
        assert path.variables["found"] is False
        assert path.variables["notfound"] is True
