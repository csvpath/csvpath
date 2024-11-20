# pylint: disable=C0114
import os
import csv
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from ..util.error import Error, ErrorHandler
from ..util.exceptions import InputException
from ..util.file_readers import DataFileReader


class LineSpooler(ABC):
    def __init__(self, myresult) -> None:
        self.result = myresult
        self._sink = None
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
        self.path = None
        self.writer = None

    def load_if(self) -> None:
        p = self._instance_data_file_path()
        if p is not None:
            self.sink = open(p, "a")
            self.writer = csv.writer(self.sink)

    def next(self):
        for line in DataFileReader(
            self.path,
            filetype="csv",
            delimiter=self.result.csvpath.delimiter,
            quotechar=self.result.csvpath.quotechar,
        ).next():
            yield line

    def _instance_data_file_path(self):
        if (
            self.result is None
            or self.result.csvpath is None
            or self.result.csvpath.scanner is None
            or self.result.csvpath.scanner.filename is None
        ):
            if self.result and self.result.csvpath:
                self.result.csvpath.logger.warn(
                    "CsvLineSpooler cannot find instance_data_file_path yet within %s",
                    self.result.run_dir,
                )
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
            return os.stat(p).st_size
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
                ErrorHandler(
                    csvpaths=self.result.csvpath.csvpaths,
                    csvpath=self.result.csvpath,
                    error_collector=self.result,
                ).handle_error(ex)
            except Exception as e:
                self.result.csvpath.logger.error(
                    f"Caught {e}. Not raising an exception because closing."
                )
