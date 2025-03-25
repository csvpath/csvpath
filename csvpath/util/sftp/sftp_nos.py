# pylint: disable=C0114
import os
import paramiko
import stat
from stat import S_ISDIR, S_ISREG
from csvpath.util.box import Box
from ..path_util import PathUtility as pathu
from .sftp_config import SftpConfig
from .sftp_walk import SftpWalk


class SftpDo:
    def __init__(self, path):
        self._path = None
        self._server_part = None
        self._config = None
        self.setup(path)

    def setup(self, path: str = None) -> None:
        box = Box()
        config = box.get(Box.CSVPATHS_CONFIG)
        self._server_part = f"sftp://{config.get(section='sftp', name='server')}:{config.get(section='sftp', name='port')}"
        self._config = SftpConfig(config)
        if path:
            self.path = path
            #
            # have to set the cwd to the path. from the caller's POV this is
            # a new use of Nos.
            #
            # to keep it simple just reset.
            #
            self._config.reset()

    @property
    def path(self) -> str:
        return self._path

    """
    @property
    def parent_dir_path(self) -> str:
        p = self.path
        if p.find("/") == -1:
            return "/"
        if not p.startswith("/"):
            p = f"/{p}"
        return p[0:p.rfind("/")]
    """

    @path.setter
    def path(self, p) -> None:
        p = pathu.resep(p)
        p = pathu.stripp(p)
        #
        # when we set the path using Nos we are always expecting the
        # fully qualified path. pathu.stripp may not give us the sftp
        # root. we shouldn't assume. instead make sure.
        #
        if not p.startswith("/"):
            p = f"/{p}"
        self._path = p

    def remove(self) -> None:
        if self.path == "/":
            raise ValueError("Cannot remove the root")
        if self.isfile():
            self._config.sftp_client.remove(self.path)
        else:
            walk = SftpWalk(self._config)
            walk.remove(self.path)

    def listdir(
        self,
        *,
        files_only: bool = False,
        recurse: bool = False,
        dirs_only: bool = False,
        default=None,
    ) -> list[str]:
        if files_only is True and dirs_only is True:
            raise ValueError("Cannot list with neither files nor dirs")
        walk = SftpWalk(self._config)
        #
        # TODO: walk reads the whole tree under self.path, regardless if we want recursion
        # or not. we can obviously do better! this is just a simple first pass.
        #
        path = self.path
        lst = walk.listdir(path=path, default=[])
        if files_only:
            lst = [_ for _ in lst if _[1] is True]
        if dirs_only:
            lst = [_ for _ in lst if _[1] is False]
        if recurse:
            lst = [_[0] for _ in lst]
        else:
            lst = [_[0][_[0].rfind("/") + 1 :] for _ in lst]
            lst = [_ for _ in lst if _.find("/") == -1]
        return lst

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
            ld = self.listdir(default=None)
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
