import os
import unittest
from csvpath import CsvPath

UUIDS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}uuid.csv"


class TestCsvPathFunctionsRuntime(unittest.TestCase):
    def test_function_runtime_1(self):
        path = CsvPath().parse(
            f"""${UUIDS}[1*][
            @v = runtime( "line_number" )
            push( "runtime", @v )
            ]"""
        )
        path.collect()
        r = path.variables["runtime"]
        print(f"vars: r: {r}")
        assert r == [1, 2, 3]

    def test_function_runtime_2(self):
        path = CsvPath().parse(
            f"""~id:me~${UUIDS}[1*][
            @v = runtime( "identity" )
            push( "runtime", @v )
            ]"""
        )
        path.collect()
        r = path.variables["runtime"]
        print(f"vars: r: {r}")
        assert r == ["me", "me", "me"]
