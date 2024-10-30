# pylint: disable=C0114
import csv
from abc import ABC, abstractmethod
import pylightxl as xl
from .exceptions import InputException


class CsvDataFileReader(ABC):
    def __new__(cls, path: str, *, sheet=None, delimiter=None, quotechar=None):
        if cls == CsvDataFileReader:
            sheet = None
            if path.find("#") > -1:
                sheet = path[path.find("#") + 1 :]
                path = path[0 : path.find("#")]
            if path.endswith("xlsx"):
                return XlsxDataReader(
                    path,
                    sheet=sheet if sheet != path else None,
                    delimiter=delimiter,
                    quotechar=quotechar,
                )
            else:
                return CsvDataReader(path, delimiter=delimiter, quotechar=quotechar)
        else:
            instance = super().__new__(cls)
            return instance

    @abstractmethod
    def next(self) -> list[str]:
        pass


class CsvDataReader(CsvDataFileReader):
    def __init__(
        self, path: str, *, sheet=None, delimiter=None, quotechar=None
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


class XlsxDataReader(CsvDataFileReader):
    def __init__(
        self, path: str, *, sheet=None, delimiter=None, quotechar=None
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
