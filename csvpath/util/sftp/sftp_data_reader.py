# pylint: disable=C0114
import csv
from smart_open import open
from csvpath.util.box import Box
from csvpath.util.nos import Nos
from ..file_readers import CsvDataReader
from .sftp_fingerprinter import SftpFingerprinter
from .sftp_config import SftpConfig
from .sftp_nos import SftpDo

#
# TODO: next only works with CSV atm. need Excel.
#


class SftpDataReader(CsvDataReader):
    # LOAD = 0

    def load_if(self) -> None:
        if self.source is None:
            config = Box.STUFF.get(Box.CSVPATHS_CONFIG)
            c = SftpConfig(config)
            # SftpDataReader.LOAD += 1
            # print(f"SftpDataReader: load_if: loding: {SftpDataReader.LOAD}")
            # from csvpath.util.log_utility import LogUtility
            # LogUtility.log_brief_trace()

            self.source = open(
                self._path,
                "r",
                transport_params={
                    "connect_kwargs": {"username": c.username, "password": c.password}
                },
            )

    def next(self) -> list[str]:
        config = Box.STUFF.get(Box.CSVPATHS_CONFIG)
        c = SftpConfig(config)
        with open(
            self._path,
            "r",
            transport_params={
                "connect_kwargs": {"username": c.username, "password": c.password}
            },
        ) as file:
            reader = csv.reader(
                file, delimiter=self._delimiter, quotechar=self._quotechar
            )
            for line in reader:
                yield line

    def fingerprint(self) -> str:
        self.load_if()
        h = SftpFingerprinter().fingerprint(self._path)
        self.close()
        return h

    def exists(self, path: str) -> bool:
        nos = Nos(path)
        if nos.isfile():
            return nos.exists()
        else:
            raise ValueError(f"Path {path} is not a file")

    def remove(self, path: str) -> None:
        nos = Nos(path)
        if nos.isfile():
            return nos.remove()
        else:
            raise ValueError(f"Path {path} is not a file")

    def rename(self, path: str, new_path: str) -> None:
        nos = Nos(path)
        if nos.isfile():
            return nos.rename(new_path)
        else:
            raise ValueError(f"Path {path} is not a file")

    #
    # this is not using smart-open. same in the s3. is anything using it?
    #
    def read(self) -> str:
        with open(uri=self.path, mode="r", encoding="utf-8") as file:
            return file.read()

    #
    # this is not using smart-open. same in the s3. is anything using it?
    #
    def next_raw(self) -> str:
        with open(uri=self.path, mode="rb") as file:
            for line in file:
                yield line

    def file_info(self) -> dict[str, str | int | float]:
        # TODO: what can/should we provide here?
        return {}
