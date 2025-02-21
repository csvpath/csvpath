# pylint: disable=C0114
import os
import paramiko
from csvpath.util.box import Box
from .sftp_config import SftpConfig


class SftpDo:
    def __init__(self, path):
        box = Box()
        config = box.get(Box.CSVPATHS_CONFIG)
        self._config = SftpConfig(config)
        #
        #
        #
        self._path = None
        self.path = path
        #
        # save the client itself in box because we clean up
        # the box and need to see a closable thing
        #
        self.sftp = self._config.sftp_client

    @classmethod
    def strip_protocol(self, path: str) -> str:
        p2 = path.lstrip("sftp://")
        if p2 != path:
            # take off the server name
            p2 = p2[p2.find("/") + 1 :]
        return p2

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, p) -> None:
        p = SftpDo.strip_protocol(p)
        self._path = p

    def remove(self) -> None:
        if self.isfile():
            self.sftp.remove(self.path)
        else:
            self._rmdir(self.path)

    def _rmdir(self, path):
        lst = [path]
        self._descendents(lst, path)
        lst.reverse()
        for p in lst:
            if self._isfile(p):
                self.sftp.remove(p)
            else:
                self.sftp.rmdir(p)

    def _descendents(self, lst, path) -> list[str]:
        for n in self._listdir(path, default=[]):
            p = f"{path}/{n}"
            lst.append(p)
            self._descendents(lst, p)

    def copy(self, to) -> None:
        if not self.exists():
            raise FileNotFoundError(f"Source {self.path} does not exist.")
        a = self._config.ssh_client
        a.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        a.connect(
            self._config.server,
            port=self._config.port,
            username=self._config.username,
            password=self._config.password,
        )
        stdin, stdout, stderr = a.exec_command(f"cp {self.path} {to}")

    def exists(self) -> bool:
        try:
            self.sftp.stat(self.path)
            return True
        except FileNotFoundError:
            return False

    def dir_exists(self) -> bool:
        try:
            ld = self._listdir(self.path, default=None)
            return ld is not None
        except FileNotFoundError:
            return False

    def isfile(self) -> bool:
        return self._isfile(self.path)

    def _isfile(self, path) -> bool:
        try:
            self.sftp.open(path, "r")
            r = True
        except (FileNotFoundError, OSError):
            r = False
        return r

    def rename(self, new_path: str) -> None:
        try:
            np = SftpDo.strip_protocol(new_path)
            self.sftp.rename(self.path, np)
        except (IOError, PermissionError):
            raise RuntimeError(f"Failed to rename {self.path} to {new_path}")

    def makedirs(self) -> None:
        self._mkdirs(self.path)

    def _mkdirs(self, path):
        if path == ".":
            return
        try:
            self.sftp.listdir(path)
        except IOError:
            self._mkdirs(os.path.dirname(path))
            self.sftp.mkdir(path)

    def makedir(self) -> None:
        self.makedirs()

    def listdir(self) -> list[str]:
        return self._listdir(self.path)

    def _listdir(self, path, default=None) -> list[str]:
        try:
            return self.sftp.listdir(path)
        except OSError:
            return default
