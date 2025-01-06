# pylint: disable=C0114
import os
import pylightxl as xl
import boto3
from smart_open import open
from ..file_readers import XlsxDataReader
from .s3_fingerprinter import S3Fingerprinter


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
            session = boto3.Session(
                aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            )
            try:
                self.source = open(
                    self._path, "rb", transport_params={"client": session.client("s3")}
                )
            except DeprecationWarning:
                ...

    def fingerprint(self) -> str:
        self.load_if()
        h = S3Fingerprinter().fingerprint(self._path)
        h = self.percent_encode(h)
        self.close()
        return h
