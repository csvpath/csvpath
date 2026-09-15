import json
from csvpath.util.file_info import FileInfo
from csvpath.util.file_readers import DataFileReader


class JsonDocumentReader(DataFileReader):
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
        quotechar: str = None,
    ) -> None:
        super().__init__()
        self.path = path
        self.mode = mode
        self.encoding = encoding
        self._updates_headers = True

    def next(self) -> list[str]:
        #
        # if you use this class as a context manager you don't
        # need to load_if and close. if that's not the case it
        # must be managed.
        #
        # self.load_if()
        yield json.load(self.source)
        # self.close()

    def file_info(self) -> dict[str, str | int | float]:
        return FileInfo.info(self.path)
