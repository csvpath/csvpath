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
        stmt = f"""
            ${PATH}[*]
            [
                @a = sure()
            ]"""
        imports = os.path.join("tests", "csvpath", "test_resources", "function.imports")
        path.config.set(section="functions", name="imports", value=imports)
        path.fast_forward(stmt)
        assert "a" in path.variables
        assert path.variables["a"] is True
        assert len(FunctionFactory.NOT_MY_FUNCTION) >= 1
        name = FunctionFactory.qname(matcher=path.matcher, name="sure")
        assert name in FunctionFactory.NOT_MY_FUNCTION

    def test_function_externals2(self):
        path = CsvPath()
        path.config.configpath = INI
        path.config.reload()
        assert path.config.function_imports is not None
        assert pathu.equal(path.config.function_imports, IMPORTS)
