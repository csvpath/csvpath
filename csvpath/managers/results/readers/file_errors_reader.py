import os
import json
from abc import ABC, abstractmethod
from csvpath.managers.errors.error import Error
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from .readers import ErrorsReader


class FileErrorsReader(ErrorsReader):
    def __init__(self) -> None:
        super().__init__()
        self._errors = None

    @property
    def errors(self) -> list[Error]:
        if self._errors is None and self.result is not None:
            ej = None
            p = os.path.join(self.result.instance_dir, "errors.json")
            if Nos(p).exists():
                with DataFileReader(p) as file:
                    ej = json.load(file.source)
            self._errors = []
            if ej:
                for e in ej:
                    error = Error()
                    error.from_json(e)
                    self._errors.append(error)
        return self._errors
