# pylint: disable=C0114

import os
import boto3
from smart_open import open
from ..file_writers import DataFileWriter
from csvpath.util.box import Box
from csvpath.util.s3.s3_utils import S3Utils


class S3DataWriter(DataFileWriter):
    def load_if(self) -> None:
        if self.sink is None:
            client = S3Utils.make_client()
            self.sink = open(
                self.path,
                self.mode,
                transport_params={"client": client},
            )

    def write(self, data) -> None:
        #
        # don't call this using DataFileWriter as a context manager.
        #
        if data is None:
            raise ValueError("Data cannot be None")
        if not isinstance(data, bytes):
            data = data.encode("utf-8")
        client = S3Utils.make_client()
        with open(self.path, "wb", transport_params={"client": client}) as file:
            file.write(data)
            file.flush()
            file.close()

    def file_info(self) -> dict[str, str | int | float]:
        # TODO: what can/should we provide here?
        return {}
