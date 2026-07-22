import json
import os
import unittest
from csvpath.util.config_env import ConfigEnv
from csvpath.util.nos import Nos

TMP_DIR = os.path.join("tests", "util", "test_resources", "tmp", "config_env")
VAR_FILE = os.path.join(TMP_DIR, "vars.json")


class FakeConfig:
    def __init__(self, *, allow_var_sub=False, var_sub_source="env"):
        self._allow_var_sub = allow_var_sub
        self._var_sub_source = var_sub_source

    def get(self, *, section, name, default=None, string_parse=True):
        assert section == "config"
        if name == "var_sub_source":
            return self._var_sub_source
        if name == "allow_var_sub":
            return self._allow_var_sub
        return default


class TestUtilConfigEnv(unittest.TestCase):
    def setUp(self):
        nos = Nos(TMP_DIR)
        if not nos.dir_exists():
            nos.makedirs()
        self._saved_env = dict(os.environ)

    def tearDown(self):
        nos = Nos(TMP_DIR)
        if nos.dir_exists():
            nos.remove()
        os.environ.clear()
        os.environ.update(self._saved_env)

    #
    # construction
    #

    def test_init_raises_when_config_is_none(self):
        with self.assertRaises(ValueError):
            ConfigEnv(config=None)

    def test_config_property_returns_the_passed_config(self):
        fake = FakeConfig()
        env = ConfigEnv(config=fake)
        assert env.config is fake

    #
    # var_sub_source / allow_var_sub
    #

    def test_var_sub_source_delegates_to_config(self):
        fake = FakeConfig(var_sub_source="my-source.json")
        env = ConfigEnv(config=fake)
        assert env.var_sub_source == "my-source.json"

    def test_allow_var_sub_true_variants(self):
        for value in ["True", "true", "yes", "YES", "on", " On "]:
            fake = FakeConfig(allow_var_sub=value)
            env = ConfigEnv(config=fake)
            assert env.allow_var_sub is True, f"expected True for {value!r}"

    def test_allow_var_sub_false_for_unrecognized_string(self):
        fake = FakeConfig(allow_var_sub="nope")
        env = ConfigEnv(config=fake)
        assert bool(env.allow_var_sub) is False

    def test_allow_var_sub_returns_the_falsy_source_value_unchanged(self):
        # documents a real quirk: "a and str(a).strip().lower() in [...]"
        # short-circuits and returns "a" itself when "a" is falsy, not a
        # normalized False. So a None config value comes back as None,
        # not False, even though the property is typed "-> bool". Every
        # real caller only uses this in an "if" truthy context, so it is
        # not a functional bug, just a type-hint inaccuracy worth knowing.
        fake = FakeConfig(allow_var_sub=None)
        env = ConfigEnv(config=fake)
        assert env.allow_var_sub is None
        fake2 = FakeConfig(allow_var_sub=False)
        env2 = ConfigEnv(config=fake2)
        assert env2.allow_var_sub is False

    #
    # subs
    #

    def test_subs_is_empty_dict_when_var_sub_disallowed(self):
        fake = FakeConfig(allow_var_sub=False)
        env = ConfigEnv(config=fake)
        assert env.subs == {}

    def test_subs_is_os_environ_when_source_is_env(self):
        fake = FakeConfig(allow_var_sub="true", var_sub_source="env")
        env = ConfigEnv(config=fake)
        assert env.subs is os.environ

    def test_subs_is_env_property_when_source_is_a_file(self):
        fake = FakeConfig(allow_var_sub="true", var_sub_source=VAR_FILE)
        with open(VAR_FILE, "w", encoding="utf-8") as f:
            json.dump({"FOO": "bar"}, f)
        env = ConfigEnv(config=fake)
        assert env.subs == {"FOO": "bar"}

    #
    # env (JSON var file)
    #

    def test_env_creates_empty_file_when_missing(self):
        fake = FakeConfig(var_sub_source=VAR_FILE)
        env = ConfigEnv(config=fake)
        assert not os.path.exists(VAR_FILE)
        result = env.env
        assert result == {}
        assert os.path.exists(VAR_FILE)
        with open(VAR_FILE, "r", encoding="utf-8") as f:
            assert json.load(f) == {}

    def test_env_reads_existing_file_content(self):
        with open(VAR_FILE, "w", encoding="utf-8") as f:
            json.dump({"A": "1", "B": "2"}, f)
        fake = FakeConfig(var_sub_source=VAR_FILE)
        env = ConfigEnv(config=fake)
        assert env.env == {"A": "1", "B": "2"}

    def test_env_is_cached_until_refresh(self):
        with open(VAR_FILE, "w", encoding="utf-8") as f:
            json.dump({"A": "1"}, f)
        fake = FakeConfig(var_sub_source=VAR_FILE)
        env = ConfigEnv(config=fake)
        first = env.env
        with open(VAR_FILE, "w", encoding="utf-8") as f:
            json.dump({"A": "2"}, f)
        assert env.env == first
        env.refresh()
        assert env.env == {"A": "2"}

    def test_env_returns_none_on_invalid_json_without_raising(self):
        with open(VAR_FILE, "w", encoding="utf-8") as f:
            f.write("not valid json{{{")
        fake = FakeConfig(var_sub_source=VAR_FILE)
        env = ConfigEnv(config=fake)
        assert env.env is None

    #
    # write_env_file
    #

    def test_write_env_file_writes_given_dict(self):
        fake = FakeConfig(var_sub_source=VAR_FILE)
        env = ConfigEnv(config=fake)
        env.write_env_file({"X": "y"})
        with open(VAR_FILE, "r", encoding="utf-8") as f:
            assert json.load(f) == {"X": "y"}

    #
    # nos
    #

    def test_nos_reuses_the_same_instance_and_updates_path(self):
        fake = FakeConfig()
        env = ConfigEnv(config=fake)
        first = env.nos(VAR_FILE)
        assert first.path == VAR_FILE
        second = env.nos(TMP_DIR)
        assert second is first
        assert second.path == TMP_DIR

    #
    # get / get_from_env
    #

    def test_get_raises_when_name_is_none(self):
        fake = FakeConfig()
        env = ConfigEnv(config=fake)
        with self.assertRaises(ValueError):
            env.get(name=None)

    def test_get_returns_name_unchanged_when_not_all_uppercase(self):
        fake = FakeConfig(allow_var_sub="true", var_sub_source="env")
        env = ConfigEnv(config=fake)
        assert env.get(name="not_upper") == "not_upper"

    def test_get_returns_default_when_not_all_uppercase_and_default_given(self):
        fake = FakeConfig(allow_var_sub="true", var_sub_source="env")
        env = ConfigEnv(config=fake)
        assert env.get(name="not_upper", default="fallback") == "fallback"

    def test_get_returns_name_unchanged_when_var_sub_disallowed(self):
        fake = FakeConfig(allow_var_sub=False)
        env = ConfigEnv(config=fake)
        assert env.get(name="MY_VAR") == "MY_VAR"

    def test_get_from_env_source_reads_real_os_environ(self):
        os.environ["CSVPATH_TEST_CONFIG_ENV_VAR"] = "real-value"
        fake = FakeConfig(allow_var_sub="true", var_sub_source="env")
        env = ConfigEnv(config=fake)
        assert env.get(name="CSVPATH_TEST_CONFIG_ENV_VAR") == "real-value"

    def test_get_from_env_source_falls_back_to_default_when_not_set(self):
        os.environ.pop("CSVPATH_TEST_CONFIG_ENV_MISSING", None)
        fake = FakeConfig(allow_var_sub="true", var_sub_source="env")
        env = ConfigEnv(config=fake)
        assert env.get(name="CSVPATH_TEST_CONFIG_ENV_MISSING", default="dflt") == "dflt"

    def test_get_from_env_source_falls_back_to_name_when_not_set_and_no_default(self):
        os.environ.pop("CSVPATH_TEST_CONFIG_ENV_MISSING", None)
        fake = FakeConfig(allow_var_sub="true", var_sub_source="env")
        env = ConfigEnv(config=fake)
        assert env.get(name="CSVPATH_TEST_CONFIG_ENV_MISSING") == "CSVPATH_TEST_CONFIG_ENV_MISSING"

    def test_get_from_file_source_reads_json_var_file(self):
        with open(VAR_FILE, "w", encoding="utf-8") as f:
            json.dump({"MY_VAR": "file-value"}, f)
        fake = FakeConfig(allow_var_sub="true", var_sub_source=VAR_FILE)
        env = ConfigEnv(config=fake)
        assert env.get(name="MY_VAR") == "file-value"

    def test_get_from_file_source_falls_back_to_default_when_key_missing(self):
        with open(VAR_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        fake = FakeConfig(allow_var_sub="true", var_sub_source=VAR_FILE)
        env = ConfigEnv(config=fake)
        assert env.get(name="MISSING_VAR", default="dflt") == "dflt"


if __name__ == "__main__":
    unittest.main()
