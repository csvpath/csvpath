import uuid
import tempfile
from smart_open import open
from csvpath.util.hasher import Hasher
from csvpath import CsvPaths
from csvpath.util.box import Box
from .sftp_config import SftpConfig


class SftpFingerprinter:
    @property
    def _config(self):
        config = Box().get(Box.CSVPATHS_CONFIG)
        if config is None:
            #
            # if none, we may not be in a context closely tied to a CsvPaths.
            # e.g. FP. so we create a new csvpaths just for the config. it will
            # be identical to any csvpaths in this project unless the other
            # csvpaths were long-lived and had programmatic changes.
            #
            config = CsvPaths().config
            Box().add(Box.CSVPATHS_CONFIG, config)
        return config

    def fingerprint(self, path: str) -> str:
        config = self._config
        #
        #
        #
        c = SftpConfig(config)
        h = None
        try:
            f = c.sftp_client.file(path)
            h = f.check("sha256")
            c.client.close()
        except (OSError, FileNotFoundError):
            #
            # most servers do not support the check extension method so
            # we expect most of the time we'll get here. still, worth a
            # try.
            #
            try:
                with open(
                    path,
                    "rb",
                    transport_params={
                        "connect_kwargs": {
                            "username": c.username,
                            "password": c.password,
                        }
                    },
                ) as file:
                    with tempfile.NamedTemporaryFile() as to:
                        s = file.read()
                        to.write(s)
                        h = Hasher().hash(to)
            except Exception as e:
                print(f"SftpFingerprinter: second chance failed with {type(e)}: {e}")
        return h
