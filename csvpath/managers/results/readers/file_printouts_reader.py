import os
from abc import ABC, abstractmethod
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
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
                if Nos(d).exists():
                    self._printouts = Printouts()
                    with DataFileReader(d) as file:
                        t = file.source.read()
                        printouts = t.split("---- PRINTOUT:")
                        for p in printouts:
                            name = p[0 : p.find("\n")]
                            name = name.strip()
                            body = p[p.find("\n") + 1 :]
                            ps = self._body_to_lines(body)
                            self._printouts[name] = ps
                else:
                    self.result.csvpath.logger.debug(
                        "There is no printouts file at %s", d
                    )
        if self._printouts is None:
            self._printouts = Printouts()
        return self._printouts

    def _body_to_lines(self, body) -> list[str]:
        ps = [line for line in body.split("\n")]
        for i, line in enumerate(ps):
            #
            # print allows newlines. we don't keep newlines from creating new list
            # entries today, but probably should. we would transform the backslash-n
            # to a literal 2-char backslash-n and then convert back here. we can do
            # the back conversion now w/o waiting for the forward. busy, one thing at
            # a time.
            #
            line = line.replace("\\n", "\n")
            if line.strip() == "" and i == len(ps) - 1:
                ps = ps[0 : len(ps) - 1]
        return ps
