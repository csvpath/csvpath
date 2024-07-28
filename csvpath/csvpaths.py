from csvpath.csvpath import CsvPath, NoFileException
from typing import Dict
import os
import json


class CsvPaths:
    def __init__(
        self,
        *,
        filename=None,
        delimiter=",",
        quotechar='"',
        skip_blank_lines=True,
        named_files: Dict[str, str] = {},
    ):
        self.named_files: Dict[str, str] = None
        self.set_file_path(filename)
        if self.named_files is None:
            self.named_files = {}
        if named_files is not None and not named_files == {}:
            self.named_files = {**named_files, **self.named_files}
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.skip_blank_lines = skip_blank_lines

    def update_file_path(self, name_or_path: str) -> str:
        ret = None
        print(f"CsvPaths.update_file_path: named_files: {self.named_files}")
        if self.named_files is not None and name_or_path in self.named_files:
            ret = self.named_files.get(name_or_path)
        else:
            ret = name_or_path
        return ret

    def csvpath(self) -> CsvPath:
        # csvpath will look to its csvpaths for files
        return CsvPath(
            csvpaths=self,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            skip_blank_lines=self.skip_blank_lines,
        )

    def set_named_files(self, nf: Dict[str, str]) -> None:
        self.named_files = nf

    def set_file_path(self, name: str) -> None:
        self.filename = None
        if name is None:
            return
        elif os.path.isdir(name):
            self._set_from_dir(name)
        else:
            # file. is json? plain csv?
            try:
                with open(name) as f:
                    j = json.load(f)
                    self.named_files = j
            except Exception:
                # expected exception
                self._set_from_file(name)

    def _set_from_dir(self, name):
        if self.named_files is None:
            self.named_files = {}
        dlist = os.listdir(name)
        base = name
        for p in dlist:
            name = self._name_from_name_part(p)
            path = os.path.join(base, p)
            self.named_files[name] = path

    def _name_from_name_part(self, name):
        i = name.rfind(".")
        if i == -1:
            pass
        else:
            name = name[0:i]
        return name

    def _set_from_file(self, name):
        path = name
        i = name.rfind(os.sep)
        name = self._name_from_name_part(name[i + 1 :])
        if self.named_files is None:
            self.named_files = {}
        self.named_files[name] = path
