from typing import Dict, List, Any
import os
import json
from abc import ABC, abstractmethod
from ..exceptions import ConfigurationException


class CsvPathsManager(ABC):
    @abstractmethod
    def add_named_paths_from_dir(self, *, dir_path: str) -> None:
        pass

    @abstractmethod
    def add_named_paths_from_json(self, filename: str) -> None:
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

    def __init__(self, *, named_paths: Dict[str, List[str]] = {}):
        self.named_paths = named_paths

    def set_named_paths(self, np: Dict[str, List[str]]) -> None:
        self.named_paths = np

    def add_named_paths_from_dir(self, dir_path: str) -> None:
        if dir_path is None:
            raise ConfigurationException("Named paths collection name needed")
        elif os.path.isdir(dir_path):
            if self.named_paths is None:
                self.named_files = {}
            dlist = os.listdir(dir_path)
            base = dir_path
            for p in dlist:
                name = self._name_from_name_part(p)
                path = os.path.join(base, p)
                with open(path, "r") as f:
                    cp = f.read()
                    _ = [apath.strip() for apath in cp.split(PathsManager.MARKER)]
                    self.add_named_paths(name, _)
        else:
            raise ConfigurationException("dir_path must point to a directory")

    def add_named_paths_from_json(self, file_path: str) -> None:
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
