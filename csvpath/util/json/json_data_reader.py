import jsonlines
from datetime import datetime
from csvpath.matching.util.expression_utility import ExpressionUtility as exut
from csvpath.util.file_info import FileInfo
from csvpath.util.class_loader import ClassLoader
from csvpath.util.file_readers import DataFileReader
from .json_reader_helper import JsonReaderHelper


class JsonDataReader(DataFileReader):

    #
    # some classes may assume a delimiter and quotechar even though
    # that isn't needed for Json. if passed we ignore them.
    #
    def __init__(
        self,
        path: str,
        *,
        mode: str = "r",
        encoding: str = "utf-8",
        filetype: str = None,
        delimiter: str = None,
        quotechar: str = None
    ) -> None:
        super().__init__()
        self.path = path
        self.mode = mode
        self.encoding = encoding

    def next(self) -> list[str]:
        with jsonlines.open(self.path) as reader:
            i = 0
            for obj in reader.iter(skip_invalid=True):
                line = JsonReaderHelper.line_from_obj(obj, i)
                if isinstance(line, tuple):
                    headers = line[0]
                    line = line[1]
                    yield headers
                    yield line
                else:
                    yield line
                i += 1

    def file_info(self) -> dict[str, str | int | float]:
        return FileInfo.info(self.path)
