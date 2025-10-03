import json
import os
import traceback
from typing import Optional, Any
from csvpath.util.class_loader import ClassLoader


class ConfigEnv:
    def __init__(self, *, config) -> None:
        if config is None:
            raise ValueError("Config cannot be None")
        self._config = config
        #
        # giving Nos "" makes us have to set Nos.path = ...; but otherwise, not a problem.
        #
        self._nos = ClassLoader.load("from csvpath.util.nos import Nos", [""])
        self._env = None
        self._var_sub_source = None
        self._allow = None

    def refresh(self) -> None:
        self._env = None
        self._var_sub_source = None
        self._allow = None

    def nos(self, path: str):
        self._nos.path = path
        return self._nos

    @property
    def config(self):
        return self._config

    @property
    def var_sub_source(self) -> str:
        if self._var_sub_source is None:
            self._var_sub_source = self.config.get(
                section="config", name="var_sub_source", default="env"
            )
        return self._var_sub_source

    @property
    def allow_var_sub(self) -> bool:
        if self._allow is None:
            a = self.config.get(section="config", name="allow_var_sub", default=False)
            self._allow = a and str(a).strip().lower() in ["true", "yes"]
        return self._allow

    @property
    def env(self) -> dict:
        if self._env is None:
            try:
                if not self.nos(self.var_sub_source).exists():
                    # cannot use DataFileWriter and DataFileReader because that would create a circular import.
                    # with DataFileWriter(path=self.var_sub_source) as file:
                    file = ClassLoader.load(
                        "from csvpath.util.file_writers import DataFileWriter",
                        [],
                        {"path": self.var_sub_source},
                    )
                    file.__enter__()
                    json.dump({}, file.sink, indent=4)
                    file.__exit__(None, None, None)

                # with DataFileReader(self.var_sub_source) as file:
                file = ClassLoader.load(
                    "from csvpath.util.file_readers import DataFileReader",
                    [self.var_sub_source],
                )
                file.__enter__()
                self._env = json.load(file.source)
                file.__exit__(None, None, None)
            except Exception:
                print(traceback.format_exc())
        return self._env

    #
    # takes an UPPERCASE name-value, finds where to swap it -- env vars, env file --
    # and returns the swapped value or default, if any; otherwise, returns the
    # original name.
    #
    def get(self, *, name: str, default: Optional[Any] = None):
        if name is None:
            raise ValueError("Name cannot be None")
        if not name.isupper():
            return default if default else name
        if not self.allow_var_sub:
            return default if default else name
        if self.var_sub_source == "env":
            v = os.getenv(name)
            return v if v else default if default else name
        if self.env and name in self.env:
            return self.env.get(name)
        return default if default else name
