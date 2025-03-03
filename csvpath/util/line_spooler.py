import os
import csv
import json
import boto3
from pathlib import Path
from abc import ABC, abstractmethod
from .exceptions import InputException
from .file_readers import DataFileReader
from .file_writers import DataFileWriter
from .file_info import FileInfo
from .nos import Nos
from .path_util import PathUtility as pathu


class LineSpooler(ABC):
    def __init__(self, myresult) -> None:
        self.result = myresult if myresult is not None else None
        self.sink = None
        self._count = 0
        self.closed = False

    @abstractmethod
    def append(self, line) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def bytes_written(self) -> int:
        pass

    def __len__(self) -> int:
        return self._count


class ListLineSpooler(LineSpooler):
    def __init__(self, myresult=None, lines=None) -> None:
        super().__init__(myresult)
        if lines is None:
            raise InputException("Lines argument cannot be none")
        self.sink = lines

    def append(self, line) -> None:
        self.sink.append(line)

    def bytes_written(self) -> int:
        return 0

    def close(self) -> None:
        #
        # note that self.closed must remain False because
        # this memory-only implementation never opens a file and writes data.
        #
        pass

    def __len__(self) -> int:
        return len(self.sink)


class CsvLineSpooler(LineSpooler):
    def __init__(self, myresult) -> None:
        super().__init__(myresult)
        self._path = None
        self.writer = None

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, p: str) -> None:
        p = pathu.resep(p)
        self._path = p

    def __iter__(self):
        return self

    def __next__(self):
        for _ in self.next():
            yield _

    def to_list(self) -> list[str]:
        if self.path is None:
            self._instance_data_file_path()
        if Nos(self.path).exists() is False:
            self.result.csvpath.logger.debug(
                "There is no data.csv at %s. This may or may not be a problem.",
                self.path,
            )
            return []
        lst = []
        for line in DataFileReader(
            self.path,
            filetype="csv",
            delimiter=self.result.csvpath.delimiter,
            quotechar=self.result.csvpath.quotechar,
        ).next():
            lst.append(line)
        return lst

    def __len__(self) -> int:
        if self._count is None or self._count <= 0:
            if self.result is not None and self.result.instance_dir:
                d = os.path.join(self.result.instance_dir, "meta.json")
                if Nos(d).exists() is True:
                    with DataFileReader(d) as file:
                        j = json.load(file.source)
                        n = j["runtime_data"]["count_matches"]
                        self._count = n
        return self._count

    def load_if(self) -> None:
        p = self._instance_data_file_path()
        if p is not None:
            self.sink = self._open_file(p)
            self.writer = csv.writer(self.sink)

    def _open_file(self, path: str):
        # TODO: set this up better for other protocols besides s3
        if path.find("://") > -1:
            dw = DataFileWriter(path=path, mode="w")
            dw.load_if()
            return dw.sink
        file = open(path, "a", newline="", encoding="utf-8")
        return file

    def next(self):
        if self.path is None:
            self._instance_data_file_path()
        if Nos(self.path).exists() is False:
            # if os.path.exists(self.path) is False:
            self.result.csvpath.logger.debug(
                "There is no data.csv at %s. This may or may not be a problem.",
                self.path,
            )
            return
        for line in DataFileReader(
            self.path,
            filetype="csv",
            delimiter=self.result.csvpath.delimiter,
            quotechar=self.result.csvpath.quotechar,
        ).next():
            yield line

    def _warn_if(self) -> None:
        if self.result is not None and self.result.csvpath:
            self.result.csvpath.logger.warning(
                "CsvLineSpooler cannot find instance_data_file_path yet within %s",
                self.result.run_dir,
            )

    def _instance_data_file_path(self):
        if self.result is None:
            self._warn_if()
            return None
        if self.result.csvpath is None:
            self._warn_if()
            return None
        if self.result.csvpath.scanner is None:
            self._warn_if()
            return None
        if self.result.csvpath.scanner.filename is None:
            self._warn_if()
            return None
        #
        # data file could be not there. we can in principle make sure that doesn't happen.
        # if we did, tho, we would need to be sure we don't create the dir so early that
        # it interferes with the ordering of date-stamped instance dirs -- which we saw in
        # one case. leave the concern about the existence of the path aside for now.
        #
        self.path = self.result.data_file_path
        return self.path

    def append(self, line) -> None:
        if not self.writer:
            self.load_if()
        if not self.writer:
            raise InputException(f"Cannot write to data file for {self.result}")
        self.writer.writerows([line])
        self._count += 1

    def bytes_written(self) -> int:
        p = self._instance_data_file_path()
        # there may be no file if we're on/before line 0 of the data.csv
        # that is Ok.
        try:
            i = FileInfo.info(p)
            if i and "bytes" in i:
                return i["bytes"]
            else:
                return -1
        except FileNotFoundError:
            return 0

    def close(self) -> None:
        try:
            if self.sink:
                self.sink.close()
                self.sink = None
                self.closed = True
        except Exception as ex:
            # drop the sink so no chance for recurse
            self.sink = None
            try:
                c = self.csvpath if self.csvpath else self.csvpaths
                c.error_manager.handle_error(source=self, msg=f"{ex}")
            except Exception as e:
                self.result.csvpath.logger.error(
                    f"Caught {e}. Not raising an exception because closing."
                )
