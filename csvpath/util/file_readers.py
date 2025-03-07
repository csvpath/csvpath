# pylint: disable=C0114
import csv
import importlib
import hashlib
import os
from abc import ABC, abstractmethod
import pylightxl as xl
from .exceptions import InputException
from .file_info import FileInfo
from .class_loader import ClassLoader
from .hasher import Hasher
from .path_util import PathUtility as pathu


class DataFileReader(ABC):
    DATA = {}

    def __init__(self) -> None:
        self._path = None
        self.source = None

    @classmethod
    def register_data(cls, *, path, filelike) -> None:
        DataFileReader.DATA[path] = filelike

    @classmethod
    def deregister_data(cls, path) -> None:
        del DataFileReader.DATA[path]

    def __enter__(self):
        self.load_if()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def close(self) -> None:
        if self.source is not None:
            self.source.close()
            self.source = None

    def fingerprint(self) -> str:
        """non-local file-like situations -- e.g. smart-open -- must
        implement their own fingerprint method
        """
        h = Hasher().hash(self.path)
        return h

    def load_if(self) -> None:
        if self.source is None:
            p = self.path
            self.source = open(p, "r", encoding="utf-8")

    def read(self) -> str:
        #
        # this method may not work as-is for some files, e.g. xlsx.
        # however, today we only need it for csvpaths files.
        #
        self.load_if()
        s = self.source.read()
        self.close()
        return s

    def exists(self, path: str) -> bool:
        os.path.exists(path)

    def remove(self, path: str) -> None:
        os.remove(path)

    #
    # new can be a path -- on an os. in
    # S3 it is a key within the same bucket
    # that is part of the path argument.
    #
    def rename(self, path: str, new: str) -> None:
        os.rename(path, new)

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path) -> None:
        path = pathu.resep(path)
        self._path = path

    def __new__(
        cls,
        path: str,
        *,
        filetype: str = None,
        sheet=None,
        delimiter=None,
        quotechar=None,
    ):
        if cls == DataFileReader:
            sheet = None
            if path.find("#") > -1:
                sheet = path[path.find("#") + 1 :]
                path = path[0 : path.find("#")]
            #
            # do we have a file-like / dataframe thing pre-registered?
            #
            thing = DataFileReader.DATA.get(path)
            if thing is not None and thing.__class__.__name__.endswith("DataFrame"):
                if thing is None:
                    raise Exception(f"No dataframe for {path}")
                module = importlib.import_module("csvpath.util.pandas_data_reader")
                class_ = getattr(module, "PandasDataReader")
                instance = class_(path, delimiter=delimiter, quotechar=quotechar)
                return instance
            #
            # how about XLSX?
            #
            if (filetype is not None and filetype == "xlsx") or path.endswith("xlsx"):
                if path.find("s3://") > -1:
                    instance = ClassLoader.load(
                        "from csvpath.util.s3.s3_xlsx_data_reader import S3XlsxDataReader",
                        args=[path],
                        kwargs={
                            "sheet": sheet if sheet != path else None,
                            "delimiter": delimiter,
                            "quotechar": quotechar,
                        },
                    )
                    return instance
                if path.find("sftp://") > -1:
                    instance = ClassLoader.load(
                        "from csvpath.util.sftp.sftp_xlsx_data_reader import SftpXlsxDataReader",
                        args=[path],
                        kwargs={
                            "sheet": sheet if sheet != path else None,
                            "delimiter": delimiter,
                            "quotechar": quotechar,
                        },
                    )
                    return instance
                if path.find("azure://") > -1:
                    instance = ClassLoader.load(
                        "from csvpath.util.azure.azure_xlsx_data_reader import AzureXlsxDataReader",
                        args=[path],
                        kwargs={
                            "sheet": sheet if sheet != path else None,
                            "delimiter": delimiter,
                            "quotechar": quotechar,
                        },
                    )
                    return instance
                if path.find("gs://") > -1:
                    instance = ClassLoader.load(
                        "from csvpath.util.gcs.gcs_xlsx_data_reader import GcsXlsxDataReader",
                        args=[path],
                        kwargs={
                            "sheet": sheet if sheet != path else None,
                            "delimiter": delimiter,
                            "quotechar": quotechar,
                        },
                    )
                    return instance
                return XlsxDataReader(
                    path,
                    sheet=sheet if sheet != path else None,
                    delimiter=delimiter,
                    quotechar=quotechar,
                )
            #
            # not an XSLT
            #
            if path.startswith("s3://"):
                instance = ClassLoader.load(
                    "from csvpath.util.s3.s3_data_reader import S3DataReader",
                    args=[path],
                    kwargs={"delimiter": delimiter, "quotechar": quotechar},
                )
                return instance
            if path.startswith("sftp://"):
                instance = ClassLoader.load(
                    "from csvpath.util.sftp.sftp_data_reader import SftpDataReader",
                    args=[path],
                    kwargs={"delimiter": delimiter, "quotechar": quotechar},
                )
                return instance
            if path.startswith("azure://"):
                instance = ClassLoader.load(
                    "from csvpath.util.azure.azure_data_reader import AzureDataReader",
                    args=[path],
                    kwargs={"delimiter": delimiter, "quotechar": quotechar},
                )
                return instance
            if path.startswith("http://") or path.startswith("https://"):
                instance = ClassLoader.load(
                    "from csvpath.util.http.http_data_reader import HttpDataReader",
                    args=[path],
                    kwargs={"delimiter": delimiter, "quotechar": quotechar},
                )
                return instance
            if path.startswith("gs://"):
                instance = ClassLoader.load(
                    "from csvpath.util.gcs.gcs_data_reader import GcsDataReader",
                    args=[path],
                    kwargs={"delimiter": delimiter, "quotechar": quotechar},
                )
                return instance
            return CsvDataReader(path, delimiter=delimiter, quotechar=quotechar)
        else:
            instance = super().__new__(cls)
            return instance

    @abstractmethod
    def next(self) -> list[str]:
        pass

    @abstractmethod
    def file_info(self) -> dict[str, str | int | float]:
        pass

    def next_raw(self, mode: str = "r") -> list[str]:
        try:
            with open(self.path, mode=mode, encoding="utf-8") as file:
                for line in file:
                    yield line
        except UnicodeDecodeError:
            with open(self.path, mode="rb") as file:
                for line in file:
                    yield line


class CsvDataReader(DataFileReader):
    def __init__(
        self,
        path: str,
        *,
        filetype: str = None,
        sheet=None,
        delimiter=None,
        quotechar=None,
    ) -> None:
        super().__init__()
        self.path = path
        if sheet is not None or path.find("#") > -1:
            raise InputException(
                f"Received unexpected # char or sheet argument '{sheet}'. CSV files do not have worksheets."
            )
        self._delimiter = delimiter if delimiter is not None else ","
        self._quotechar = quotechar if quotechar is not None else '"'

    def next(self) -> list[str]:
        with open(self.path, "r", encoding="utf-8") as file:
            reader = csv.reader(
                file, delimiter=self._delimiter, quotechar=self._quotechar
            )
            for line in reader:
                yield line

    def file_info(self) -> dict[str, str | int | float]:
        return FileInfo.info(self.path)


class XlsxDataReader(DataFileReader):
    def __init__(
        self,
        path: str,
        *,
        filetype: str = None,
        sheet=None,
        delimiter=None,
        quotechar=None,
    ) -> None:
        super().__init__()
        self._sheet = sheet
        self.path = path
        #
        # path should have already been trimmed in __new__ above.
        #
        if path.find("#") > -1:
            self._sheet = path[path.find("#") + 1 :]
            self.path = path[0 : path.find("#")]

    def next(self) -> list[str]:
        db = xl.readxl(fn=self.path)
        if not self._sheet:
            self._sheet = db.ws_names[0]
        for row in db.ws(ws=self._sheet).rows:
            yield [f"{datum}" for datum in row]

    def file_info(self) -> dict[str, str | int | float]:
        return FileInfo.info(self.path)
