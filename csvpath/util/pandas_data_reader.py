# pylint: disable=C0114
import pandas as pd
from .file_readers import DataFileReader
from .exceptions import InputException


class PandasDataReader(DataFileReader):
    """
    this class can only be used when the optional "pandas"
    dependency (a.k.a. an "extra") is installed. use: poetry add csvpath[pandas]
    at add/install time.

    for the reader to work it requires that a dataframe is registered
    with the DataFileReader class.
    """

    #
    # the point here is to handle tabular data from any source pandas
    # supports -- the dataframe, rather than the specific file format.
    # is there any use in supporting loading files into pandas and then
    # setting up the dataframe behind the scenes? probably, but better
    # to wait for demand w/a specific use case.
    #

    def __init__(
        self, path: str, *, sheet=None, delimiter=None, quotechar=None
    ) -> None:
        super().__init__()
        self.path = path
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
