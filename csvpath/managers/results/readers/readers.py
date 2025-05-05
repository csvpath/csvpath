import os
from abc import ABC, abstractmethod
from csvpath.util.class_loader import ClassLoader
from csvpath.managers.errors.error import Error


class ResultReader(ABC):
    def __init__(self):
        self._result = None

    @property
    def result(self) -> str:
        return self._result

    @result.setter
    def result(self, result) -> None:
        self._result = result


class ErrorsReader(ResultReader):
    def __init__(self):
        super().__init__()
        self._errors = None

    @property
    @abstractmethod
    def errors(self) -> list[Error]:
        pass


class UnmatchedReader(ResultReader):
    def __init__(self):
        super().__init__()
        self._unmatched = None

    @property
    @abstractmethod
    def unmatched(self) -> list[str]:
        pass


class LinesReader(ResultReader):
    def __init__(self):
        super().__init__()
        self._lines = None

    @property
    @abstractmethod
    def lines(self) -> list[str]:
        pass


class PrintoutsReader(ResultReader):
    def __init__(self):
        super().__init__()
        self._printouts = None

    @property
    @abstractmethod
    def printouts(self) -> dict[str, list[str]]:
        pass


class ResultReadersFacade(ErrorsReader, UnmatchedReader, LinesReader, PrintoutsReader):
    #
    # as soon as we get a run_dir and an instance we'll create the
    # instance_dir and load the readers
    #
    def __init__(self, result):
        self.result = result
        #
        # can defer loading at cost of more properties. later.
        #
        self.errors_reader = None
        self.unmatched_reader = None
        self.printouts_reader = None
        self.lines_reader = None
        if result is not None:
            self.load_readers()

    @property
    def run_dir(self) -> str:
        return self.result._run_dir

    def load_readers(self) -> None:
        #
        # eventually, probably, look in [readers] for names -> reader classes. assumption is
        # that at some point we use some kind of database to store results.
        #
        loader = ClassLoader()
        cmd = "from csvpath.managers.results.readers.file_errors_reader import FileErrorsReader"
        r = loader.load(cmd)
        r.result = self.result
        self.errors_reader = r

        cmd = "from csvpath.managers.results.readers.file_printouts_reader import FilePrintoutsReader"
        r = loader.load(cmd)
        r.result = self.result
        self.printouts_reader = r

        cmd = "from csvpath.managers.results.readers.file_lines_reader import FileLinesReader"
        r = loader.load(cmd)
        r.result = self.result
        self.lines_reader = r

        cmd = "from csvpath.managers.results.readers.file_unmatched_reader import FileUnmatchedReader"
        r = loader.load(cmd)
        r.result = self.result
        self.unmatched_reader = r

    @property
    def errors(self) -> list[Error]:
        return self.errors_reader.errors

    @property
    def unmatched(self) -> list[str]:
        return self.unmatched_reader.unmatched

    @property
    def lines(self) -> list[str]:
        return self.lines_reader.lines

    @property
    def printouts(self) -> dict[str, list[str]]:
        return self.printouts_reader.printouts
