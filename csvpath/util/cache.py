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
        cachepath = os.path.join(self._cachedir(), fn)
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
            self.csvpaths.logger.warning(
                f"Could not read {cachepath} for {filename}. This may be fine, if the cache is empty. Otherwise, check your config.ini for the cache path."
            )
        return res

    def cache_text(self, filename, strtype: str, data: str) -> None:
        filename = pathu.resep(filename)
        cachedir = self._cachedir()
        cachedir = pathu.resep(cachedir)
        cn = self._cache_name(filename)
        cachepath = os.path.join(cachedir, f"{cn}.{strtype}")
        with open(cachepath, "w", encoding="utf-8") as file:
            file.write(str(data))
