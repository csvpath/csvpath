import unittest
import os
from csvpath import CsvPath
from csvpath.matching.functions.function_finder import FunctionFinder
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.util.path_util import PathUtility as pathu

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
INI = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}config.ini"
IMPORTS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}function.imports"


class TestCsvPathFunctionsExternals(unittest.TestCase):
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
        path.config.configpath = INI
        path.config.reload()
        assert path.config.function_imports is not None
        print(f"test fun im: {path.config.function_imports}")
        print(f"test fun IM: {IMPORTS}")

        assert pathu.equal(path.config.function_imports, IMPORTS)
