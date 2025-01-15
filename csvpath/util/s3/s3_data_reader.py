# pylint: disable=C0114
import csv
import importlib
import os
import boto3
from smart_open import open
from ..file_readers import CsvDataReader
from .s3_utils import S3Utils
from .s3_fingerprinter import S3Fingerprinter
from csvpath.util.box import Box


#
# TODO: next only works with CSV atm. need Excel.
#
class S3DataReader(CsvDataReader):
    def load_if(self) -> None:
        if self.source is None:
            client = Box.STUFF.get("boto_s3_client")
            if client is None:
                client = S3Utils.make_client()
                """
                session = boto3.Session(
                    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
                )
                client = session.client("s3")
                """
            try:
                self.source = open(self._path, "r", transport_params={"client": client})
            except DeprecationWarning:
                ...

    def next(self) -> list[str]:
        #
        # TODO: check if smart-open is in play and open w/o client is correct
        #
        with open(uri=self._path, mode="r") as file:
            reader = csv.reader(
                file, delimiter=self._delimiter, quotechar=self._quotechar
            )
            for line in reader:
                yield line

    def fingerprint(self) -> str:
        self.load_if()
        h = S3Fingerprinter().fingerprint(self._path)
        h = self.percent_encode(h)
        self.close()
        return h

    def exists(self, path: str) -> bool:
        bucket, key = S3Utils.path_to_parts(path)
        return S3Utils.exists(bucket, key)

    def remove(self, path: str) -> None:
        bucket, key = S3Utils.path_to_parts(path)
        return S3Utils.remove(bucket, key)

    def rename(self, path: str, new_path: str) -> None:
        bucket, key = S3Utils.path_to_parts(path)
        same_bucket, new_key = S3Utils.path_to_parts(new_path)
        if bucket != same_bucket:
            raise ValueError(
                "The old path and the new location must have the same bucket"
            )
        return S3Utils.rename(bucket, key, new_key)

    def read(self) -> str:
        with open(uri=self._path, mode="r", encoding="utf-8") as file:
            return file.read()

    def next_raw(self) -> str:
        with open(uri=self._path, mode="rb") as file:
            for line in file:
                yield line

    def file_info(self) -> dict[str, str | int | float]:
        # TODO: what can/should we provide here?
        return {}
