# pylint: disable=C0114
import os
import csv
import hashlib
from typing import Dict
from .path_util import PathUtility as pathu


class Cache:
    def __init__(self, csvpaths):
        self.csvpaths = csvpaths

    def _cache_name(self, filename: str) -> str:
        if filename is None:
            raise ValueError("Filename cannot be None")
        h = hashlib.sha256(filename.encode("utf-8")).hexdigest()
        return h

    def _cachedir(self) -> str:
        self.csvpaths.config._assure_cache_path()
        return self.csvpaths.config.cache_dir_path

    def cached_text(self, filename: str, type: str) -> str:
        fn = self._cache_name(filename)
        cachedir = self._cachedir()
        cachepath = None
        keypath = None
        if cachedir is None:
            self.csvpaths.logger.debug(
                "No cache path available for file: {filename} of type: {type}"
            )
        else:
            cachepath = os.path.join(cachedir, fn)
            keypath = f"{cachepath}.{type}"
        res = None
        try:
            with open(keypath, "r", encoding="utf-8") as file:
                if type == "csv":
                    reader = csv.reader(file)
                    for line in reader:
                        if len(line) > 0:
                            res = line
                            break
                    if res is None:
                        res = []
                else:
                    res = ""
                    for line in file:
                        res += line
        except Exception:
            self.csvpaths.logger.debug(
                f"Could not read {cachepath} for {filename}. Check config.ini for the cache path."
            )
        return res

    def cache_text(self, filename, strtype: str, data: str) -> None:
        filename = pathu.resep(filename)
        cachedir = self._cachedir()
        if cachedir is None:
            self.csvpaths.logger.debug(
                "No cache dir available. Cannot cache {filename} with {strtype}"
            )
            return
        cachedir = pathu.resep(cachedir)
        cn = self._cache_name(filename)
        cachepath = os.path.join(cachedir, f"{cn}.{strtype}")
        with open(cachepath, "w", encoding="utf-8") as file:
            file.write(str(data))
