from typing import Dict, List, Any
import os
import json
from abc import ABC, abstractmethod
from .. import ConfigurationException
from csvpath.util.config import CsvPathConfig


class CsvPathsManager(ABC):
    @abstractmethod
    def add_named_paths_from_dir(self, *, directory: str, thename: str = None) -> None:
        """adds named paths found in a directory. files with multiple paths
        will be handled. if thename is not None the named paths for all files
        in the directory will be keyed by thename.
        """
        pass

    @abstractmethod
    def set_named_paths_from_json(self, filename: str) -> None:
        pass

    @abstractmethod
    def set_named_paths(self, np: Dict[str, List[str]]) -> None:
        pass

    @abstractmethod
    def add_named_paths(self, name: str, path: List[str]) -> None:
        """aggregates the path list under the name. if there is no
        existing list of paths, the name will be added. otherwise,
        the lists will be joined. duplicates are not added.
        """
        pass

    @abstractmethod
    def get_named_paths(self, name: str) -> List[str]:
        pass

    @abstractmethod
    def remove_named_paths(self, name: str) -> None:
        pass

    @abstractmethod
    def has_named_paths(self, name: str) -> bool:
        pass

    @abstractmethod
    def number_of_named_paths(self) -> bool:
        pass


class PathsManager(CsvPathsManager):
    MARKER: str = "---- CSVPATH ----"

    def __init__(self, *, csvpaths, named_paths=None):
        if named_paths is None:
            named_paths = {}
        self.named_paths = named_paths
        self.csvpaths = csvpaths

    def set_named_paths(self, np: Dict[str, List[str]]) -> None:
        self.named_paths = np

    def add_named_paths_from_dir(self, *, directory: str, thename: str = None) -> None:
        if directory is None:
            raise ConfigurationException("Named paths collection name needed")
        elif os.path.isdir(directory):
            dlist = os.listdir(directory)
            base = directory
            for p in dlist:
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
                    aname = name if thename is None else thename
                    self.add_named_paths(aname, _)
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

    def add_named_paths(self, name: str, paths: List[str]) -> None:
        if name in self.named_paths:
            for p in paths:
                if p in self.named_paths[name]:
                    pass
                else:
                    self.named_paths[name].append(paths)
        else:
            self.named_paths[name] = paths

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

    def has_named_paths(self, name: str) -> bool:
        return name in self.named_paths

    def number_of_named_paths(self) -> bool:
        return len(self.named_paths)

    def _name_from_name_part(self, name):
        i = name.rfind(".")
        if i == -1:
            pass
        else:
            name = name[0:i]
        return name
