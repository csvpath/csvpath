from typing import NewType
from csvpath.managers.files.file_manager import FileManager

NamedFileName = NewType("NamedFileName", str)
"""@private"""


class TrackingFileManager(FileManager):

    ADDED = {}

    def __init__(self, *, csvpaths, mgr: FileManager):
        super().__init__(csvpaths=csvpaths)
        self.mgr = mgr

    def add_named_file(
        self, *, name: NamedFileName, path: str, template: str = None
    ) -> None:
        if TrackingFileManager.ADDED.get(name) == path:
            ...
            # print(f"tracking file mgr: skipping file add: {name} is in {TrackingFileManager.ADDED}")
        else:
            self.mgr.add_named_file(name=name, path=path, template=template)
            TrackingFileManager.ADDED[name] = path

    def remove_named_file(self, name: NamedFileName) -> bool:
        if name is not None and name in TrackingFileManager.ADDED:
            del TrackingFileManager.ADDED[name]
        return self.mgr.remove_named_file(name)
