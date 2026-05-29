# pylint: disable=C0114
import csv
from smart_open import open
from ..file_readers import CsvDataReader
from .sftp_fingerprinter import SftpFingerprinter
from .sftp_config import SftpConfig
from csvpath import CsvPaths
from csvpath.util.var_utility import VarUtility as vaut
from csvpath.util.box import Box
from csvpath.util.nos import Nos
from csvpath.managers.files.file_descriptor import ServerConfig


class SftpDataReader(CsvDataReader):
    @property
    def _config(self):
        config = Box().get(Box.CSVPATHS_CONFIG)
        if config is None:
            #
            # if none, we may not be in a context closely tied to a CsvPaths.
            # e.g. FP. so we create a new csvpaths just for the config. it will
            # be identical to any csvpaths in this project unless the other
            # csvpaths were long-lived and had programmatic changes.
            #
            config = CsvPaths().config
            Box().add(Box.CSVPATHS_CONFIG, config)
        return config

    #
    # populate from the FileManager.describer's descriptor, when needed, in order
    # to load files from sftp sites other than the one configured in config.ini
    # that is the only use that should be made.
    #
    # we need to be able to use a non-cached client with a given set of credentials
    # so that we can talk with servers that are not in our config.ini. this is a
    # particularly sftp requirement.
    #
    # in this class we have the advantage of never having cached the client used
    # for basic reads. (Nos is another matter). so if we add the required info here
    # we should be good.
    #
    @property
    def server_config(self) -> list[ServerConfig]:
        if not hasattr(self, "_server_config") or self._server_config is None:
            return []
        return self._server_config

    @server_config.setter
    def server_config(self, servers: list[ServerConfig]) -> None:
        self._server_config = servers

    #
    # unit
    #
    def server_credentials(self) -> tuple[str, int]:
        if not Nos(self.path).is_sftp:
            raise ValueError(f"{self.path} is not sftp")
        server, port = Nos(self.path).location_and_port
        username = None
        password = None
        for k, v in self.server_config.items():
            if v.address == server:
                if v.port == port:
                    username = vaut.parse_var_value(
                        self._config, "username", v.username
                    )
                    password = vaut.parse_var_value(
                        self._config, "password", v.password
                    )
                    break
                if port is None and (v.port == 22 or v.port is None):
                    username = vaut.parse_var_value(
                        self._config, "username", v.username
                    )
                    password = vaut.parse_var_value(
                        self._config, "password", v.password
                    )
                    break
        if username is None:
            c = SftpConfig(self._config)
            username = c.username
            password = c.password
        return username, password

    def load_if(self) -> None:
        if self.source is None:
            #
            # careful with the "b", w/o removing the encoding we have problems.
            #
            u, p = self.server_credentials()
            if self.mode and "b" in self.mode:
                self.source = open(
                    self.path,
                    self.mode,
                    transport_params={
                        "connect_kwargs": {
                            "username": u,
                            "password": p,
                            "look_for_keys": False,
                            "allow_agent": False,
                        }
                    },
                )
            else:
                self.source = open(
                    self.path,
                    self.mode,
                    encoding=self.encoding,
                    transport_params={
                        "connect_kwargs": {
                            "username": u,
                            "password": p,
                            "look_for_keys": False,
                            "allow_agent": False,
                        }
                    },
                )

    # ----------------------
    # NOTE:
    #
    # fingerprint(), exists(), remove(), and rename() use Nos and
    # are always operating against the config.ini sftp server.
    #
    # the read methods: next(), next_raw() and read() can use the
    # server_config properties and server_credentials() to go against
    # other sftp servers.
    # ----------------------

    def fingerprint(self) -> str:
        self.load_if()
        h = SftpFingerprinter().fingerprint(self.path)
        self.close()
        return h

    def exists(self, path: str) -> bool:
        nos = Nos(path)
        if nos.isfile():
            return nos.exists()
        else:
            raise ValueError(f"Path {path} is not a file")

    def remove(self, path: str) -> None:
        nos = Nos(path)
        if nos.isfile():
            return nos.remove()
        else:
            raise ValueError(f"Path {path} is not a file")

    def rename(self, path: str, new_path: str) -> None:
        nos = Nos(path)
        if nos.isfile():
            return nos.rename(new_path)
        else:
            raise ValueError(f"Path {path} is not a file")

    def next(self) -> list[str]:
        u, p = self.server_credentials()
        with open(
            self.path,
            self.mode,
            encoding=self.encoding,
            transport_params={
                "connect_kwargs": {
                    "username": u,
                    "password": p,
                    "look_for_keys": False,
                    "allow_agent": False,
                }
            },
        ) as file:
            reader = csv.reader(
                file, delimiter=self._delimiter, quotechar=self._quotechar
            )
            for line in reader:
                yield line

    def next_raw(self) -> list[str]:
        u, p = self.server_credentials()
        with open(
            self.path,
            self.mode,
            encoding=self.encoding,
            transport_params={
                "connect_kwargs": {
                    "username": u,
                    "password": p,
                    "look_for_keys": False,
                    "allow_agent": False,
                }
            },
        ) as file:
            for line in file:
                yield line

    #
    # now using smart-open. the test_title_fix test uses it. other than that?
    #
    def read(self) -> str:
        u, p = self.server_credentials()
        with open(
            self.path,
            self.mode,
            transport_params={
                "connect_kwargs": {
                    "username": u,
                    "password": p,
                    "look_for_keys": False,
                    "allow_agent": False,
                }
            },
        ) as file:
            bs = file.read()
            try:
                if self.is_binary:
                    return bs
                elif isinstance(bs, str):
                    return bs
                else:
                    return bs.encode("utf-8")
            except UnicodeDecodeError:
                s = bs.decode("latin-1")
                s.encode("utf-8")
                return s
