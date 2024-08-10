from typing import Dict, List, Any
import os
import json
from . import CsvPath
from . import FileException


class CsvPaths:
    def __init__(
        self,
        *,
        filename=None,
        delimiter=",",
        quotechar='"',
        skip_blank_lines=True,
        named_files: Dict[str, str] = {},
        named_paths: Dict[str, str] = {},
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
        self.named_paths = named_paths
        self.named_collections = {}
        self.named_collectors = {}

    def add_named_paths_from_json(self, filename: str) -> None:
        try:
            with open(filename) as f:
                j = json.load(f)
                self.named_paths = j
                self.named_collections = {}
        except Exception:
            print(f"Error: cannot load {filename}")

    def add_named_path(self, name: str, path: str) -> None:
        self.named_paths[name] = path

    def remove_named_path(self, name: str) -> None:
        if name in self.named_paths:
            del self.named_paths[name]
        if name in self.named_collections:
            del self.named_collections[name]

    def remove_named_collection(self, name: str) -> None:
        if name in self.named_collections:
            del self.named_collections[name]
            del self.named_collectors[name]

    def get_named_collection(self, name) -> List[List[Any]]:
        if name not in self.named_collections:
            self.collect_named_path(name)
        return self.named_collections[name]

    def get_named_collector(self, name) -> CsvPath:
        if name not in self.named_collectors:
            self.collect_named_path(name)
        return self.named_collectors[name]

    def collect_named_path(self, name: str) -> None:
        if name in self.named_paths:
            path = self.csvpath()
            path.parse(self.named_paths[name])
            lines = path.collect()
            self.named_collections[name] = lines
            self.named_collectors[name] = path

    def update_file_path(self, name_or_path: str) -> str:
        ret = None
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

    # =======================

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
