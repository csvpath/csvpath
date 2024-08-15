from typing import Dict, List, Any
import os
import json
from ..exceptions import FileException
from ..exceptions import ConfigurationException
from abc import ABC, abstractmethod


class CsvPathsFilesManager(ABC):
    @abstractmethod
    def add_named_files_from_dir(self, *, dir_path: str) -> None:
        pass

    @abstractmethod
    def add_named_files_from_json(self, filename: str) -> None:
        pass

    @abstractmethod
    def set_named_files(self, nf: Dict[str, str]) -> None:
        pass

    @abstractmethod
    def add_named_file(self, name: str, path: str) -> None:
        pass

    @abstractmethod
    def get_named_file(self, name: str) -> str:
        pass

    @abstractmethod
    def remove_named_file(self, name: str) -> None:
        pass


class FilesManager(CsvPathsFilesManager):
    def __init__(self, *, named_files: Dict[str, str] = {}):
        self.named_files: Dict[str, str] = named_files

    def set_named_files(self, nf: Dict[str, str]) -> None:
        self.named_files = nf

    def add_named_files_from_json(self, filename: str) -> None:
        try:
            with open(filename) as f:
                j = json.load(f)
                self.named_files = j
        except Exception:
            print(f"Error: cannot load {filename}")

    def add_named_files_from_dir(self, name):
        dlist = os.listdir(name)
        base = name
        for p in dlist:
            _ = p.lower()
            if _.endswith(".csv") or _.endswith(".tsv"):
                name = self._name_from_name_part(p)
                path = os.path.join(base, p)
                self.named_files[name] = path
            else:
                print(f"skipping {p} because it doesn't look like a csv file")

    def add_named_file(self, name: str, path: str) -> None:
        self.named_files[name] = path

    def get_named_file(self, name: str) -> str:
        if name not in self.named_files:
            return None
        return self.named_files[name]

    def remove_named_file(self, name: str) -> None:
        if name in self.named_files:
            del self.named_files[name]

    def _name_from_name_part(self, name):
        i = name.rfind(".")
        if i == -1:
            pass
        else:
            name = name[0:i]
        return name