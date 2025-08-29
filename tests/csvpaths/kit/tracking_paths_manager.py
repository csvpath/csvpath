# pylint: disable=C0114
from typing import NewType
from csvpath import CsvPath
from csvpath.managers.paths.paths_manager import PathsManager

# types for clarity
NamedPathsName = NewType("NamedPathsName", str)
"""@private"""
Csvpath = NewType("Csvpath", str)
"""@private"""
Identity = NewType("Identity", str)
"""@private"""


class TrackingPathsManager(PathsManager):

    ADDED = {}

    def __init__(self, *, csvpaths, named_paths=None, mgr=PathsManager):
        super().__init__(csvpaths=csvpaths, named_paths=named_paths)
        self.mgr = mgr

    def add_named_paths(
        self,
        *,
        name: NamedPathsName,
        paths: list[Csvpath] = None,
        from_file: str = None,
        from_dir: str = None,
        from_json: str = None,
        source_path: str = None,
        template: str = None,
        append: bool = False,
    ) -> None:
        if not append and self._loaded(name, paths):
            ...
        else:
            ref = self.mgr.add_named_paths(
                name=name,
                paths=paths,
                from_file=from_file,
                from_dir=from_dir,
                from_json=from_json,
                source_path=source_path,
                template=template,
                append=append,
            )
            TrackingPathsManager.ADDED[name] = paths
            return ref

    def _loaded(self, name, paths):
        _ = TrackingPathsManager.ADDED.get(name)
        if paths is None:
            return False
        if _ is None:
            if name in TrackingPathsManager.ADDED:
                del TrackingPathsManager.ADDED[name]
            return False
        if paths == _:
            return True
        return False

    def remove_named_paths(self, name: NamedPathsName, strict: bool = False) -> None:
        self.mgr.remove_named_paths(name, strict)
        if name in TrackingPathsManager.ADDED:
            del TrackingPathsManager.ADDED[name]
