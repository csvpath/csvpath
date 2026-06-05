# pylint: disable=C0114

from csvpath.util.nos import Nos
from csvpath.util.sftp.sftp_config import SftpConfig
from csvpath.util.var_utility import VarUtility as vaut


class SftpServerCreds:
    @classmethod
    def server_credentials(cls, reader_or_writer) -> tuple[str, int]:
        if not Nos(reader_or_writer.path).is_sftp:
            raise ValueError(f"{reader_or_writer.path} is not sftp")
        server, port = Nos(reader_or_writer.path).location_and_port
        username = None
        password = None
        for k, v in reader_or_writer.server_config.items():
            if v.address == server:
                if v.port == port:
                    username = vaut.parse_var_value(
                        reader_or_writer._config, "username", v.username
                    )
                    password = vaut.parse_var_value(
                        reader_or_writer._config, "password", v.password
                    )
                    break
                if port is None and (v.port == 22 or v.port is None):
                    username = vaut.parse_var_value(
                        reader_or_writer._config, "username", v.username
                    )
                    password = vaut.parse_var_value(
                        reader_or_writer._config, "password", v.password
                    )
                    break
        if username is None:
            c = SftpConfig(reader_or_writer._config)
            username = c.username
            password = c.password
        return username, password
