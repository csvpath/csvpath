# pylint: disable=C0114
import os
import pylightxl as xl
from smart_open import open
from csvpath.util.box import Box
from csvpath.util.hasher import Hasher
from ..file_readers import XlsxDataReader
from .sftp_fingerprinter import SftpFingerprinter
from .sftp_config import SftpConfig


class SftpXlsxDataReader(XlsxDataReader):
    def next(self) -> list[str]:
        with self as file:
            db = xl.readxl(fn=file.source)
            if not self._sheet:
                self._sheet = db.ws_names[0]
            for row in db.ws(ws=self._sheet).rows:
                yield [f"{datum}" for datum in row]

    def load_if(self) -> None:
        if self.source is None:
            config = Box().get(Box.CSVPATHS_CONFIG)
            c = SftpConfig(config)
            self.source = open(
                self.path,
                # always binary
                "rb",
                transport_params={
                    "connect_kwargs": {
                        "username": c.username,
                        "password": c.password,
                        "look_for_keys": False,
                        "allow_agent": False,
                    }
                },
            )

    def fingerprint(self) -> str:
        self.load_if()
        h = SftpFingerprinter().fingerprint(self.path)
        h = Hasher.percent_encode(h)
        self.close()
        return h
