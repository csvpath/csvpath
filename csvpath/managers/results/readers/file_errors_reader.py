import os
import json
from abc import ABC, abstractmethod
from csvpath.util.error import Error
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
            if os.path.exists(p):
                with open(p, "r") as file:
                    ej = json.load(file)
            self._errors = []
            if ej:
                for e in ej:
                    error = Error()
                    error.from_json(e)
                    self._errors.append(error)
        return self._errors
