import unittest
from csvpath.csvpath import CsvPath
from csvpath.matching.functions.function_finder import FunctionFinder
from csvpath.matching.functions.function_factory import FunctionFactory

PATH = "tests/test_resources/test.csv"


class TestFunctionsExternals(unittest.TestCase):
    def test_function_externals1(self):
        print("")
        path = CsvPath()
        print(f"test: conifg at: {path.config.configpath}")
        FunctionFinder._add_function(
            path.matcher,
            FunctionFactory,
            "from csvpath.matching.functions.boolean.yes import Yes as sure",
        )
        path.parse(
            f"""
            ${PATH}[*]
            [
                @a = sure()
            ]"""
        )
        path.fast_forward()
        print(f"test_function_externals: path vars: {path.variables}")
        assert "a" in path.variables
        assert path.variables["a"] is True
        print(f"test_function_externals1: not mine: {FunctionFactory.NOT_MY_FUNCTION}")
        assert len(FunctionFactory.NOT_MY_FUNCTION) >= 1
        assert "sure" in FunctionFactory.NOT_MY_FUNCTION

    def test_function_externals2(self):
        print("")
        path = CsvPath()
        path.config.configpath = "tests/test_resources/config.ini"
        path.config.reload()
        assert path.config.function_imports is not None
        assert path.config.function_imports == "tests/test_resources/function.imports"
