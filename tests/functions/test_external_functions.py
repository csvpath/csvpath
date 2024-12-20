import unittest
from csvpath import CsvPath
from csvpath.matching.functions.function_finder import FunctionFinder
from csvpath.matching.functions.function_factory import FunctionFactory

PATH = "tests/test_resources/test.csv"


class TestFunctionsExternals(unittest.TestCase):
    def test_function_externals1(self):
        path = CsvPath()
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
        assert "a" in path.variables
        assert path.variables["a"] is True
        assert len(FunctionFactory.NOT_MY_FUNCTION) >= 1
        assert "sure" in FunctionFactory.NOT_MY_FUNCTION

    def test_function_externals2(self):
        path = CsvPath()
        path.config.configpath = "tests/test_resources/config.ini"
        path.config.reload()
        assert path.config.function_imports is not None
        assert path.config.function_imports == "tests/test_resources/function.imports"
