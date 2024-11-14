# pylint: disable=C0114
import pandas as pd
from .file_readers import DataFileReader
from .exceptions import InputException


class PandasDataReader(DataFileReader):
    """
    this class can only be used when the optional "pandas"
    dependency (a.k.a. an "extra") is installed. use csvpath[pandas]
    at add/install time.

    for the reader to work it requires that a dataframe is registered
    with the DataFileReader class
    """

    def __init__(
        self, path: str, *, sheet=None, delimiter=None, quotechar=None
    ) -> None:
        super().__init__()
        self._path = path
        self._delimiter = delimiter if delimiter is not None else ","
        self._quotechar = quotechar if quotechar is not None else '"'
        self._frame = DataFileReader.DATA.get(path)

    @property
    def dataframe(self) -> None:
        return self._frame

    @dataframe.setter
    def dataframe(self, df) -> None:
        self._frame = df

    def next(self) -> list[str]:
        if self.dataframe is None:
            raise InputException("No dataframe is registered on {self._path}")
        data = self.dataframe.copy()
        for row in data.itertuples(index=False):
            line = list(row)
            yield line

    def next_raw(self) -> list[str]:
        raise Exception("next_raw is not supported for Pandas")

    def file_metadata(self) -> dict[str, str | int | float]:
        # TODO: path is likely to be a named-path pointer, not a physical
        # location. what can/should we provide here?
        return {}
