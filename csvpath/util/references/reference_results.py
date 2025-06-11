import os
import json
from csvpath.util.file_readers import DataFileReader
from csvpath.util.references.reference_parser import ReferenceParser


class ReferenceResults:
    # csvpaths: "CsvPaths" disallowed by flake
    def __init__(self, *, ref: ReferenceParser, csvpaths) -> None:
        self.ref = ref
        self.csvpaths = csvpaths
        self._files = []
        self._manifest_path = None
        self._mani = None
        self._version_index = -1

    @property
    def runs_manifest_path(self) -> str:
        return f"{self.csvpaths.config.get(section='results', name='archive')}{os.sep}manifest.json"

    @property
    def runs_manifest(self) -> str:
        with DataFileReader(self.runs_manifest_path) as file:
            return json.load(file.source)

    @property
    def files(self) -> list[str]:
        return self._files

    @files.setter
    def files(self, files: list[str]) -> None:
        if not isinstance(files, list):
            raise ValueError("Files must be a list")
        self._files = files

    @property
    def manifest_path(self) -> str:
        return self._manifest_path

    @manifest_path.setter
    def manifest_path(self, mani: str) -> None:
        self._manifest_path = mani

    def __len__(self) -> int:
        if self._files is None:
            return 0
        return len(self._files)

    @property
    def version_index(self) -> int:
        if self._version_index == -1:
            # self.resolve()
            ...
        return self._version_index

    @property
    def manifest(self):
        if self._mani is None:
            if self.ref.datatype == "files":
                fm = self.csvpaths.file_manager
                r = fm.registrar
                rm = self.ref.root_major
                home = fm.named_file_home(rm)
                mani_path = r.manifest_path(home)
                self._mani = r.get_manifest(mani_path)
            elif self.ref.datatype == "results":
                ...
            elif self.ref.datatype == "csvpaths":
                ...
            else:
                ...
        return self._mani
