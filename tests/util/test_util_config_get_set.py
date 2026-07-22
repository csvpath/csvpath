import json
import os
import unittest
from csvpath.util.config import Config
from csvpath.util.config_exception import ConfigurationException
from csvpath.util.nos import Nos

TMP_ROOT = os.path.join("tests", "util", "test_resources", "tmp", "config_get_set")


def _minimal_config_text(
    *,
    config_path,
    log_dir,
    cache_dir,
    archive_dir,
    transfers_dir,
    files_dir,
    csvpaths_dir,
    csvpath_errors="print",
    csvpaths_errors="print",
    csvpath_log="info",
    csvpaths_log="info",
    log_file_line=None,
    allow_var_sub="False",
    var_sub_source="env",
) -> str:
    if log_file_line is None:
        log_file_line = f"log_file = {log_dir}{os.sep}csvpath.log"
    return f"""[errors]
csvpath = {csvpath_errors}
csvpaths = {csvpaths_errors}

[logging]
csvpath = {csvpath_log}
csvpaths = {csvpaths_log}
{log_file_line}
log_files_to_keep = 10
log_file_size = 12800000

[config]
path = {config_path}
allow_var_sub = {allow_var_sub}
var_sub_source = {var_sub_source}

[cache]
path = {cache_dir}

[results]
archive = {archive_dir}
transfers = {transfers_dir}

[inputs]
files = {files_dir}
csvpaths = {csvpaths_dir}
"""


class TestUtilConfigGetSet(unittest.TestCase):
    def setUp(self):
        self._saved_env = os.environ.get(Config.CSVPATH_CONFIG_FILE_ENV)
        self._test_dir = os.path.join(TMP_ROOT, self._testMethodName)
        nos = Nos(self._test_dir)
        if nos.dir_exists():
            nos.remove()
        nos.makedirs()

    def tearDown(self):
        if self._saved_env is None:
            os.environ.pop(Config.CSVPATH_CONFIG_FILE_ENV, None)
        else:
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = self._saved_env
        nos = Nos(self._test_dir)
        if nos.dir_exists():
            nos.remove()

    def _paths(self, **overrides):
        root = self._test_dir
        file_path = os.path.join(root, "config.ini")
        p = {
            "file_path": file_path,
            "config_path": file_path,
            "log_dir": os.path.join(root, "logs"),
            "cache_dir": os.path.join(root, "cache"),
            "archive_dir": os.path.join(root, "archive"),
            "transfers_dir": os.path.join(root, "transfers"),
            "files_dir": os.path.join(root, "inputs", "named_files"),
            "csvpaths_dir": os.path.join(root, "inputs", "named_paths"),
        }
        p.update(overrides)
        return p

    def _write_config(self, **overrides):
        p = self._paths(**overrides)
        text_kwargs = {
            k: v
            for k, v in p.items()
            if k
            in (
                "config_path",
                "log_dir",
                "cache_dir",
                "archive_dir",
                "transfers_dir",
                "files_dir",
                "csvpaths_dir",
            )
        }
        for k in (
            "csvpath_errors",
            "csvpaths_errors",
            "csvpath_log",
            "csvpaths_log",
            "log_file_line",
            "allow_var_sub",
            "var_sub_source",
        ):
            if k in overrides:
                text_kwargs[k] = overrides[k]
        text = _minimal_config_text(**text_kwargs)
        with open(p["file_path"], "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def _config(self, **overrides):
        p = self._write_config(**overrides)
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = p["file_path"]
        return Config(), p

    #
    # _get / get
    #

    def test_get_raises_when_name_is_none(self):
        c, _ = self._config()
        with self.assertRaises(ConfigurationException):
            c.get(name=None)

    def test_get_without_section_delegates_to_config_env(self):
        c, _ = self._config(allow_var_sub="True", var_sub_source="env")
        os.environ["CSVPATH_TEST_CONFIGGET_ENV"] = "env-value"
        assert c.get(name="CSVPATH_TEST_CONFIGGET_ENV") == "env-value"

    def test_get_returns_value_for_existing_key(self):
        c, p = self._config()
        assert c.get(section="cache", name="path") == p["cache_dir"]

    def test_get_returns_default_for_missing_key(self):
        c, _ = self._config()
        assert c.get(section="cache", name="nope", default="dflt") == "dflt"

    def test_get_splits_comma_separated_values_into_a_list(self):
        c, _ = self._config()
        c.set(section="listeners", name="groups", value="a,b,c")
        assert c.get(section="listeners", name="groups") == ["a", "b", "c"]

    def test_get_swaps_uppercase_value_for_real_env_var_by_default(self):
        c, _ = self._config(allow_var_sub="True")
        os.environ["CSVPATH_TEST_CONFIGGET_SWAP"] = "swapped-value"
        c.set(section="cache", name="path", value="CSVPATH_TEST_CONFIGGET_SWAP")
        assert c.get(section="cache", name="path") == "swapped-value"

    def test_get_does_not_swap_when_swaps_is_false(self):
        c, _ = self._config()
        os.environ["CSVPATH_TEST_CONFIGGET_SWAP2"] = "swapped-value"
        c.set(section="cache", name="path", value="CSVPATH_TEST_CONFIGGET_SWAP2")
        assert (
            c.get(section="cache", name="path", swaps=False)
            == "CSVPATH_TEST_CONFIGGET_SWAP2"
        )

    def test_get_substitutes_curly_brace_tokens_from_json_var_file(self):
        var_file = os.path.join(self._test_dir, "vars.json")
        with open(var_file, "w", encoding="utf-8") as f:
            json.dump({"NAME": "World"}, f)
        c, _ = self._config(allow_var_sub="True", var_sub_source=var_file)
        c.set(section="cache", name="path", value="Hello {NAME}")
        assert c.get(section="cache", name="path") == "Hello World"

    def test_get_string_parse_false_skips_token_substitution(self):
        var_file = os.path.join(self._test_dir, "vars.json")
        with open(var_file, "w", encoding="utf-8") as f:
            json.dump({"NAME": "World"}, f)
        c, _ = self._config(allow_var_sub="True", var_sub_source=var_file)
        c.set(section="cache", name="path", value="Hello {NAME}")
        assert (
            c.get(section="cache", name="path", string_parse=False) == "Hello {NAME}"
        )

    def test_get_returns_default_when_internal_config_parser_is_missing(self):
        # defensive branch: _get() raises ConfigurationException if
        # self._config is ever None
        c, _ = self._config()
        c._config = None
        with self.assertRaises(ConfigurationException):
            c.get(section="cache", name="path")

    #
    # set / _set / add_to_config
    #

    def test_set_creates_a_new_section(self):
        c, _ = self._config()
        assert "newsection" not in c.sections
        c.set(section="newsection", name="key", value="val")
        assert "newsection" in c.sections
        assert c.get(section="newsection", name="key") == "val"

    def test_set_joins_list_values_into_a_comma_string(self):
        c, _ = self._config()
        c.set(section="listeners", name="groups", value=["a", "b", "c"])
        assert c._config.get("listeners", "groups") == "a,b,c"

    def test_set_on_config_section_resets_config_env_cache(self):
        c, _ = self._config()
        first = c.config_env
        c.set(section="config", name="allow_var_sub", value="True")
        assert c.config_env is not first

    def test_set_on_other_section_does_not_reset_config_env_cache(self):
        c, _ = self._config()
        first = c.config_env
        c.set(section="cache", name="path", value="somewhere")
        assert c.config_env is first

    def test_add_to_config_stores_value_and_refreshes(self):
        c, _ = self._config()
        c.add_to_config("cache", "path", "new-cache-dir")
        assert c.get(section="cache", name="path") == "new-cache-dir"

    def test_add_to_config_stores_none_as_empty_string(self):
        c, _ = self._config()
        c.add_to_config("newsection", "key", None)
        assert c._config.get("newsection", "key") == ""

    #
    # validate_config() raise paths
    #

    def test_validate_config_raises_for_bad_csvpath_errors_policy(self):
        p = self._paths()
        os.makedirs(self._test_dir, exist_ok=True)
        with self.assertRaises(ConfigurationException):
            self._config(csvpath_errors="not-a-real-policy")

    def test_validate_config_raises_for_bad_log_level(self):
        with self.assertRaises(ConfigurationException):
            self._config(csvpath_log="not-a-real-level")

    def test_validate_config_raises_for_missing_log_file(self):
        with self.assertRaises(ConfigurationException):
            self._config(log_file_line="")

    #
    # simple properties
    #

    def test_cache_dir_path_get_and_set(self):
        c, p = self._config()
        assert c.cache_dir_path == p["cache_dir"]
        c.cache_dir_path = "/elsewhere/cache"
        assert c.cache_dir_path == "/elsewhere/cache"

    def test_transfer_root_get_and_set(self):
        c, p = self._config()
        assert c.transfer_root == p["transfers_dir"]
        c.transfer_root = "/elsewhere/transfers"
        assert c.transfer_root == "/elsewhere/transfers"

    def test_archive_path_get_and_set(self):
        c, p = self._config()
        assert c.archive_path == p["archive_dir"]
        c.archive_path = "/elsewhere/archive"
        assert c.archive_path == "/elsewhere/archive"

    def test_archive_name_returns_basename_when_path_has_a_separator(self):
        c, _ = self._config()
        c.archive_path = os.path.join(self._test_dir, "myarchive")
        assert c.archive_name == "myarchive"

    def test_archive_name_returns_whole_value_when_no_separator(self):
        c, _ = self._config()
        c.archive_path = "justaname"
        assert c.archive_name == "justaname"

    def test_inputs_files_path_get_and_set(self):
        c, p = self._config()
        assert c.inputs_files_path == p["files_dir"]
        c.inputs_files_path = "/elsewhere/files"
        assert c.inputs_files_path == "/elsewhere/files"

    def test_inputs_csvpaths_path_get_and_set(self):
        c, p = self._config()
        assert c.inputs_csvpaths_path == p["csvpaths_dir"]
        c.inputs_csvpaths_path = "/elsewhere/csvpaths"
        assert c.inputs_csvpaths_path == "/elsewhere/csvpaths"

    def test_function_imports_default_and_set(self):
        c, _ = self._config()
        assert c.function_imports == ""
        c.function_imports = "/some/imports.txt"
        assert c.function_imports == "/some/imports.txt"

    def test_csvpath_errors_policy_getter_always_returns_a_list(self):
        c, _ = self._config()
        assert c.csvpath_errors_policy == ["print"]

    def test_csvpath_errors_policy_setter_wraps_a_single_string(self):
        c, _ = self._config()
        c.csvpath_errors_policy = "collect"
        assert c.csvpath_errors_policy == ["collect"]

    def test_csvpath_errors_policy_setter_accepts_a_list(self):
        c, _ = self._config()
        c.csvpath_errors_policy = ["collect", "print"]
        assert c.csvpath_errors_policy == ["collect", "print"]

    def test_csvpaths_errors_policy_getter_always_returns_a_list(self):
        c, _ = self._config()
        assert c.csvpaths_errors_policy == ["print"]

    def test_csvpath_log_level_get_and_set(self):
        c, _ = self._config()
        assert c.csvpath_log_level == "info"
        c.csvpath_log_level = "debug"
        assert c.csvpath_log_level == "debug"

    def test_csvpaths_log_level_get_and_set(self):
        c, _ = self._config()
        assert c.csvpaths_log_level == "info"
        c.csvpaths_log_level = "warn"
        assert c.csvpaths_log_level == "warn"

    def test_log_file_get_and_set(self):
        c, p = self._config()
        assert c.log_file == p["log_dir"] + os.sep + "csvpath.log"
        c.log_file = "/elsewhere/csvpath.log"
        assert c.log_file == "/elsewhere/csvpath.log"

    def test_log_files_to_keep_get_and_set(self):
        c, _ = self._config()
        assert c.log_files_to_keep == 10
        c.log_files_to_keep = 25
        assert c.log_files_to_keep == 25

    def test_log_files_to_keep_setter_coerces_bad_value_to_default(self):
        c, _ = self._config()
        c.log_files_to_keep = "not-a-number"
        assert c.log_files_to_keep == 10

    def test_log_files_to_keep_getter_coerces_bad_stored_value_to_default(self):
        c, _ = self._config()
        c._config.set("logging", "log_files_to_keep", "not-a-number")
        assert c.log_files_to_keep == 10

    def test_log_file_size_get_and_set(self):
        c, _ = self._config()
        assert c.log_file_size == 12800000
        c.log_file_size = 999
        assert c.log_file_size == 999

    def test_log_file_size_setter_coerces_bad_value_to_default(self):
        c, _ = self._config()
        c.log_file_size = None
        assert c.log_file_size == 12800000

    def test_archive_sep_defaults_to_os_sep_for_local_path(self):
        c, _ = self._config()
        c.archive_path = os.path.join(self._test_dir, "archive")
        assert c.archive_sep == os.sep

    def test_archive_sep_is_forward_slash_for_remote_path(self):
        c, _ = self._config()
        c.archive_path = "s3://bucket/archive"
        assert c.archive_sep == "/"

    def test_files_sep_defaults_to_os_sep_for_local_path(self):
        c, _ = self._config()
        c.inputs_files_path = os.path.join(self._test_dir, "files")
        assert c.files_sep == os.sep

    def test_files_sep_is_forward_slash_for_remote_path(self):
        c, _ = self._config()
        c.inputs_files_path = "sftp://host/files"
        assert c.files_sep == "/"

    def test_csvpaths_sep_is_broken_and_always_raises(self):
        # documents a real bug (issue #204): csvpaths_sep references
        # self._assure_inputs_csvpaths_path (a bound method object)
        # instead of self.inputs_csvpaths_path (the property), so it
        # always raises AttributeError. Zero callers anywhere in the
        # package. Compare with the working archive_sep/files_sep
        # properties tested above.
        c, _ = self._config()
        with self.assertRaises(AttributeError):
            c.csvpaths_sep

    def test_halt_on_unmatched_file_fingerprints_halt(self):
        c, _ = self._config()
        c.set(section="inputs", name="on_unmatched_file_fingerprints", value="halt")
        assert c.halt_on_unmatched_file_fingerprints() is True

    def test_halt_on_unmatched_file_fingerprints_continue(self):
        c, _ = self._config()
        c.set(
            section="inputs", name="on_unmatched_file_fingerprints", value="continue"
        )
        assert c.halt_on_unmatched_file_fingerprints() is False

    def test_halt_on_unmatched_file_fingerprints_unrecognized_is_none(self):
        c, _ = self._config()
        c.set(section="inputs", name="on_unmatched_file_fingerprints", value="huh")
        assert c.halt_on_unmatched_file_fingerprints() is None

    #
    # additional_listeners
    #

    def test_additional_listeners_collects_matching_group_entries(self):
        c, _ = self._config()
        c.set(section="listeners", name="groups", value="default")
        c.set(
            section="listeners",
            name="default.file",
            value="from a.b import C",
        )
        result = c.additional_listeners("file")
        assert result == ["from a.b import C"]

    def test_additional_listeners_across_multiple_groups(self):
        c, _ = self._config()
        c.set(section="listeners", name="groups", value="g1,g2")
        c.set(section="listeners", name="g1.file", value="from a import A")
        c.set(section="listeners", name="g2.file", value="from b import B")
        result = c.additional_listeners("file")
        assert result == ["from a import A", "from b import B"]

    def test_additional_listeners_skips_groups_with_no_matching_entry(self):
        c, _ = self._config()
        c.set(section="listeners", name="groups", value="g1,g2")
        c.set(section="listeners", name="g1.file", value="from a import A")
        result = c.additional_listeners("file")
        assert result == ["from a import A"]

    def test_additional_listeners_returns_empty_list_when_no_groups(self):
        c, _ = self._config()
        assert c.additional_listeners("file") == []


if __name__ == "__main__":
    unittest.main()
