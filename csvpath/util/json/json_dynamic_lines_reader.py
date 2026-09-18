from typing import Any
from csvpath.util.file_readers import DataFileReader
from csvpath.util.json.json_reader_helper import JsonReaderHelper


class JsonDynamicLinesReader(DataFileReader):
    #
    # this class is used for accessing a JSON object structure
    # as if it were a file. it requires registering an object
    # with DataFileReader on a path. if used as a context manager
    # the file-like JSONL object will be deregistered. likewise
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
            raise ValueError("JSON cannot be None")
        if not isinstance(doc, list):
            doc = [doc]
        self._doc = doc
        self._updates_headers = True

    def load_if(self) -> None: ...

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

    def next(self) -> list[Any]:
        if self._doc is None:
            raise ValueError("Data cannot be None")
        i = 0
        for obj in self._doc:
            line = JsonReaderHelper.line_from_obj(obj, i)
            if isinstance(line, tuple):
                headers = line[0]
                self.current_headers = headers
                line = line[1]
                yield line
            else:
                if not isinstance(line, (dict, list)):
                    line = [line]
                self.current_headers = line[:]
                yield line
            i += 1

    def file_info(self) -> None:
        return None
