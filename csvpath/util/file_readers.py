# pylint: disable=C0114
import csv
import importlib
import os
from abc import ABC, abstractmethod
import pylightxl as xl
from .exceptions import InputException


class DataFileReader(ABC):
    DATA = {}

    @classmethod
    def register_data(cls, *, path, filelike) -> None:
        DataFileReader.DATA[path] = filelike

    @classmethod
    def deregister_data(cls, path) -> None:
        del DataFileReader.DATA[path]

    def __init__(self) -> None:
        self._path = None

    @property
    def path(self) -> str:
        return self._path

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
            # do we have a file-like thing pre-registered?
            #
            thing = DataFileReader.DATA.get(path)
            if thing is not None and thing.__class__.__name__.endswith("DataFrame"):
                if thing is None:
                    raise Exception(f"No dataframe for {path}")
                module = importlib.import_module("csvpath.util.pandas_data_reader")
                class_ = getattr(module, "PandasDataReader")
                instance = class_(path, delimiter=delimiter, quotechar=quotechar)
                return instance
            if (filetype is not None and filetype == "xlsx") or path.endswith("xlsx"):
                return XlsxDataReader(
                    path,
                    sheet=sheet if sheet != path else None,
                    delimiter=delimiter,
                    quotechar=quotechar,
                )
            if path.startswith("s3://"):
                # e.g. s3://csvpath-example-1/timezones.csv
                module = importlib.import_module("csvpath.util.s3_data_reader")
                class_ = getattr(module, "S3DataReader")
                instance = class_(path, delimiter=delimiter, quotechar=quotechar)
                return instance
            return CsvDataReader(path, delimiter=delimiter, quotechar=quotechar)
        else:
            instance = super().__new__(cls)
            return instance

    @abstractmethod
    def next(self) -> list[str]:
        pass

    @abstractmethod
    def file_metadata(self) -> dict[str, str | int | float]:
        pass


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
        self._path = path
        if sheet is not None or path.find("#") > -1:
            raise InputException(
                f"Received unexpected # char or sheet argument '{sheet}'. CSV files do not have worksheets."
            )
        self._delimiter = delimiter if delimiter is not None else ","
        self._quotechar = quotechar if quotechar is not None else '"'

    def next(self) -> list[str]:
        with open(self._path, "r", encoding="utf-8") as file:
            reader = csv.reader(
                file, delimiter=self._delimiter, quotechar=self._quotechar
            )
            for line in reader:
                yield line

    def next_raw(self) -> list[str]:
        print(f"self._path: {self._path}")
        with open(uri=self._path, mode="r") as file:
            for line in file:
                yield line

    def file_metadata(self) -> dict[str, str | int | float]:
        s = os.stat(self.path)
        meta = {
            "mode",
            s.st_mode,
            "device",
            s.st_dev,
            "bytes",
            s.st_size,
            "created",
            s.st_ctime,
            "last_read",
            s.st_atime,
            "last_mod",
            s.st_mtime,
            "flags",
            s.st._flags,
        }
        return meta


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
        self._sheet = sheet
        self._path = path
        if path.find("#") > -1:
            self._sheet = path[path.find("#") + 1 :]
            self._path = path[0 : path.find("#")]

    def next(self) -> list[str]:
        db = xl.readxl(fn=self._path)
        if not self._sheet:
            self._sheet = db.ws_names[0]

        for row in db.ws(ws=self._sheet).rows:
            yield [f"{datum}" for datum in row]

    def next_raw(self) -> list[str]:
        with open(uri=self._path, mode="r") as file:
            for line in file:
                yield line

    def file_metadata(self) -> dict[str, str | int | float]:
        s = os.stat(self.path)
        meta = {
            "mode",
            s.st_mode,
            "device",
            s.st_dev,
            "bytes",
            s.st_size,
            "created",
            s.st_ctime,
            "last_read",
            s.st_atime,
            "last_mod",
            s.st_mtime,
            "flags",
            s.st._flags,
        }
        return meta
