import unittest
from csvpath.util.config import Config
from tests.skip_utility import SkipUtility as skut


class TestSkipUtility(unittest.TestCase):
    def _config(self, *, backend: str, value) -> Config:
        #
        # set() changes the in-memory config only; nothing is written
        #
        config = Config()
        config.set(section="testing", name=f"{backend}.skip", value=value)
        return config

    def test_no_means_enabled(self):
        for backend in skut.BACKENDS:
            config = self._config(backend=backend, value="no")
            assert skut.is_skipped(backend=backend, config=config) is False

    def test_yes_means_skipped(self):
        for backend in skut.BACKENDS:
            config = self._config(backend=backend, value="yes")
            assert skut.is_skipped(backend=backend, config=config) is True

    def test_case_and_whitespace_are_ignored(self):
        config = self._config(backend="s3", value=" No ")
        assert skut.is_skipped(backend="s3", config=config) is False
        config = self._config(backend="s3", value="YES")
        assert skut.is_skipped(backend="s3", config=config) is True

    def test_missing_flag_means_skipped(self):
        config = self._config(backend="gcs", value=None)
        assert skut.is_skipped(backend="gcs", config=config) is True

    def test_missing_section_means_skipped(self):
        #
        # an unloaded config has no sections at all, like a config file
        # with no [testing] section
        #
        config = Config(load=False)
        for backend in skut.BACKENDS:
            assert skut.is_skipped(backend=backend, config=config) is True

    def test_other_values_raise(self):
        for value in ["maybe", "true", "false", "0", ""]:
            config = self._config(backend="azure", value=value)
            with self.assertRaises(ValueError):
                skut.is_skipped(backend="azure", config=config)

    def test_bad_backend_raises(self):
        config = self._config(backend="s3", value="no")
        with self.assertRaises(ValueError):
            skut.is_skipped(backend="http", config=config)
        with self.assertRaises(ValueError):
            skut.is_skipped(backend="gs", config=config)
        with self.assertRaises(TypeError):
            skut.is_skipped(backend=None, config=config)

    def test_skip_unless_enabled_raises_skiptest(self):
        config = self._config(backend="sftp", value="yes")
        with self.assertRaises(unittest.SkipTest):
            skut.skip_unless_enabled(backend="sftp", config=config)

    def test_skip_unless_enabled_returns_when_enabled(self):
        config = self._config(backend="sftp", value="no")
        assert skut.skip_unless_enabled(backend="sftp", config=config) is None

    def test_default_config_is_the_active_config(self):
        #
        # with no config passed, the flags come from the config the run
        # points at. every config we test with sets these to yes, but the
        # point here is only that the call reads the same value Config() does
        #
        flag = Config().get(section="testing", name="s3.skip")
        expected = flag is None or f"{flag}".strip().lower() == "yes"
        assert skut.is_skipped(backend="s3") is expected
