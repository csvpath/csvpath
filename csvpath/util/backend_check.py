import os
from csvpath.util.config import Config


#
# just checks for credentials, not reachability or ability to log in.
#
class BackendCheck:
    @classmethod
    def s3_available(self, config: Config) -> bool:
        if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
            return False
        return True

    @classmethod
    def azure_available(self, config: Config) -> bool:
        if not os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
            return False
        return True

    @classmethod
    def gcs_available(self, config: Config) -> bool:
        if not os.getenv("GCS_CREDENTIALS_PATH"):
            return False
        return True

    @classmethod
    def sftp_available(self, config: Config) -> bool:
        u = config.get(section="sftp", name="username")
        p = config.get(section="sftp", name="password")
        return u and u != "username" and p and p != "password"
