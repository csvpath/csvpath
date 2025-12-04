import csv
import importlib
import pylightxl as xl
from csvpath.util.file_info import FileInfo
from csvpath.util.class_loader import ClassLoader
from csvpath.util.file_readers import DataFileReader


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
