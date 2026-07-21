import os
import unittest
from csvpath.util.backend_check import BackendCheck
from csvpath.util.config import Config

AWS_KEYS = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
AZURE_KEYS = ["AZURE_STORAGE_CONNECTION_STRING"]
GCS_KEYS = ["GCS_CREDENTIALS_PATH"]


class TestUtilBackendCheck(unittest.TestCase):
    def setUp(self):
        self._saved = {}
        for k in AWS_KEYS + AZURE_KEYS + GCS_KEYS:
            self._saved[k] = os.environ.pop(k, None)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    #
    # s3_available()
    #
    def test_s3_available_true_when_both_env_vars_set(self):
        os.environ["AWS_ACCESS_KEY_ID"] = "id"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "secret"
        assert BackendCheck.s3_available(None) is True

    def test_s3_available_false_when_missing_either_var(self):
        assert BackendCheck.s3_available(None) is False
        os.environ["AWS_ACCESS_KEY_ID"] = "id"
        assert BackendCheck.s3_available(None) is False

    #
    # azure_available()
    #
    def test_azure_available_true_when_env_var_set(self):
        os.environ["AZURE_STORAGE_CONNECTION_STRING"] = "conn"
        assert BackendCheck.azure_available(None) is True

    def test_azure_available_false_when_missing(self):
        assert BackendCheck.azure_available(None) is False

    #
    # gcs_available()
    #
    def test_gcs_available_true_when_env_var_set(self):
        os.environ["GCS_CREDENTIALS_PATH"] = "/path/to/creds.json"
        assert BackendCheck.gcs_available(None) is True

    def test_gcs_available_false_when_missing(self):
        assert BackendCheck.gcs_available(None) is False

    #
    # sftp_available()
    #
    def test_sftp_available_true_with_real_looking_creds(self):
        config = Config()
        config.set(section="sftp", name="username", value="areal user")
        config.set(section="sftp", name="password", value="areal pass")
        assert BackendCheck.sftp_available(config) is True

    def test_sftp_available_false_with_placeholder_creds(self):
        # "username"/"password" are treated as the not-yet-configured
        # placeholder values, not real credentials
        config = Config()
        config.set(section="sftp", name="username", value="username")
        config.set(section="sftp", name="password", value="password")
        assert not BackendCheck.sftp_available(config)

    def test_sftp_available_false_when_missing(self):
        config = Config()
        config.set(section="sftp", name="username", value=None)
        config.set(section="sftp", name="password", value=None)
        assert not BackendCheck.sftp_available(config)
