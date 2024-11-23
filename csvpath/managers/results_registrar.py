import os
import json
from datetime import datetime
from .result import Result
from .result_serializer import ResultSerializer
from .result_registrar import ResultRegistrar


class ResultsRegistrar:
    def __init__(
        self, *, csvpaths, run_dir: str, pathsname: str, results: list[Result]
    ) -> None:
        self.csvpaths = csvpaths
        self.pathsname = pathsname
        self.run_dir = run_dir
        self.results = results

    def write_manifest(self) -> None:
        m = {}
        time = f"{datetime.now()}"
        completed = self.all_completed()
        valid = self.all_valid()
        errors = self.error_count()
        files = self.all_expected_files()
        m["all_completed"] = completed
        m["all_valid"] = valid
        m["time"] = time
        m["error_count"] = errors
        m["all_expected_files"] = files
        mp = self.manifest_path
        with open(mp, "w", encoding="utf-8") as file:
            json.dump(m, file, indent=2)

    def all_valid(self) -> bool:
        for r in self.results:
            if not r.csvpath.is_valid:
                return False
        return True

    def all_completed(self) -> bool:
        for r in self.results:
            if not r.csvpath.completed:
                return False
        return True

    def error_count(self) -> bool:
        ec = 0
        for r in self.results:
            ec += r.errors_count
        return ec

    def all_expected_files(self) -> bool:
        rs = ResultSerializer(self.csvpaths.config.archive_path)
        for r in self.results:
            rr = ResultRegistrar(result=r, result_serializer=rs)
            if not rr.all_expected_files:
                return False
        return True

    @property
    def manifest(self) -> dict[str, str | bool]:
        with open(self.manifest_path, "r", encoding="utf-8") as file:
            d = json.load(file)
            return d
        return None

    @property
    def manifest_path(self) -> str:
        return os.path.join(self.run_dir, "manifest.json")
