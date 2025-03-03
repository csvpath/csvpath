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
            self.source = open(
                self.path,
                "r",
                encoding="utf-8",
                transport_params={
                    "connect_kwargs": {"username": c.username, "password": c.password}
                },
            )

    def next(self) -> list[str]:
        config = Box.STUFF.get(Box.CSVPATHS_CONFIG)
        c = SftpConfig(config)
        with open(
            self.path,
            "r",
            encoding="utf-8",
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
        h = SftpFingerprinter().fingerprint(self.path)
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
    # now using smart-open. the test_title_fix test uses it. other than that?
    #
    def read(self) -> str:
        config = Box.STUFF.get(Box.CSVPATHS_CONFIG)
        c = SftpConfig(config)
        with open(
            self.path,
            "rb",
            transport_params={
                "connect_kwargs": {"username": c.username, "password": c.password}
            },
        ) as file:
            bs = file.read()
            try:
                return bs.decode("utf-8")
            except UnicodeDecodeError:
                s = bs.decode("latin-1")
                s.encode("utf-8")
                return s

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
