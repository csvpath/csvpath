from typing import Dict, List, Any
import os
import json
from abc import ABC, abstractmethod
from .. import ConfigurationException
from csvpath.util.config import CsvPathConfig


class CsvPathsManager(ABC):
    @abstractmethod
    def add_named_paths_from_dir(self, *, dirname: str) -> None:
        pass

    @abstractmethod
    def set_named_paths_from_json(self, filename: str) -> None:
        pass

    @abstractmethod
    def set_named_paths(self, np: Dict[str, List[str]]) -> None:
        pass

    @abstractmethod
    def add_named_paths(self, name: str, path: List[str]) -> None:
        pass

    @abstractmethod
    def get_named_paths(self, name: str) -> List[str]:
        pass

    @abstractmethod
    def remove_named_paths(self, name: str) -> None:
        pass


class PathsManager(CsvPathsManager):
    MARKER: str = "---- CSVPATH ----"

    def __init__(self, *, named_paths: Dict[str, List[str]] = {}, csvpaths):
        self.named_paths = named_paths
        self.csvpaths = csvpaths

    def set_named_paths(self, np: Dict[str, List[str]]) -> None:
        self.named_paths = np

    def add_named_paths_from_dir(self, dirname: str) -> None:
        if dirname is None:
            raise ConfigurationException("Named paths collection name needed")
        elif os.path.isdir(dirname):
            if self.named_paths is None:
                self.named_files = {}
            dlist = os.listdir(dirname)
            base = dirname
            for p in dlist:
                #
                # TODO: make allowed exts config
                #
                if p[0] == ".":
                    continue
                if p.find(".") == -1:
                    continue
                ext = p[p.rfind(".") + 1 :].strip().lower()
                if ext not in self.csvpaths.config.CSVPATH_FILE_EXTENSIONS:
                    continue
                name = self._name_from_name_part(p)
                path = os.path.join(base, p)
                with open(path, "r") as f:
                    cp = f.read()
                    _ = [
                        apath.strip()
                        for apath in cp.split(PathsManager.MARKER)
                        if apath.strip() != ""
                    ]
                    self.add_named_paths(name, _)
        else:
            raise ConfigurationException("dirname must point to a directory")

    def set_named_paths_from_json(self, file_path: str) -> None:
        try:
            with open(file_path) as f:
                j = json.load(f)
                for k in j:
                    v = j[k]
                    if isinstance(v, list):
                        continue
                    elif isinstance(v, str):
                        j[k] = [av.strip() for av in v.split(PathsManager.MARKER)]
                    else:
                        raise ConfigurationException(
                            f"Unexpected object in JSON key: {k}: {v}"
                        )
                self.named_paths = j
        except Exception as e:
            raise ConfigurationException(f"Error: cannot load {file_path}: {e}")

    def add_named_paths(self, name: str, path: List[str]) -> None:
        self.named_paths[name] = path

    def get_named_paths(self, name: str) -> List[str]:
        if name in self.named_paths:
            return self.named_paths[name]
        else:
            raise ConfigurationException("{name} not found")

    def remove_named_paths(self, name: str) -> None:
        if name in self.named_paths:
            del self.named_paths[name]
        else:
            raise ConfigurationException("{name} not found")

    def _name_from_name_part(self, name):
        i = name.rfind(".")
        if i == -1:
            pass
        else:
            name = name[0:i]
        return name
