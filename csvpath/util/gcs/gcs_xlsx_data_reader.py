# pylint: disable=C0114
import os
import pylightxl as xl
from smart_open import open
from csvpath.util.box import Box
from csvpath.util.hasher import Hasher
from csvpath.util.file_readers import XlsxDataReader
from .gcs_fingerprinter import GcsFingerprinter
from .gcs_utils import GcsUtility


class GcsXlsxDataReader(XlsxDataReader):
    def next(self) -> list[str]:
        with self as file:
            db = xl.readxl(fn=file.source)
            if not self._sheet:
                self._sheet = db.ws_names[0]
            for row in db.ws(ws=self._sheet).rows:
                yield [f"{datum}" for datum in row]

    def load_if(self) -> None:
        if self.source is None:
            client = GcsUtility.make_client()
            try:
                # xlsx are binary, so always rb.
                self.source = open(self.path, "rb", transport_params={"client": client})
            except DeprecationWarning:
                ...

    def fingerprint(self) -> str:
        self.load_if()
        h = GcsFingerprinter().fingerprint(self.path)
        h = Hasher.percent_encode(h)
        self.close()
        return h
