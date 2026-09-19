from typing import Any
from csvpath.util.file_readers import DataFileReader
from csvpath.util.hasher import Hasher


class JsonDynamicDocumentReader(DataFileReader):
    #
    # this class is used for accessing a JSON object structure
    # as if it were a file. it requires registering an object
    # with DataFileReader on a path. if used as a context manager
    # the file-like JSON objects will be deregistered. likewise
    # if used within CsvPaths, the data will be cleared when a
    # run completes and CsvPaths clears out the box.
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
        if path is None:
            raise ValueError("Path cannot be None")
        self.path = path
        doc = DataFileReader.DATA.get(path)
        if doc is None:
            raise ValueError("JSON data cannot be None")
        self._doc = doc

    def fingerprint(self) -> str:
        h = Hasher().hash_json(self._doc)
        return h

    def close(self) -> None:
        #
        # can't clear the box because in CsvPaths we use a context mgr
        # form access multiple times within a run. that's what we want
        # to do, generally, but in this case it would cause the data to
        # vanish. CsvPaths will clear the box for us. CsvPath will not.
        # we need to deregister data manually.
        #
        ...
        """
        if self.path:
            self.deregister_data(self.path)
        """

    def load_if(self) -> None: ...

    def next(self) -> Any:
        yield self._doc

    def file_info(self) -> None:
        return None
