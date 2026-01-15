import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException


PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.jsonl"
DOC = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}jsondoc-sm.jsonl"
DOC2 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}jsondoc-sm2.jsonl"
DOC3 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test2.jsonl"


class TestCsvPathFunctionsJSONPath(unittest.TestCase):
    def test_function_jsonpath1(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[7][
                print("headers: $.csvpath.headers")
                @s = jsonpath(#say, "$[*]")
            ]"""
        )
        path.fast_forward()
        assert "s" in path.variables
        s = path.variables["s"]
        assert len(s) == 2
        assert "growl" in s
        assert s["growl"] == "fooo"

    def test_function_jsonpath2(self):
        path = CsvPath()
        path.fast_forward(
            f"""
              ~ validation-mode:print, raise ~
              ${DOC}[*][
                print("firstname: $.headers.print_summary")
                @s = jsonpath(#print_summary, "$.[1]") ]
            """
        )
        assert "s" in path.variables
        s = path.variables["s"]
        assert s
        assert s == "b"
        assert path.headers == ["print_summary", "test"]

    def test_jsonl_1(self):
        path = CsvPath()
        path.fast_forward(
            f"""
              ~
                JSONL sets new headers for every line. if a line has a dict the
                headers are the keys in some indeterminate order. if the line has an
                array the headers the the values of the line in order.
              validation-mode:print, raise ~
              ${DOC2}[*][
                print("$.csvpath.headers")
                push("val", #0)
                push("name", header_name(0))
            ]
            """
        )
        print(f"vars: {path.variables}")
        assert path.variables["val"] == [["a", "b", "c"], "a", "fish"]
        assert path.variables["name"] == ["print_summary", "a", "animal"]

    def test_jsonl_2(self):
        path = CsvPath()
        path.fast_forward(
            f"""
              ~
              find what the system role says
              validation-mode:print, raise ~
              ${DOC3}[*][
                push("roles", jsonpath(#0, "$[?(@.role == 'system')].content") )
              ]
            """
        )
        print(f"vars: {path.variables}")
        assert "roles" in path.variables
        roles = path.variables["roles"]
        assert len(roles) == 5
        for i, _ in enumerate(roles):
            print(f"_[{i}]: {_}")
        assert (
            roles[0]
            == "You are a happy assistant that puts a positive spin on everything."
        )
        assert roles[2] == []

    def test_jsonl_3(self):
        path = CsvPath()
        path.fast_forward(
            f"""
              ~
              find the length of the conversations
              validation-mode:print, raise ~
              ${DOC3}[*][
                push("stmts", jsonpath(#0, "$.`len`") )
              ]
            """
        )
        print(f"vars: {path.variables}")
        assert "stmts" in path.variables
        stmts = path.variables["stmts"]
        assert len(stmts) == 5
        for i, _ in enumerate(stmts):
            print(f"_[{i}]: {_}")
        assert stmts[1] == 9

    def test_jsonl_4(self):
        path = CsvPath()
        path.fast_forward(
            f"""
              ~
              find the assistant's statement that has two parts and return the 2nd part
              find the length of the conversations
              validation-mode:print, raise ~
              ${DOC3}[*][
                push("stmts", jsonpath(#messages, "$[?(@.role == 'assistant' & @.content.`len` == 2)].content[1]") )
              ]
              """
        )
        print(f"vars: {path.variables}")
        assert "stmts" in path.variables
        stmts = path.variables["stmts"]
        assert len(stmts) == 5
        for i, _ in enumerate(stmts):
            print(f"_[{i}]: {_}")
