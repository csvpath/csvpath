# pylint: disable=C0114
import os
import json
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter


class Intermediary:
    HIT_COUNT = 0
    MISS_COUNT = 0
    WRITE_COUNT = 0

    def __init__(self, csvpaths) -> None:
        self._csvpaths = csvpaths

    def get_json(self, path):
        ...

    def put_json(self, path, j) -> None:
        ...

    def clear(self, path) -> None:
        ...

    def __new__(cls, csvpaths):
        if cls == Intermediary:
            uc = csvpaths.config.get(section="cache", name="use_cache")
            if uc and uc.strip().lower() == "no":
                return NoCacheIntermediary(csvpaths)
            return CacheIntermediary(csvpaths)
        else:
            instance = super().__new__(cls)
            return instance


class CacheIntermediary:
    def __init__(self, csvpaths) -> None:
        self._csvpaths = csvpaths
        self._cache = {}

    def get_json(self, path):
        if path in self._cache:
            Intermediary.HIT_COUNT += 1
            return self._cache[path]
        try:
            Intermediary.MISS_COUNT += 1
            with DataFileReader(path) as reader:
                j = json.load(reader.source)
                self._cache[path] = j
                return j
        except FileNotFoundError:
            self.put_json(path, [])
            return []

    def put_json(self, path, j) -> None:
        self._cache[path] = j
        Intermediary.WRITE_COUNT += 1
        with DataFileWriter(path=path, mode="w") as writer:
            json.dump(j, writer.sink, indent=2)

    def clear(self, path) -> None:
        del self._cache[path]


class NoCacheIntermediary:
    def __init__(self, csvpaths) -> None:
        self._csvpaths = csvpaths

    def get_json(self, path):
        try:
            with DataFileReader(path) as reader:
                return json.load(reader.source)
        except FileNotFoundError:
            return []

    def put_json(self, path, j) -> None:
        with DataFileWriter(path=path, mode="w") as writer:
            json.dump(j, writer.sink, indent=2)

    def clear(self, path) -> None:
        ...
