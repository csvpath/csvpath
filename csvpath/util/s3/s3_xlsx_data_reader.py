# pylint: disable=C0114
import os
import pylightxl as xl
import boto3
from smart_open import open
from ..file_readers import XlsxDataReader
from .s3_fingerprinter import S3Fingerprinter
from csvpath.util.box import Box
from csvpath.util.s3.s3_utils import S3Utils


class S3XlsxDataReader(XlsxDataReader):
    def next(self) -> list[str]:
        with self as file:
            db = xl.readxl(fn=file.source)
            if not self._sheet:
                self._sheet = db.ws_names[0]
            for row in db.ws(ws=self._sheet).rows:
                yield [f"{datum}" for datum in row]

    def load_if(self) -> None:
        if self.source is None:
            client = Box.STUFF.get("boto_s3_client")
            if client is None:
                client = S3Utils.make_client()
            try:
                self.source = open(
                    self._path, "rb", transport_params={"client": client}
                )
            except DeprecationWarning:
                ...

    def fingerprint(self) -> str:
        self.load_if()
        h = S3Fingerprinter().fingerprint(self._path)
        h = self.percent_encode(h)
        self.close()
        return h
