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

    def __init__(self, *, path: str, mode="w") -> None:
        self._count = 0
        self._mode = mode
        self._path = None
        self.path = path
        self.sink = None

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
        self.load_if()
        if self._mode.find("b") > -1 and isinstance(data, str):
            data = data.encode("utf-8")
        self.sink.write(data)

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str) -> None:
        path = pathu.resep(path)
        self._path = path

    def __new__(cls, *, path: str, mode: str = "w"):
        if cls == DataFileWriter:
            if path.startswith("s3://"):
                instance = ClassLoader.load(
                    "from csvpath.util.s3.s3_data_writer import S3DataWriter",
                    kwargs={"path": path, "mode": mode},
                )
                return instance
            if path.startswith("sftp://"):
                instance = ClassLoader.load(
                    "from csvpath.util.sftp.sftp_data_writer import SftpDataWriter",
                    kwargs={"path": path, "mode": mode},
                )
                return instance
            if path.startswith("azure://"):
                instance = ClassLoader.load(
                    "from csvpath.util.azure.azure_data_writer import AzureDataWriter",
                    kwargs={"path": path, "mode": mode},
                )
                return instance
            if path.startswith("gs://"):
                instance = ClassLoader.load(
                    "from csvpath.util.gcs.gcs_data_writer import GcsDataWriter",
                    kwargs={"path": path, "mode": mode},
                )
                return instance
            return GeneralDataWriter(path=path, mode=mode)
        else:
            instance = super().__new__(cls)
            return instance

    @abstractmethod
    def write(self, data) -> None:
        pass

    @abstractmethod
    def file_info(self) -> dict[str, str | int | float]:
        pass


class GeneralDataWriter(DataFileWriter):
    def __init__(self, path: str, mode: str = "w") -> None:
        super().__init__(path=path, mode=mode)

    def load_if(self) -> None:
        if self.sink is None:
            mode = "w" if self._mode is None else self._mode
            if mode != "wb":
                self.sink = open(self.path, mode, encoding="utf-8", newline="")
            else:
                self.sink = open(self.path, mode)

    def write(self, data) -> None:
        """this is a one-and-done write. you don't use the data writer
        as a context manager for this method. for multiple write
        calls to the same file handle use append().
        """
        with open(self.path, "w", encoding="utf-8", newline="") as file:
            file.write(data)

    def file_info(self) -> dict[str, str | int | float]:
        return FileInfo.info(self.path)
