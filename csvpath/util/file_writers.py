# pylint: disable=C0114
import csv
import importlib
import os
from abc import ABC, abstractmethod
import pylightxl as xl
from .exceptions import InputException
from .file_info import FileInfo
from .class_loader import ClassLoader
from .path_util import PathUtility as pathu


class DataFileWriter(ABC):
    """
    to write a csv line-by-line we use a line spooler.
    """

    def __init__(self, *, path: str, mode="w", encoding="utf-8") -> None:
        self._count = 0
        self._mode = None
        self._encoding = None
        self._path = None
        self.sink = None
        self.path = path
        self.encoding = encoding
        self.mode = mode

    def __enter__(self):
        self.load_if()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def close(self) -> None:
        if self.sink is not None:
            self.sink.flush()
            self.sink.close()
            self.sink = None

    @abstractmethod
    def load_if(self) -> None:
        ...

    def append(self, data) -> None:
        #
        # note that this only actually appends if mode is "a" or "ab". if
        # "w" we rewrite the file, despite the method name. :/
        #
        self.load_if()
        if self.is_binary and isinstance(data, str):
            data = data.encode(self.encoding)
        self.sink.write(data)

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, m: str) -> None:
        self._mode = m

    @property
    def is_binary(self) -> bool:
        return "b" in self.mode

    @property
    def encoding(self) -> str:
        return self._encoding

    @encoding.setter
    def encoding(self, e: str) -> None:
        self._encoding = e

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str) -> None:
        path = pathu.resep(path)
        self._path = path

    def __new__(cls, *, path: str, mode: str = "w", encoding="utf-8"):
        if cls == DataFileWriter:
            if path.startswith("s3://"):
                instance = ClassLoader.load(
                    "from csvpath.util.s3.s3_data_writer import S3DataWriter",
                    kwargs={"path": path, "mode": mode, "encoding": encoding},
                )
                return instance
            if path.startswith("sftp://"):
                instance = ClassLoader.load(
                    "from csvpath.util.sftp.sftp_data_writer import SftpDataWriter",
                    kwargs={"path": path, "mode": mode, "encoding": encoding},
                )
                return instance
            if path.startswith("azure://"):
                instance = ClassLoader.load(
                    "from csvpath.util.azure.azure_data_writer import AzureDataWriter",
                    kwargs={"path": path, "mode": mode, "encoding": encoding},
                )
                return instance
            if path.startswith("gs://"):
                instance = ClassLoader.load(
                    "from csvpath.util.gcs.gcs_data_writer import GcsDataWriter",
                    kwargs={"path": path, "mode": mode, "encoding": encoding},
                )
                return instance
            return GeneralDataWriter(path=path, mode=mode, encoding=encoding)
        else:
            instance = super().__new__(cls)
            return instance

    @abstractmethod
    def write(self, data) -> None:
        ...

    def file_info(self) -> dict[str, str | int | float]:
        return {}


class GeneralDataWriter(DataFileWriter):
    def __init__(self, path: str, *, mode: str = "w", encoding="utf-8") -> None:
        super().__init__(path=path, mode=mode, encoding=encoding)

    def load_if(self) -> None:
        if self.sink is None:
            if self.is_binary:
                self.sink = open(self.path, self.mode)
            else:
                self.sink = open(self.path, self.mode, encoding="utf-8", newline="")

    def write(self, data) -> None:
        if self.is_binary:
            with open(self.path, self.mode) as file:
                if not isinstance(data, bytes):
                    try:
                        data = data.encode("utf-8")
                    except Exception:
                        ...
                file.write(data)
        else:
            with open(self.path, self.mode, encoding=self.encoding, newline="") as file:
                file.write(data)

    def file_info(self) -> dict[str, str | int | float]:
        try:
            return FileInfo.info(self.path)
        except Exception:
            return {}
