import os
import csv
import json
import boto3
import logging
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
        self.result = myresult
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
    def __init__(
        self,
        myresult,
        *,
        path: str = None,
        logger: logging.Logger = None,
        delimiter: str = ",",
        quotechar: str = '"',
    ) -> None:
        super().__init__(myresult)
        self._path = path
        self.writer = None
        self._logger = logger
        self._delimiter = delimiter
        self._quotechar = quotechar

    @property
    def path(self) -> str:
        if self._path is None:
            self._instance_data_file_path()
        return self._path

    @path.setter
    def path(self, p: str) -> None:
        p = pathu.resep(p)
        self._path = p

    @property
    def logger(self) -> logging.Logger:
        if self._logger:
            return self._logger
        if self.result is not None and self.result.csvpath is not None:
            return self.result.csvpath.logger
        return logging.getLogger(self.__class__.__name__)

    @property
    def delimiter(self) -> str:
        if self._delimiter is not None:
            return self._delimiter
        if self.result is not None and self.result.csvpath is not None:
            return self.result.csvpath.delimiter
        else:
            self.logger.error("No delimiter available")

    @property
    def quotechar(self) -> str:
        if self._quotechar is not None:
            return self._quotechar
        if self.result is not None and self.result.csvpath is not None:
            return self.result.csvpath.quotechar
        else:
            self.logger.error("No quotechar available")

    def __iter__(self):
        return self

    def to_list(self) -> list[str]:
        if not self.path:
            return []
        if self.path is not None and Nos(self.path).exists() is False:
            self.logger.debug(
                "There is no data.csv at %s. This may or may not be a problem.",
                self.path,
            )
            return []
        lst = []
        for line in DataFileReader(
            self.path,
            filetype="csv",
            delimiter=self.delimiter,
            quotechar=self.quotechar,
        ).next():
            lst.append(line)
        return lst

    def __len__(self) -> int:
        if self._count is None or self._count <= 0:
            if self.result is not None and self.result.instance_dir is not None:
                d = Nos(self.result.instance_dir).join("meta.json")
                if Nos(d).exists() is True:
                    with DataFileReader(d) as file:
                        j = json.load(file.source)
                        n = j["runtime_data"]["count_matches"]
                        self._count = n
        return self._count

    def load_if(self) -> None:
        if self.path is None:
            ...
        else:
            self.sink = self._open_file(self.path)
            self.writer = csv.writer(self.sink)

    def _open_file(self, path: str):
        dw = DataFileWriter(path=path, mode="w")
        dw.load_if()
        return dw.sink

    def next(self):
        if not self.path:
            ...
        if Nos(self.path).exists() is False:
            self.logger.debug(
                "There is no data.csv at %s. This may or may not be a problem.",
                self.path,
            )
            return
        for line in DataFileReader(
            self.path,
            filetype="csv",
            delimiter=self.delimiter,
            quotechar=self.quotechar,
        ).next():
            yield line

    def _warn_if(self) -> None:
        if self.result is not None and self.result.csvpath is not None:
            self.logger.warning(
                "CsvLineSpooler cannot find data file path yet within %s",
                self.result.run_dir,
            )
        else:
            self.logger.warning("No path available")

    def _instance_data_file_path(self):
        if self._path is not None:
            return
        if self.result is None:
            self._warn_if()
            return
        if self.result.csvpath is None:
            self._warn_if()
            return
        if self.result.csvpath.scanner is None:
            self._warn_if()
            return
        if self.result.csvpath.scanner.filename is None:
            self._warn_if()
            return
        #
        # data file could be not there. we can in principle make sure that doesn't happen.
        # if we did, tho, we would need to be sure we don't create the dir so early that
        # it interferes with the ordering of date-stamped instance dirs -- which we saw in
        # one case. leave the concern about the existence of the path aside for now.
        #
        self.path = self.result.data_file_path

    def append(self, line) -> None:
        if not self.writer:
            self.load_if()
        if not self.writer:
            msg = None
            if self.result:
                msg = f"Cannot write to data file for {self.result}"
            else:
                msg = f"Cannot write to {self.path}"
            raise InputException(msg)
        self.writer.writerows([line])
        self._count += 1

    def bytes_written(self) -> int:
        try:
            i = FileInfo.info(self.path)
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
                if self.csvpath:
                    self.csvpath.error_manager.handle_error(source=self, msg=f"{ex}")
                elif self.csvpaths:
                    self.csvpaths.error_manager.handle_error(source=self, msg=f"{ex}")
                else:
                    self.logger.error(str(ex))
            except Exception as e:
                self.logger.error(
                    f"Caught {e}. Not raising an exception because closing."
                )
