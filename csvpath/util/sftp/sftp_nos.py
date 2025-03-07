# pylint: disable=C0114
import os
import paramiko
from csvpath.util.box import Box
from .sftp_config import SftpConfig
from ..path_util import PathUtility as pathu


class SftpDo:
    def __init__(self, path):
        self._path = None
        self.setup(path)

    def setup(self, path: str = None) -> None:
        box = Box()
        config = box.get(Box.CSVPATHS_CONFIG)
        self._config = SftpConfig(config)
        if path:
            self.path = path

    """
    @classmethod
    def strip_protocol(self, path: str) -> str:
        return pathu.stripp(path)
    """

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, p) -> None:
        p = pathu.resep(p)
        p = pathu.stripp(p)
        self._path = p

    def remove(self) -> None:
        if self.isfile():
            self._config.sftp_client.remove(self.path)
        else:
            self._rmdir(self.path)

    def _rmdir(self, path):
        lst = [path]
        self._descendents(lst, path)
        lst.reverse()
        for p in lst:
            if self._isfile(p):
                self._config.sftp_client.remove(p)
            else:
                self._config.sftp_client.rmdir(p)

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
            self._config.sftp_client.stat(self.path)
            return True
        except FileNotFoundError:
            return False

    def dir_exists(self) -> bool:
        try:
            ld = self._listdir(self.path, default=None)
            return ld is not None
        except FileNotFoundError:
            return False

    def physical_dirs(self) -> bool:
        return True

    def isfile(self) -> bool:
        return self._isfile(self.path)

    def _isfile(self, path) -> bool:
        try:
            self._config.sftp_client.open(path, "r")
            r = True
        except (FileNotFoundError, OSError):
            r = False
        return r

    def rename(self, new_path: str) -> None:
        try:
            np = pathu.resep(new_path)
            np = pathu.stripp(np)
            self._config.sftp_client.rename(self.path, np)
        except (IOError, PermissionError):
            raise RuntimeError(f"Failed to rename {self.path} to {new_path}")

    def makedirs(self) -> None:
        lst = self.path.split("/")
        path = ""
        for p in lst:
            path = f"{p}" if path == "" else f"{path}/{p}"
            self._mkdirs(path)

    def _mkdirs(self, path):
        try:
            self._config.sftp_client.mkdir(path)
        except OSError:
            ...
            # TODO: should log
        except IOError:
            ...
            # TODO: should log

    def makedir(self) -> None:
        self.makedirs()

    def listdir(self) -> list[str]:
        return self._listdir(self.path)

    def _listdir(self, path, default=None) -> list[str]:
        try:
            return self._config.sftp_client.listdir(path)
        except OSError:
            return default
