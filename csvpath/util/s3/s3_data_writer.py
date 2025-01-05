# pylint: disable=C0114

import os
import boto3
from smart_open import open
from ..file_writers import DataFileWriter


class S3DataWriter(DataFileWriter):
    def load_if(self) -> None:
        if self.sink is None:
            session = boto3.Session(
                aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            )
            import warnings

            warnings.filterwarnings(
                action="ignore", message=r"datetime.datetime.utcnow"
            )

            self.sink = open(
                self._path,
                self._mode,
                transport_params={"client": session.client("s3")},
            )

    def write(self, data) -> None:
        """this is a one-and-done write in mode 'w'. you don't use the data writer
        as a context manager for this method. for multiple write
        calls to the same file handle use append().
        """
        session = boto3.Session(
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
        with open(
            self._path, "wb", transport_params={"client": session.client("s3")}
        ) as file:
            file.write(data.encode("utf-8"))

    def file_info(self) -> dict[str, str | int | float]:
        # TODO: what can/should we provide here?
        return {}
