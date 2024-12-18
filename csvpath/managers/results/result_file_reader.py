import os
import json


class ResultFileReader:
    @classmethod
    def json_file(self, path: str) -> dict | None:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as file:
                json.dump({}, file, indent=2)
                return {}
        with open(path, "r", encoding="utf-8") as file:
            d = json.load(file)
            return d

    @classmethod
    def manifest(self, result_home: str) -> dict | None:
        mp = os.path.join(result_home, "manifest.json")
        return ResultFileReader.json_file(mp)

    @classmethod
    def meta(self, result_home: str) -> dict | None:
        mp = os.path.join(result_home, "meta.json")
        return ResultFileReader.json_file(mp)
