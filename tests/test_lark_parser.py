import unittest
from lark import Lark
from lark.tree import Tree
from lark.lexer import Token
import os
from csvpath.matching.lark_parser import LarkParser


class TestLarkParser(unittest.TestCase):
    def test_lark_parser(self):
        LarkParser()
        dirpath = "tests/grammar/match"
        dlist = os.listdir(dirpath)
        base = dirpath
        tree = None
        i = 0
        e = 0
        for p in dlist:
            try:
                _ = p.lower()
                if _.endswith(".txt"):
                    path = os.path.join(base, p)
                    print(f"file: {path}")
                    with open(path) as f:
                        matchpart = f.read()
                        parser = Lark(
                            LarkParser.GRAMMAR, start="match", ambiguity="explicit"
                        )
                        tree = parser.parse(matchpart)
                        print(f"path {path} is:\n{tree.pretty()}")
            except Exception as ex:
                print(f"Error on {i}: {ex}")
                e += 1
        print("test_lark_parser: {i} examples parsed correctly")
        assert e == 0
