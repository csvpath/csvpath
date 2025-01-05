import os
import json
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter


class ResultFileReader:
    @classmethod
    def json_file(self, path: str) -> dict | None:
        if not Nos(path).exists():
            # if not os.path.exists(path):
            with DataFileWriter(path=path) as file:
                # with open(path, "w", encoding="utf-8") as file:
                json.dump({}, file.sink, indent=2)
                return {}
        with DataFileReader(path) as file:
            # with open(path, "r", encoding="utf-8") as file:
            d = json.load(file.source)
            return d

    @classmethod
    def manifest(self, result_home: str) -> dict | None:
        mp = os.path.join(result_home, "manifest.json")
        return ResultFileReader.json_file(mp)

    @classmethod
    def meta(self, result_home: str) -> dict | None:
        mp = os.path.join(result_home, "meta.json")
        return ResultFileReader.json_file(mp)
