# pylint: disable=C0114
import os
import paramiko
import stat
from stat import S_ISDIR, S_ISREG
from csvpath import CsvPaths
from csvpath.util.box import Box
from ..path_util import PathUtility as pathu
from .sftp_config import SftpConfig
from .sftp_walk import SftpWalk


class SftpDo:
    @property
    def _config(self):
        if self._cfg is None:
            self._cfg = Box().get(Box.CSVPATHS_CONFIG)
            #
            # if none, we may not be in a context closely tied to a CsvPaths.
            # e.g. FP. so we create a new csvpaths just for the config. it will
            # be identical to any csvpaths in this project unless the other
            # csvpaths were long-lived and had programmatic changes.
            #
            if self._cfg is None:
                self._cfg = CsvPaths().config
                Box().add(Box.CSVPATHS_CONFIG, self._cfg)
        return self._cfg

    @property
    def sep(self) -> str:
        return "/"

    @_config.setter
    def _config(self, cfg: SftpConfig) -> None:
        self._cfg = cfg

    def __init__(self, path):
        self._path = None
        self._server_part = None
        self._config = None
        self.setup(path)

    def setup(self, path: str = None) -> None:
        config = self._config
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

    @path.setter
    def path(self, p) -> None:
        p = pathu.resep(p, hint="posix")
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
        if files_only is True:
            lst = [_ for _ in lst if _[1] is True]
        if dirs_only is True:
            lst = [_ for _ in lst if _[1] is False]
        if recurse is True:
            lst = [_[0] for _ in lst]
        else:  #
            lst2 = []
            if path.startswith("/"):
                path = path[1:]
            for _ in lst:
                t = _[0]
                if t.startswith("/"):
                    t = t[1:]
                if path != "" and not t.startswith(path):
                    raise ValueError("Expecting contents to start with base path")
                if path != "":
                    t = t[len(path) + 1 :]
                if t.count("/") > 0:
                    continue
                lst2.append(t)
            lst = lst2
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
            allow_agent=False,
            look_for_keys=False,
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
            #
            # list dir now returns [] by default, for better or worse. rather than
            # change what seems to work fine in most cases we're taking the same
            # stat-based approach as in isfile(). let's see how that does.
            #
            return self.isdir(self.path)
            """
            ld = self.listdir(default=None)
            print(f"sftpnos: dir_exists: path: {self.path}: ld: {ld}: is dir: {self._isdir(self.path)}")
            return ld is not None
            """
        except FileNotFoundError:
            return False

    def isdir(self, path) -> bool:
        try:
            attr = self._config.sftp_client.stat(path)
            return stat.S_ISDIR(attr.st_mode)
        except FileNotFoundError:
            return False

    def physical_dirs(self) -> bool:
        return True

    def isfile(self) -> bool:
        return self._isfile(self.path)

    #
    # the old method worked fine with SFTPPlus but fails on SFTPGo.
    # i thought that there was an issue with the stat approach, but i
    # don't remember -- it's been months. the replacement works fine
    # on SFTPGo. haven't tried SFTPPlus yet because license. leaving
    # here in case this comes back up. worst case we might need a
    # double check or server specific approach, but that would be
    # probably not less brittle and would be ugly.
    #
    """
    def _isfile(self, path) -> bool:
        try:
            self._config.sftp_client.open(path, "r")
            r = True
        except (FileNotFoundError, OSError):
            r = False
        return r
    """

    def _isfile(self, path) -> bool:
        try:
            attr = self._config.sftp_client.stat(path)
            return stat.S_ISREG(attr.st_mode)
        except FileNotFoundError:
            return False

    def rename(self, new_path: str) -> None:
        try:
            np = pathu.resep(new_path, hint="posix")
            np = pathu.stripp(np)
            self._config.sftp_client.rename(self.path, np)
        except FileNotFoundError:
            raise
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
