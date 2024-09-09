# pylint: disable=C0114
from typing import Dict, List
import os
import json
from json import JSONDecodeError
from abc import ABC, abstractmethod
from ..util.exceptions import InputException


class CsvPathsManager(ABC):
    """holds paths (the path itself, not a file name or reference) in a named set.
    this allows all paths to be run as a unit, with the results manager holding
    the set's outcomes."""

    @abstractmethod
    def add_named_paths_from_dir(self, *, directory: str, name: str = None) -> None:
        """adds named paths found in a directory. files with multiple paths
        will be handled. if name is not None the named paths for all files
        in the directory will be keyed by name.
        """

    @abstractmethod
    def set_named_paths_from_json(self, file_path: str) -> None:
        """replaces the named paths dict with a dict found in a JSON file. lists
        of paths are keyed by names."""

    @abstractmethod
    def set_named_paths(self, np: Dict[str, List[str]]) -> None:
        """overwrites"""

    @abstractmethod
    def add_named_paths(self, name: str, paths: List[str]) -> None:
        """aggregates the path list under the name. if there is no
        existing list of paths, the name will be added. otherwise,
        the lists will be joined. duplicates are not added.
        """

    @abstractmethod
    def get_named_paths(self, name: str) -> List[str]:  # pylint: disable=C0116
        """returns the csvpaths grouped under the name. remember
        that your csvpaths are in ordered list that determines the
        execution order. when the paths are run serially each csvpath
        completes before the next starts, in the list order. when you
        run the paths breadth-first, line-by-line, the csvpaths are
        applied to each line in the order of the list.
        """

    @abstractmethod
    def remove_named_paths(self, name: str) -> None:  # pylint: disable=C0116
        pass

    @abstractmethod
    def has_named_paths(self, name: str) -> bool:  # pylint: disable=C0116
        pass

    @abstractmethod
    def number_of_named_paths(self) -> bool:  # pylint: disable=C0116
        pass


class PathsManager(CsvPathsManager):  # pylint: disable=C0115, C0116
    MARKER: str = "---- CSVPATH ----"

    def __init__(self, *, csvpaths, named_paths=None):
        if named_paths is None:
            named_paths = {}
        self.named_paths = named_paths
        self.csvpaths = csvpaths

    def set_named_paths(self, np: Dict[str, List[str]]) -> None:
        self.named_paths = np

    def add_named_paths_from_dir(self, *, directory: str, name: str = None) -> None:
        if directory is None:
            raise InputException("Named paths collection name needed")
        if os.path.isdir(directory):
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
                thename = self._name_from_name_part(p)
                path = os.path.join(base, p)
                with open(path, "r", encoding="utf-8") as f:
                    cp = f.read()
                    _ = [
                        apath.strip()
                        for apath in cp.split(PathsManager.MARKER)
                        if apath.strip() != ""
                    ]
                    aname = thename if name is None else name
                    self.add_named_paths(aname, _)
        else:
            raise InputException("dirname must point to a directory")

    def set_named_paths_from_json(self, file_path: str) -> None:
        try:
            with open(file_path, encoding="utf-8") as f:
                j = json.load(f)
                for k in j:
                    v = j[k]
                    if isinstance(v, list):
                        continue
                    if isinstance(v, str):
                        j[k] = [av.strip() for av in v.split(PathsManager.MARKER)]
                    else:
                        raise InputException(f"Unexpected object in JSON key: {k}: {v}")
                self.named_paths = j
        except (OSError, ValueError, TypeError, JSONDecodeError) as ex:
            print(f"Error: cannot load {file_path}: {ex}")

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
        raise InputException("{name} not found")

    def remove_named_paths(self, name: str) -> None:
        if name in self.named_paths:
            del self.named_paths[name]
        else:
            raise InputException("{name} not found")

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
