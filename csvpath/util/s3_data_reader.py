# pylint: disable=C0114
import csv
import importlib
from smart_open import open
from .file_readers import CsvDataReader


class S3DataReader(CsvDataReader):
    def next(self) -> list[str]:
        with open(uri=self._path, mode="r") as file:
            reader = csv.reader(
                file, delimiter=self._delimiter, quotechar=self._quotechar
            )
            for line in reader:
                yield line

    def next_raw(self) -> list[str]:
        with open(uri=self._path, mode="r") as file:
            for line in file:
                yield line

    def file_metadata(self) -> dict[str, str | int | float]:
        # TODO: what can/should we provide here?
        return {}
