# pylint: disable=C0114

from smart_open import open
from csvpath import CsvPaths
from csvpath.util.box import Box
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.sftp.sftp_server_creds import SftpServerCreds
from csvpath.managers.paths.paths_descriptor import ServerConfig


class SftpDataWriter(DataFileWriter):
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
    # populate from the PathsManager.describer's descriptor to allow transfers to
    # otherwise unknown SFTP servers. this should not be used to get files or for
    # any write other than transfers.
    #
    @property
    def server_config(self) -> dict[str, ServerConfig]:
        if not hasattr(self, "_server_config") or self._server_config is None:
            return {}
        return self._server_config

    @server_config.setter
    def server_config(self, servers: dict[str, ServerConfig]) -> None:
        self._server_config = servers

    def server_credentials(self) -> tuple[str, int]:
        u, p = SftpServerCreds.server_credentials(self)
        return (u, p)
        """
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
        """

    def load_if(self) -> None:
        if self.sink is None:
            u, p = self.server_credentials()
            self.sink = open(
                self.path,
                self.mode,
                newline="",
                transport_params={
                    "connect_kwargs": {
                        "username": u,
                        "password": p,
                        "look_for_keys": False,
                        "allow_agent": False,
                    }
                },
            )

    def write(self, data) -> None:
        if self.is_binary and not isinstance(data, bytes):
            data = data.encode(self.encoding)
        self.sink.write(data)
