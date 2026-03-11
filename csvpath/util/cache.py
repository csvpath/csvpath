# pylint: disable=C0114
import os
import csv
import hashlib
import json
from typing import Dict
from .path_util import PathUtility as pathu
from csvpath.util.nos import Nos
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader


class Cache:
    #
    # csvpathx can be either CsvPath or CsvPaths
    #
    def __init__(self, csvpathx):
        self.csvpathx = csvpathx

    def clear_cache(self) -> None:
        cachedir = self.get_cachedir()
        Nos(cachedir).remove()

    def get_cache_name(self, filename: str) -> str:
        if filename is None:
            raise ValueError("Filename cannot be None")
        try:
            #
            # we cannot cache non-local files until we implement file_info() in the
            # four non-local backends so we can get the file mod time. quite doable,
            # but not doing it atm.
            #
            t = os.path.getmtime(filename)
            filename = f"{filename}{t}"
            return hashlib.sha256(filename.encode("utf-8")).hexdigest()
        except (FileNotFoundError, IsADirectoryError):
            self.csvpathx.logger.debug("{filename} is not available or not a file")
        """
        if Nos(filename).is_local:
            try:
                filename = f"{filename}{os.path.getmtime(filename)}"
                return hashlib.sha256(filename.encode("utf-8")).hexdigest()
            except (FileNotFoundError, IsADirectoryError):
                self.csvpathx.logger.debug("{filename} is not available or not a file")
        return None
        """
    def get_cachedir(self) -> str:
        self.csvpathx.config._assure_cache_path()
        if not Nos(self.csvpathx.config.cache_dir_path).is_local:
            raise ValueError("Cache path must be local")
        return self.csvpathx.config.cache_dir_path

    def get_keypath(self, filename: str) -> str:
        if filename is None:
            raise ValueError("Filename cannot be None")
        fn = self.get_cache_name(filename)
        if fn is None:
            self.csvpathx.logger.debug(
                "Unknown cache name for file. Is the file local?"
            )
            return None
        cachedir = self.get_cachedir()
        if cachedir is None:
            self.csvpathx.logger.debug("No cache path available")
            return None
        keypath = None
        cachepath = os.path.join(cachedir, fn)
        keypath = f"{cachepath}.json"
        return keypath

    def cached_text(self, filename: str) -> list | dict:
        if not Nos(filename).is_local:
            return None
        keypath = self.get_keypath(filename)
        if keypath and Nos(keypath).exists():
            with DataFileReader(path=keypath, mode="rb") as file:
                return json.load(file.source)
        return None

    def cache_text(self, filename: str, data: list | dict) -> None:
        if not Nos(filename).is_local:
            return None
        keypath = self.get_keypath(filename)
        if keypath is None:
            raise ValueError(f"Keypath for {filename} cannot be None")
        with DataFileWriter(path=keypath) as file:
            json.dump(data, file.sink)
