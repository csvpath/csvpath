# pylint: disable=C0114
import csv
from abc import ABC, abstractmethod
import pylightxl as xl


class CsvDataFileReader(ABC):
    def __new__(cls, path: str, *, delimiter=None, quotechar=None):
        if cls == CsvDataFileReader:
            if path.endswith("xlsx"):
                return XlsxDataReader(path)
            else:
                return CsvDataReader(path)
        else:
            instance = super().__new__(cls)
            return instance

    @abstractmethod
    def next(self) -> list[str]:
        pass


class CsvDataReader(CsvDataFileReader):
    def __init__(self, path: str, *, delimiter=None, quotechar=None) -> None:
        self._path = path
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
    def __init__(self, path: str, *, delimiter=None, quotechar=None) -> None:
        self._path = path
        self._sheet = None
        if path.find("#") > -1:
            self._path = path[0 : path.find("#")]
            self._sheet = path[path.find("#") + 1]

    def next(self) -> list[str]:
        db = xl.readxl(fn=self._path)
        if not self._sheet:
            self._sheet = db.ws_names[0]

        for row in db.ws(ws=self._sheet).rows:
            yield [f"{datum}" for datum in row]
