import unittest
import os
from csvpath.util.var_utility import VarUtility
from csvpath import CsvPath
from csvpath import CsvPaths


class TestUtilVarUtil(unittest.TestCase):
    def test_var_util_1(self):
        assert VarUtility.isupper("ABDC_DEW")
        assert VarUtility.isupper("A2_DEW")
        assert VarUtility.isupper("A2")
        assert VarUtility.isupper("A")
        assert not VarUtility.isupper("1234455")
        assert not VarUtility.isupper("FishBat")
        assert not VarUtility.isupper("Fish Bat")
        assert not VarUtility.isupper("F_shBa1")
        assert not VarUtility.isupper("vishcat")

    def test_var_util_2(self):
        mdata = {}
        mdata["me"] = "hello world"
        variables = {}
        variables["time"] = 10
        assert (
            VarUtility.value_or_var_value(
                mdata=mdata, variables=variables, v="var|time"
            )
            == 10
        )
        assert (
            VarUtility.value_or_var_value(mdata=mdata, variables=variables, v="meta|me")
            == "hello world"
        )
        assert (
            VarUtility.value_or_var_value(mdata=mdata, variables=variables, v="a")
            == "a"
        )

    def test_var_util_3(self):
        mdata = {}
        mdata["me"] = "hello world"
        mdata["age"] = "4,500,000,000"
        variables = {}
        variables["time"] = 10
        pairs = VarUtility.get_value_pairs_from_value(
            metadata=mdata,
            variables=variables,
            value="t > var|time, me > meta|me, a > b, age>meta|age",
        )
        assert ("me", "hello world") in pairs

    def test_var_string_parse(self) -> None:
        config = CsvPath().config
        config.configpath = os.path.join(
            "tests", "util", "test_resources", "vars-config.ini"
        )

        server = config.get(section="inputs", name="files")
        assert server == "sftp://{DUMMY_SFTP_SERVER}:{DUMMY_SFTP_PORT}/a/b/c"

        os.environ["DUMMY_SFTP_SERVER"] = "otter"
        os.environ["DUMMY_SFTP_PORT"] = "4321"
        server = config.get(section="inputs", name="files")
        assert server == "sftp://otter:4321/a/b/c"

        path = os.path.join("tests", "util", "test_resources", "not-my-env.json")
        config.set(section="config", name="var_sub_source", value=path)
        config.clear_config_env()
        src = config.get(section="config", name="var_sub_source", string_parse=False)
        assert src == path

        server = config.get(section="inputs", name="files")
        assert server == "sftp://{DUMMY_SFTP_SERVER}:{DUMMY_SFTP_PORT}/a/b/c"

        config.set(
            section="config",
            name="var_sub_source",
            value=os.path.join("tests", "util", "test_resources", "my-env.json"),
        )
        config.clear_config_env()

        server = config.get(section="inputs", name="files")
        assert server == "sftp://otter:4321/a/b/c"

    def test_var_swaps(self) -> None:
        paths = CsvPaths()
        config = paths.config
        os.environ["CACHE_PATH"] = "fish"
        config.set(section="cache", name="path", value="CACHE_PATH")
        assert "CACHE_PATH" == config.get(section="cache", name="path", swaps=False)
        assert "fish" == config.get(section="cache", name="path")
        assert "fish" == config.get(name="CACHE_PATH")
        #
        # if we are looking at just the OS or env.json vars -- i.e. no section name -- we
        # ignore the swaps parameter.
        #
        assert "fish" == config.get(name="CACHE_PATH", swaps=False)
