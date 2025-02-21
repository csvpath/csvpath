import os
from os import environ
import textwrap
import paramiko
from csvpath.util.box import Box
from ..config import Config
from ..caser import Caser


class SftpConfig:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._server = None
        self._port = None
        self._username = None
        self._password = None
        self._sftp_client = None
        self._ssh_client = None

    def __str__(self) -> str:
        return textwrap.dedent(
            f"""
            {self.username}@{self.server}:{self.port}
        """
        )

    @property
    def sftp_client(self) -> paramiko.SSHClient:
        if self._sftp_client is None:
            self._load_clients()
        return self._sftp_client

    @property
    def ssh_client(self) -> paramiko.SSHClient:
        if self._ssh_client is None:
            self._load_clients()
        return self._ssh_client

    def _load_clients(self):
        if self._sftp_client is None:
            self._ssh_client = Box().get(Box.SSH_CLIENT)
            self._sftp_client = Box().get(Box.SFTP_CLIENT)
        if self._sftp_client is None:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(self.server, self.port, self.username, self.password)
            self._ssh_client = c
            self._sftp_client = c.open_sftp()
            Box().add(Box.SSH_CLIENT, self._ssh_client)
            Box().add(Box.SFTP_CLIENT, self._sftp_client)

    @property
    def server(self) -> str:
        if self._server is None:
            s = self.config.get(section="sftp", name="server")
            if Caser.isupper(s):
                s = environ.get(s)
            self._server = s
        return self._server

    @property
    def port(self) -> int:
        if self._port is None:
            s = self.config.get(section="sftp", name="port")
            if Caser.isupper(s):
                s = environ.get(s)
            self._port = s
        return self._port

    @property
    def username(self) -> str:
        if self._username is None:
            s = self.config.get(section="sftp", name="username")
            if Caser.isupper(s):
                s = environ.get(s)
            self._username = s
        return self._username

    @property
    def password(self) -> str:
        if self._password is None:
            s = self.config.get(section="sftp", name="password")
            if Caser.isupper(s):
                s = environ.get(s)
            self._password = s
        return self._password
