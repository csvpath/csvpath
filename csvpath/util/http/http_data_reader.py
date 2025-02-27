# pylint: disable=C0114
import csv
from smart_open import open
from ..file_readers import CsvDataReader

#
# atm, http(s) is read-remote for named-file adds only so we don't have
# to worry about the writer, Nos or Excel.
#


class HttpDataReader(CsvDataReader):
    def load_if(self) -> None:
        if self.source is None:
            self.source = open(self._path, "r")

    def next(self) -> list[str]:
        with open(self._path, "r") as file:
            reader = csv.reader(
                file, delimiter=self._delimiter, quotechar=self._quotechar
            )
            for line in reader:
                yield line

    def next_raw(self, mode: str = "r") -> list[str]:
        try:
            with open(self._path, mode=mode, encoding="utf-8") as file:
                for line in file:
                    yield line
        except UnicodeDecodeError:
            with open(self._path, mode="rb") as file:
                for line in file:
                    yield line

    def fingerprint(self) -> str:
        ...

    def exists(self, path: str) -> bool:
        ...

    def remove(self, path: str) -> None:
        ...

    def rename(self, path: str, new_path: str) -> None:
        ...

    def file_info(self) -> dict[str, str | int | float]:
        # TODO: what can/should we provide here?
        return {}
