import os
import unittest
from csvpath import CsvPath

UUIDS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}uuid.csv"


class TestCsvPathFunctionsEnv(unittest.TestCase):
    def test_function_env_1(self):
        ep = os.path.join("tests", "csvpath", "test_resources", "env.json")
        path = CsvPath()
        path.config.set(section="config", name="var_sub_source", value=ep)
        assert path.config.get(section="config", name="var_sub_source") == ep
        path.config.set(section="config", name="allow_var_sub", value="yes")
        path.parse(
            f"""~validation-mode: print, no-raise~${UUIDS}[1*][
            @t = env( "test" )
            ]"""
        )
        path.collect()
        assert path.variables["t"] == "bit bit bop"

    def test_function_env_2(self):
        path = CsvPath()
        path.config.set(section="config", name="var_sub_source", value="env")
        path.config.set(section="config", name="allow_var_sub", value="yes")
        os.environ["test"] = "bit boo bop"
        path.parse(
            f"""~validation-mode: print, no-raise~${UUIDS}[1*][
            @t = env( "test" )
            ]"""
        )
        path.collect()
        assert path.variables["t"] == "bit boo bop"
