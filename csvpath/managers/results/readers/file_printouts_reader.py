import os
from abc import ABC, abstractmethod
from .readers import PrintoutsReader


class Printouts(dict):
    def __setitem__(self, key, value):
        if not isinstance(value, list):
            raise ValueError(f"Printouts must be a list[str] not {type(value)}")
        super().__setitem__(key, value)


class FilePrintoutsReader(PrintoutsReader):
    def __init__(self) -> None:
        super().__init__()
        self._printouts = None

    @property
    def printouts(self) -> dict[str, list[str]]:
        if self._printouts is None:
            if self.result is not None and self.result.instance_dir:
                d = os.path.join(self.result.instance_dir, "printouts.txt")
                if os.path.exists(d):
                    self._printouts = Printouts()  # {}
                    with open(d, "r", encoding="utf-8") as file:
                        t = file.read()
                        printouts = t.split("---- PRINTOUT:")
                        for p in printouts:
                            name = p[0 : p.find("\n")]
                            name = name.strip()
                            body = p[p.find("\n") + 1 :]
                            ps = [line for line in body.split("\n")]
                            self._printouts[name] = ps
        if self._printouts is None:
            self._printouts = Printouts()  # {}
        return self._printouts
