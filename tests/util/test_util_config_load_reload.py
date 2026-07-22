import os
import unittest
from csvpath.util.config import Config
from csvpath.util.nos import Nos

TMP_ROOT = os.path.join("tests", "util", "test_resources", "tmp", "config")


def _minimal_config_text(
    *,
    config_path,
    log_dir,
    cache_dir,
    archive_dir,
    transfers_dir,
    files_dir,
    csvpaths_dir,
) -> str:
    # a minimal but complete config: every section/key validate_config()
    # actually checks, all pointed at absolute, isolated temp paths so
    # nothing here ever touches assets/config/config.ini or repo-root
    # dirs like archive/, cache/, logs/.
    return f"""[errors]
csvpath = print
csvpaths = print

[logging]
csvpath = info
csvpaths = info
log_file = {log_dir}{os.sep}csvpath.log
log_files_to_keep = 10
log_file_size = 12800000

[config]
path = {config_path}
allow_var_sub = False
var_sub_source = env

[cache]
path = {cache_dir}

[results]
archive = {archive_dir}
transfers = {transfers_dir}

[inputs]
files = {files_dir}
csvpaths = {csvpaths_dir}
"""


class TestUtilConfigLoadReload(unittest.TestCase):
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

    def _paths_at(self, root):
        file_path = os.path.join(root, "config.ini")
        return {
            "file_path": file_path,
            "config_path_value": file_path,
            "log_dir": os.path.join(root, "logs"),
            "cache_dir": os.path.join(root, "cache"),
            "archive_dir": os.path.join(root, "archive"),
            "transfers_dir": os.path.join(root, "transfers"),
            "files_dir": os.path.join(root, "inputs", "named_files"),
            "csvpaths_dir": os.path.join(root, "inputs", "named_paths"),
        }

    def _write_valid_config_at(self, root, **overrides):
        os.makedirs(root, exist_ok=True)
        p = self._paths_at(root)
        p.update(overrides)
        text = _minimal_config_text(
            config_path=p["config_path_value"],
            log_dir=p["log_dir"],
            cache_dir=p["cache_dir"],
            archive_dir=p["archive_dir"],
            transfers_dir=p["transfers_dir"],
            files_dir=p["files_dir"],
            csvpaths_dir=p["csvpaths_dir"],
        )
        with open(p["file_path"], "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def _paths(self):
        return self._paths_at(self._test_dir)

    def _write_valid_config(self, **overrides):
        return self._write_valid_config_at(self._test_dir, **overrides)

    def _set_env(self, path):
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = path

    #
    # configpath resolution / env var fallback
    #

    def test_missing_config_path_creates_default_config_file(self):
        p = self._paths()
        self._set_env(p["file_path"])
        assert not os.path.exists(p["file_path"])
        c = Config()
        assert os.path.exists(p["file_path"])
        # _create_default_config() always resolves configpath to an
        # absolute, cwd-prefixed path when the original was relative --
        # see _create_default_config()'s "if not directory.strip()
        # .startswith(os.sep): directory = os.path.join(os.getcwd(),
        # directory)" -- so a relative env var value comes back absolute.
        assert c.configpath == os.path.abspath(p["file_path"])
        with open(p["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
        assert "XXXXXXXXXXX" not in content
        assert p["file_path"] in content

    def test_existing_valid_config_loads_real_values(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        assert c.configpath == p["file_path"]
        assert c.get(section="cache", name="path") == p["cache_dir"]

    def test_configpath_setter_is_a_noop_when_path_unchanged(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        c._config.set("cache", "path", "marker-value")
        c.configpath = p["file_path"]
        assert c._config.get("cache", "path") == "marker-value"

    def test_configpath_setter_none_falls_back_to_env_var(self):
        p1 = self._write_valid_config_at(os.path.join(self._test_dir, "one"))
        p2 = self._write_valid_config_at(os.path.join(self._test_dir, "two"))
        self._set_env(p2["file_path"])
        c = Config(load=False)
        assert c.configpath == p2["file_path"]
        c.configpath = p1["file_path"]
        assert c.configpath == p1["file_path"]
        c.configpath = None
        assert c.configpath == p2["file_path"]

    def test_config_path_property_is_an_alias_for_configpath(self):
        # config_path is a redundant, read-only alias for configpath,
        # the real member used throughout the class. Flagged as worth
        # removing -- see issue #207.
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        assert c.config_path == c.configpath == p["file_path"]

    #
    # load flag / reload / set_config_path_and_reload
    #

    def test_load_false_skips_all_file_io(self):
        p = self._paths()
        self._set_env(p["file_path"])
        c = Config(load=False)
        assert not os.path.exists(p["file_path"])
        assert c.sections == []

    def test_reload_forces_load_true_and_reads_the_file(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config(load=False)
        assert c.sections == []
        c.reload()
        assert "cache" in c.sections
        assert c.get(section="cache", name="path") == p["cache_dir"]

    def test_reload_picks_up_out_of_band_file_edits(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        assert c.get(section="cache", name="path") == p["cache_dir"]
        with open(p["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace(p["cache_dir"], f"{p['cache_dir']}-changed")
        with open(p["file_path"], "w", encoding="utf-8") as f:
            f.write(content)
        c.reload()
        assert c.get(section="cache", name="path") == f"{p['cache_dir']}-changed"

    def test_set_config_path_and_reload_switches_to_new_file(self):
        p1 = self._write_valid_config()
        d2 = os.path.join(self._test_dir, "other")
        p2 = self._write_valid_config_at(d2, cache_dir=os.path.join(d2, "cache2"))
        self._set_env(p1["file_path"])
        c = Config()
        assert c.get(section="cache", name="path") == p1["cache_dir"]
        c.set_config_path_and_reload(p2["file_path"])
        assert c.configpath == p2["file_path"]
        assert c.get(section="cache", name="path") == p2["cache_dir"]

    #
    # [config] path cycle detection (see the class docstring/comments on
    # config_path_cycle -- self-acknowledged as a paranoia safeguard)
    #

    def test_self_referential_config_path_does_not_cycle(self):
        # the normal, common case: [config] path points at the file's own
        # path (exactly what _write_valid_config produces by default)
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        assert c.config_path_cycle == 0

    def test_config_path_cycle_raises_past_the_limit(self):
        d1 = os.path.join(self._test_dir, "a")
        d2 = os.path.join(self._test_dir, "b")
        p2 = self._write_valid_config_at(d2)
        p1 = self._write_valid_config_at(d1, config_path_value=p2["file_path"])
        # rewrite b to point back at a, so loading either bounces forever
        self._write_valid_config_at(d2, config_path_value=p1["file_path"])
        self._set_env(p1["file_path"])
        with self.assertRaises(Exception):
            Config()

    #
    # _create_default_config's directory side effects. DEFAULT_CONFIG's
    # paths (archive, cache, logs/csvpath.log, inputs/named_files,
    # inputs/named_paths) are relative, so they resolve against the
    # process's current working directory, not against the config file's
    # own directory. We chdir into the isolated temp dir for this one
    # test so the real side effect lands somewhere safe to assert on and
    # clean up, instead of the repo root.
    #
    def test_create_default_config_creates_all_assured_directories(self):
        d = os.path.abspath(self._test_dir)
        config_path = os.path.join(d, "config.ini")
        self._set_env(config_path)
        original_cwd = os.getcwd()
        try:
            os.chdir(d)
            Config()
            assert os.path.exists(os.path.join(d, "config.ini"))
            assert os.path.exists(os.path.join(d, "archive"))
            assert os.path.exists(os.path.join(d, "cache"))
            assert os.path.exists(os.path.join(d, "transfers"))
            assert os.path.exists(os.path.join(d, "inputs", "named_files"))
            assert os.path.exists(os.path.join(d, "inputs", "named_paths"))
            assert os.path.exists(os.path.join(d, "logs"))
        finally:
            os.chdir(original_cwd)

    #
    # _assure_* methods reached via the normal load flow: logs, cache,
    # and inputs dirs get created on every load via validate_config().
    #

    def test_normal_load_creates_logs_cache_and_inputs_dirs(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        Config()
        assert os.path.exists(p["log_dir"])
        assert os.path.exists(p["cache_dir"])
        assert os.path.exists(p["files_dir"])
        assert os.path.exists(p["csvpaths_dir"])

    def test_normal_load_does_not_create_archive_or_transfers_dirs(self):
        # documents a real asymmetry: _assure_archive_path() and
        # _assure_transfer_root() are only ever called from
        # _create_default_config() (grep confirms zero other callers in
        # the package) -- not from validate_config()/refresh(). So for
        # an EXISTING config file, archive/transfers dirs are never
        # auto-created by Config itself; something else (e.g.
        # RunHomeMaker.get_run_dir()) must create them on demand.
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        Config()
        assert not os.path.exists(p["archive_dir"])
        assert not os.path.exists(p["transfers_dir"])

    #
    # _assure_archive_path / _assure_transfer_root called directly
    #

    def test_assure_archive_path_creates_the_directory(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        assert not os.path.exists(p["archive_dir"])
        c._assure_archive_path()
        assert os.path.exists(p["archive_dir"])

    def test_assure_archive_path_skips_remote_prefixes(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        c.archive_path = "s3://some-bucket/archive"
        c._assure_archive_path()  # should not raise or try to os.makedirs

    def test_assure_transfer_root_creates_the_directory(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        assert not os.path.exists(p["transfers_dir"])
        c._assure_transfer_root()
        assert os.path.exists(p["transfers_dir"])

    def test_assure_methods_are_a_noop_when_load_is_false(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config(load=False)
        c.archive_path = p["archive_dir"]
        c._assure_archive_path()
        assert not os.path.exists(p["archive_dir"])

    #
    # _assure_cache_path's extra behavior: remote path raises, use_cache
    # off skips creation
    #

    def test_assure_cache_path_raises_for_remote_path(self):
        from csvpath.util.config_exception import ConfigurationException

        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        c.cache_dir_path = "s3://bucket/cache"
        with self.assertRaises(ConfigurationException):
            c._assure_cache_path()

    #
    # _assure_config_file_path
    #

    def test_assure_config_file_path_does_not_touch_an_existing_file(self):
        p = self._write_valid_config()
        with open(p["file_path"], "r", encoding="utf-8") as f:
            original = f.read()
        c = Config(load=False)
        c.configpath = p["file_path"]
        c.load = True
        c._assure_config_file_path()
        with open(p["file_path"], "r", encoding="utf-8") as f:
            assert f.read() == original

    #
    # save_config
    #

    def test_save_config_persists_in_memory_changes(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        c._set("cache", "path", "changed-by-test")
        c.save_config()
        with open(p["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
        assert "changed-by-test" in content

    #
    # __str__ / sections / config_parser / config_env
    #

    def test_str_includes_configpath_and_content(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        s = str(c)
        assert p["file_path"] in s
        assert "cache" in s

    def test_sections_returns_section_names(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        assert set(["cache", "results", "inputs", "logging", "errors", "config"]) <= set(
            c.sections
        )

    def test_config_parser_returns_the_raw_config_parser(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        assert c.config_parser.get("cache", "path") == p["cache_dir"]

    def test_config_env_is_lazily_created_and_cached(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        first = c.config_env
        second = c.config_env
        assert first is second

    def test_config_env_setter_and_clear(self):
        p = self._write_valid_config()
        self._set_env(p["file_path"])
        c = Config()
        original = c.config_env
        c.config_env = None
        assert c.config_env is not original
        new_one = c.config_env
        c.clear_config_env()
        assert c.config_env is not new_one


if __name__ == "__main__":
    unittest.main()
