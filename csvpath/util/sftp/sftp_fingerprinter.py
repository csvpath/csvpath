import uuid
import tempfile
from smart_open import open
from csvpath.util.hasher import Hasher
from csvpath.util.box import Box
from .sftp_config import SftpConfig


class SftpFingerprinter:
    def fingerprint(self, path: str) -> str:
        box = Box()
        config = box.get(Box.CSVPATHS_CONFIG)
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
