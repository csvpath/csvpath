import logging
import unittest
import os
from csvpath.util.var_utility import VarUtility
from csvpath import CsvPath
from csvpath import CsvPaths
from csvpath.util.config import Config


class FakeConfigForGet:
    def __init__(self, *, value=None):
        self._value = value
        self.logger = logging.getLogger("fake-var-util-config")

    def get(self, *, section, name):
        return self._value


class TestUtilVarUtil(unittest.TestCase):
    def test_parse_var_value(self) -> None:
        c = Config()
        c.set(
            section="config",
            name="var_sub_source",
            value="tests/util/test_resources/my-env.json",
        )
        c.set(section="config", name="allow_var_sub", value="yes")
        assert (
            c.get(section="config", name="var_sub_source")
            == "tests/util/test_resources/my-env.json"
        )
        v = VarUtility.parse_var_value(c, "server", value="DUMMY_SFTP_SERVER")
        assert v == "otter"
        v = VarUtility.parse_var_value(
            c, "server", value="{DUMMY_SFTP_SERVER} eats fish"
        )
        assert v == "otter eats fish"

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

    #
    # get() -- env var / config / uppercase-swap resolution
    #

    def test_get_prefers_real_env_var_over_config(self):
        os.environ["CSVPATH_TEST_VARUTIL_ENV"] = "from-env"
        config = FakeConfigForGet(value="from-config")
        v = VarUtility.get(
            env="CSVPATH_TEST_VARUTIL_ENV", section="s", name="n", config=config
        )
        assert v == "from-env"

    def test_get_falls_back_to_config_when_env_not_set(self):
        os.environ.pop("CSVPATH_TEST_VARUTIL_MISSING", None)
        config = FakeConfigForGet(value="plain-value")
        v = VarUtility.get(
            env="CSVPATH_TEST_VARUTIL_MISSING", section="s", name="n", config=config
        )
        assert v == "plain-value"

    def test_get_returns_default_when_config_value_is_none(self):
        config = FakeConfigForGet(value=None)
        v = VarUtility.get(section="s", name="n", default="dflt", config=config)
        assert v == "dflt"

    def test_get_swaps_uppercase_config_value_for_real_env_var(self):
        os.environ["CSVPATH_TEST_VARUTIL_UPPER"] = "swapped"
        config = FakeConfigForGet(value="CSVPATH_TEST_VARUTIL_UPPER")
        v = VarUtility.get(section="s", name="n", config=config)
        assert v == "swapped"

    def test_get_returns_uppercase_value_unchanged_when_env_var_not_set(self):
        os.environ.pop("CSVPATH_TEST_VARUTIL_UPPER_UNSET", None)
        config = FakeConfigForGet(value="CSVPATH_TEST_VARUTIL_UPPER_UNSET")
        v = VarUtility.get(section="s", name="n", config=config)
        assert v == "CSVPATH_TEST_VARUTIL_UPPER_UNSET"

    def test_get_with_only_section_logs_warning_and_returns_default(self):
        config = FakeConfigForGet(value="ignored")
        v = VarUtility.get(section="s", default="dflt", config=config)
        assert v == "dflt"

    def test_get_with_only_name_logs_warning_and_returns_default(self):
        config = FakeConfigForGet(value="ignored")
        v = VarUtility.get(name="n", default="dflt", config=config)
        assert v == "dflt"

    #
    # isupper() edge cases
    #

    def test_isupper_none_and_non_string_are_false(self):
        assert VarUtility.isupper(None) is False
        assert VarUtility.isupper(123) is False

    def test_isupper_empty_string_is_false(self):
        assert VarUtility.isupper("") is False

    def test_isupper_all_digits_is_false(self):
        assert VarUtility.isupper("0123456789") is False

    def test_isupper_lone_underscore_is_true(self):
        # documents a real quirk: a lone "_" flips the internal allnum
        # flag to False without ever seeing a letter, so isupper("_")
        # returns True even though there is no actual uppercase content.
        assert VarUtility.isupper("_") is True

    def test_isupper_digits_and_underscore_no_letters_is_true(self):
        assert VarUtility.isupper("1_2") is True

    #
    # create_pair()
    #

    def test_create_pair_without_separator_returns_none_second_value(self):
        assert VarUtility.create_pair({}, {}, "onlykey") == ("onlykey", None)

    def test_create_pair_splits_and_strips_on_greater_than(self):
        assert VarUtility.create_pair({}, {}, " a  >  b ") == ("a", "b")

    def test_create_pair_resolves_var_reference_in_value(self):
        variables = {"time": 42}
        assert VarUtility.create_pair({}, variables, "t > var|time") == ("t", 42)

    #
    # get_value_pairs()
    #

    def test_get_value_pairs_returns_default_when_key_is_none(self):
        assert VarUtility.get_value_pairs(
            metadata={}, variables={}, key=None, default="dflt"
        ) == "dflt"

    def test_get_value_pairs_returns_default_when_key_missing_from_metadata(self):
        assert VarUtility.get_value_pairs(
            metadata={}, variables={}, key="missing", default="dflt"
        ) == "dflt"

    def test_get_value_pairs_reads_from_metadata_by_key(self):
        metadata = {"pairs": "a > b, c > d"}
        result = VarUtility.get_value_pairs(metadata=metadata, variables={}, key="pairs")
        assert result == [("a", "b"), ("c", "d")]

    #
    # get_value()
    #

    def test_get_value_returns_none_when_key_is_none(self):
        assert VarUtility.get_value({"a": "1"}, {}, None) is None

    def test_get_value_returns_none_when_key_missing(self):
        assert VarUtility.get_value({"a": "1"}, {}, "missing") is None

    def test_get_value_passes_string_through_var_or_meta_substitution(self):
        variables = {"time": 10}
        mdata = {"ref": "var|time"}
        assert VarUtility.get_value(mdata, variables, "ref") == 10

    def test_get_value_returns_non_string_values_unchanged(self):
        mdata = {"count": 5}
        assert VarUtility.get_value(mdata, {}, "count") == 5

    #
    # get_str()
    #

    def test_get_str_returns_stripped_string(self):
        mdata = {"name": "  hello  "}
        assert VarUtility.get_str(mdata, {}, "name") == "hello"

    def test_get_str_returns_none_for_literal_none_value(self):
        mdata = {"name": None}
        assert VarUtility.get_str(mdata, {}, "name") is None

    #
    # get_int() / to_int()
    #

    def test_get_int_parses_numeric_string(self):
        mdata = {"count": "42"}
        assert VarUtility.get_int(mdata, {}, "count") == 42

    def test_to_int_passes_through_real_int(self):
        assert VarUtility.to_int(7) == 7

    def test_to_int_returns_none_for_non_numeric_string(self):
        assert VarUtility.to_int("not-a-number") is None

    #
    # get_bool() / is_true()
    #

    def test_is_true_handles_bool_passthrough(self):
        assert VarUtility.is_true(True) is True
        assert VarUtility.is_true(False) is False

    def test_is_true_handles_zero_and_one(self):
        assert VarUtility.is_true(0) is False
        assert VarUtility.is_true(1) is True

    def test_is_true_handles_true_yes_strings_case_insensitive(self):
        assert VarUtility.is_true("TRUE") is True
        assert VarUtility.is_true("Yes") is True

    def test_is_true_handles_false_no_null_none_strings(self):
        assert VarUtility.is_true("false") is False
        assert VarUtility.is_true("no") is False
        assert VarUtility.is_true("null") is False
        assert VarUtility.is_true("none") is False

    def test_is_true_none_and_unrecognized_string_are_false(self):
        assert VarUtility.is_true(None) is False
        assert VarUtility.is_true("maybe") is False

    def test_get_bool_reads_from_metadata(self):
        mdata = {"flag": "yes"}
        assert VarUtility.get_bool(mdata, {}, "flag") is True
