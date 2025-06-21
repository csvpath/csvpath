# pylint: disable=C0114
import os
import pylightxl as xl
from smart_open import open
from csvpath.util.box import Box
from csvpath.util.hasher import Hasher
from csvpath.util.file_readers import XlsxDataReader
from .azure_fingerprinter import AzureFingerprinter
from .azure_utils import AzureUtility


class AzureXlsxDataReader(XlsxDataReader):
    def next(self) -> list[str]:
        with self as file:
            db = xl.readxl(fn=file.source)
            if not self._sheet:
                self._sheet = db.ws_names[0]
            for row in db.ws(ws=self._sheet).rows:
                yield [f"{datum}" for datum in row]

    def load_if(self) -> None:
        if self.source is None:
            client = AzureUtility.make_client()
            try:
                #
                # xlsx are binary files, so always rb, regardless of self.mode. not
                # expecting problems.
                #
                self.source = open(self.path, "rb", transport_params={"client": client})
            except DeprecationWarning:
                ...

    def fingerprint(self) -> str:
        self.load_if()
        h = AzureFingerprinter().fingerprint(self.path)
        h = Hasher.percent_encode(h)
        self.close()
        return h
