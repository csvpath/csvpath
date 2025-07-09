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

    def __init__(self, mode="r", encoding="utf-8") -> None:
        self._path = None
        self.source = None
        self._mode = None
        self._encoding = None
        self.mode = mode
        self.encoding = encoding

    @classmethod
    def register_data(cls, *, path, filelike) -> None:
        DataFileReader.DATA[path] = filelike

    @classmethod
    def deregister_data(cls, path) -> None:
        del DataFileReader.DATA[path]

    def __enter__(self):
        self.load_if()
        return self

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

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def close(self) -> None:
        if self.source is not None:
            self.source.close()
            self.source = None

    def fingerprint(self) -> str:
        """non-local situations must implement their own fingerprint method"""
        h = Hasher().hash(self.path)
        return h

    def load_if(self) -> None:
        if self.source is None:
            if "b" in self.mode:
                self.source = open(self.path, mode=self.mode)
            else:
                self.source = open(self.path, mode=self.mode, encoding=self.encoding)

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
        mode: str = "r",
        encoding: str = "utf-8",
        filetype: str = None,
        sheet=None,
        delimiter=None,
        quotechar=None,
    ):
        #
        # not passing mode and encoding?
        #
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
            # not an XLSX
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

    def file_info(self) -> dict[str, str | int | float]:
        ...

    #
    # no csv interpretation. used in FileManager.
    #
    def next_raw(self, mode: str = None) -> list[str]:
        try:
            if mode is None:
                mode = self.mode
            if "b" in mode:
                with open(self.path, mode=mode) as file:
                    for line in file:
                        yield line
            else:
                with open(self.path, mode=mode, encoding=self.encoding) as file:
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
        mode: str = "r",
        encoding: str = "utf-8",
        filetype: str = None,
        sheet=None,
        delimiter=None,
        quotechar=None,
    ) -> None:
        super().__init__()
        if path is None:
            raise ValueError("Path cannot be None")
        try:
            self.path = path
            if sheet is not None or path.find("#") > -1:
                raise InputException(
                    f"Received unexpected # char or sheet argument '{sheet}'. CSV files do not have worksheets."
                )
            self._delimiter = delimiter if delimiter is not None else ","
            self._quotechar = quotechar if quotechar is not None else '"'
            self.mode = mode
            self.encoding = encoding
        except Exception as e:
            print(f"Error: cannot init CsvDataReader: {type(e)}: {e}")
            raise

    def next(self) -> list[str]:
        try:
            with open(self.path, self.mode, encoding=self.encoding) as file:
                reader = csv.reader(
                    file, delimiter=self._delimiter, quotechar=self._quotechar
                )
                for line in reader:
                    yield line
        except UnicodeDecodeError:
            #
            # this may not be the best way to handle this problem
            #
            with open(self.path, self.mode, encoding="latin-1") as file:
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
        mode: str = "rb",  # XLSX are always binary
        encoding: str = None,  # XLSX are always binary
        filetype: str = None,
        sheet=None,
        delimiter=None,
        quotechar=None,
    ) -> None:
        super().__init__()
        self._sheet = sheet
        self.path = path
        self.mode = mode
        self.encoding = encoding
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
