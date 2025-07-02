# pylint: disable=C0114
import csv
import os
import boto3
from smart_open import open
from ..file_readers import CsvDataReader
from .s3_utils import S3Utils
from .s3_fingerprinter import S3Fingerprinter
from csvpath.util.box import Box
from csvpath.util.hasher import Hasher

#
# TODO: next only works with CSV atm. need Excel.
#


class S3DataReader(CsvDataReader):
    def load_if(self) -> None:
        if self.source is None:
            client = S3Utils.make_client()
            try:
                self.source = open(
                    self.path, self.mode, transport_params={"client": client}
                )
            except DeprecationWarning:
                ...

    def next(self) -> list[str]:
        try:
            with open(
                uri=self.path,
                mode="r",
                encoding=self.encoding,
                transport_params={"client": S3Utils.make_client()},
            ) as file:
                reader = csv.reader(
                    file, delimiter=self._delimiter, quotechar=self._quotechar
                )
                for line in reader:
                    yield line
        except DeprecationWarning:
            ...

    def fingerprint(self) -> str:
        self.load_if()
        h = S3Fingerprinter().fingerprint(self.path)
        h = Hasher.percent_encode(h)
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

    #
    # TODO: are read() and raw_read() incorrect because not S3, like open() above?
    #
    def read(self) -> str:
        with open(uri=self.path, mode=self.mode, encoding=self.encoding) as file:
            return file.read()

    #
    # no csv interpretation. used in FileManager.
    #
    def next_raw(self) -> str:
        if self.mode.find("b") > -1:
            with open(
                uri=self.path,
                mode=self.mode,
                transport_params={"client": S3Utils.make_client()},
            ) as file:
                for line in file:
                    yield line
        else:
            with open(
                uri=self.path,
                mode=self.mode,
                encoding=self.encoding,
                transport_params={"client": S3Utils.make_client()},
            ) as file:
                for line in file:
                    yield line
