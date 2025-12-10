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
    #
    # note that there is no 1 test that checks that we will load external functions
    # for every external functions file encountered (e.g. in different projects);
    # however, in the aggregate, a full test run tests that capability at least 1x
    # because we use multiple functions.imports files across tests. not having a
    # specific test would only become a problem if we removed other tests or
    # simplified them all down to a single imports file -- both are not expected
    # to happen and would be their own problem.
    #
    def test_function_externals1(self):
        path = CsvPath()
        #
        # remove the sentinal to make sure we're loading this particular imports file
        # as-is this will be a problem for Server
        #
        if "externalfunctionsloaded" in FunctionFactory.NOT_MY_FUNCTION:
            del FunctionFactory.NOT_MY_FUNCTION["externalfunctionsloaded"]
        imports = os.path.join("tests", "csvpath", "test_resources", "function.imports")
        path.config.set(section="functions", name="imports", value=imports)
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
        assert pathu.equal(path.config.function_imports, IMPORTS)
