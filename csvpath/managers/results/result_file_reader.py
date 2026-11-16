import os
import json
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader


class ResultFileReader:
    """@private"""

    @classmethod
    def json_file(self, path: str) -> dict | None:
        #
        # a read never writes (issue #609): writing {} for a missing file
        # could land on top of a manifest a run was still writing
        #
        if not Nos(path).exists():
            return {}
        with DataFileReader(path) as file:
            d = json.load(file.source)
            return d

    @classmethod
    def manifest(self, result_home: str) -> dict | None:
        mp = Nos(result_home).join("manifest.json")
        return ResultFileReader.json_file(mp)

    @classmethod
    def meta(self, result_home: str) -> dict | None:
        mp = Nos(result_home).join("meta.json")
        return ResultFileReader.json_file(mp)

    @classmethod
    def vars(self, result_home: str) -> dict | None:
        mp = Nos(result_home).join("vars.json")
        return ResultFileReader.json_file(mp)
