# pylint: disable=C0114
import paramiko
import stat
from csvpath import CsvPaths
from csvpath.util.box import Box
from ..path_util import PathUtility as pathu
from .sftp_config import SftpConfig
from .sftp_walk import SftpWalk


#
# apr 2026. this class now does 1x retry to attempt to manage sketchy
# network conditions. it covers SftpWalk and fingerprinter. it does not
# cover the read and write classes. retrying a simple atomic operation
# feels reasonable. retrying a read or write feels potentially less
# safe and less like something we should cover for, rather than draw
# attention to.
#
class SftpDo:
    def _csvpath_config(self):
        _csvpathconfig = Box().get(Box.CSVPATHS_CONFIG)
        #
        # if none, we may not be in a context closely tied to a CsvPaths.
        # e.g. FP. so we create a new csvpaths just for the config. it will
        # be identical to any csvpaths in this project unless the other
        # csvpaths were long-lived and had programmatic changes.
        #
        if _csvpathconfig is None:
            _csvpathconfig = CsvPaths().config
            Box().add(Box.CSVPATHS_CONFIG, _csvpathconfig)
        return _csvpathconfig

    @property
    def _config(self):
        return self._cfg

    @_config.setter
    def _config(self, cfg: SftpConfig) -> None:
        self._cfg = cfg

    @property
    def sep(self) -> str:
        return "/"

    def __init__(self, path, setup: bool = True):
        self._path = None
        self._orig_path = None
        # self._server_part = None
        self._csvpathconfig = None
        #
        # primarily for the case of setting up using ServerConfig, we may
        # not want to do SftpConfig stuff here. we'll take the path, tho
        # since that's just a given.
        #
        if setup is True:
            self.setup(path)
        else:
            self.path = path

    def setup(self, path: str = None) -> None:
        config = self._csvpath_config()
        # self._server_part = f"sftp://{config.get(section='sftp', name='server')}:{config.get(section='sftp', name='port')}"
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
        #
        # keep the orig because we strip off the protocol.
        # this could become a problem.
        #
        self._orig_path = p
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

    def join(self, name: str) -> str:
        return f"{self._orig_path}/{name}"

    def remove(self, *, retry=True) -> None:
        try:
            if self.path == "/":
                raise ValueError("Cannot remove the root")
            if self.isfile():
                self._config.sftp_client.remove(self.path)
            else:
                walk = SftpWalk(self._config)
                walk.remove(self.path)
        except Exception:
            if retry is True:
                self._config.reset()
                self.remove(retry=False)
                return None
            raise

    def listdir(
        self,
        *,
        files_only: bool = False,
        recurse: bool = False,
        dirs_only: bool = False,
        default=None,
        retry=True,
    ) -> list[str]:
        try:
            if files_only is True and dirs_only is True:
                raise ValueError("Cannot list with neither files nor dirs")
            walk = SftpWalk(self._config)
            path = self.path
            lst = walk.listdir(path=path, default=[], recurse=recurse)
            if files_only is True:
                lst = [_ for _ in lst if _[1] is True]
            if dirs_only is True:
                lst = [_ for _ in lst if _[1] is False]
            if recurse is True:
                lst = [_[0] for _ in lst]
            else:
                lst2 = []
                path = path.lstrip("/")
                for _ in lst:
                    t = _[0]
                    t = t.lstrip("/")
                    if t.startswith(path):
                        t = t[len(path) + 1 :]
                    if t.count("/") > 0:
                        continue
                    lst2.append(t)
                lst = lst2
            return lst
        except Exception:
            if retry is True:
                self._config.reset()
                return self.listdir(
                    files_only=files_only,
                    recurse=recurse,
                    dirs_only=dirs_only,
                    default=default,
                    retry=False,
                )
            raise

    def copy(self, to, *, retry=True) -> None:
        try:
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
        except Exception:
            if retry is True:
                self._config.reset()
                self.copy(to, retry=False)
                return None
            raise

    def exists(self, *, retry=True) -> bool:
        try:
            path = self.path
            self._config.sftp_client.stat(path)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            if retry is True:
                self._config.reset()
                return self.exists(retry=False)
            raise

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
            return ld is not None
            """
        except FileNotFoundError:
            return False

    def isdir(self, path, *, retry=True) -> bool:
        try:
            attr = self._config.sftp_client.stat(path)
            return stat.S_ISDIR(attr.st_mode)
        except FileNotFoundError:
            return False
        except Exception:
            if retry is True:
                self._config.reset()
                return self.isdir(path, retry=False)

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
    """
    #
    # we handle stripping the protocol and server in self.path = path using pathu
    #
    def _strip_location(self, url_or_path:str) -> str:
        if url_or_path is None:
            raise ValueError("url_or_path cannot be None")
        if not isinstance(url_or_path, str):
            return ValueError("url_or_path must be a string")
        url_or_path = url_or_path.strip()
        if url_or_path.find("://") > -1 and url_or_path.startswith("sftp://") == -1:
            raise ValueError("url_or_path must begin with sftp://")
        path = url_or_path
        if url_or_path.startswith("sftp://"):
            path = url_or_path[7:]
            i = path.find("/")
            if i == -1:
                raise ValueError("url_or_path must have a / after the network location")
            path = path[i:]
        return path

    def stripped(self) -> str:
        return self._strip_location(self.path)
    """

    def _isfile(self, path, *, retry=True) -> bool:
        if path is None:
            raise ValueError("Path cannot be None")
        try:
            #
            # typically we remove protocol, location, and port in setting path; however,
            # it has been seen that in at least one case we still need to failsafe of
            # doing it (again) here.
            #
            path = pathu.stripp(path)
            c = self._config
            sc = c.sftp_client
            attr = sc.stat(path)
            return stat.S_ISREG(attr.st_mode)
        except FileNotFoundError:
            return False
        except Exception:
            if retry is True:
                self._config.reset()
                return self._isfile(path, retry=False)
            raise

    def rename(self, new_path: str, *, retry=True) -> None:
        try:
            np = pathu.resep(new_path, hint="posix")
            np = pathu.stripp(np)
            self._config.sftp_client.rename(self.path, np)
        except FileNotFoundError:
            raise
        except (IOError, PermissionError):
            raise RuntimeError(f"Failed to rename {self.path} to {new_path}")
        except Exception:
            if retry is True:
                self._config.reset()
                self.rename(new_path, retry=False)

    def makedirs(self) -> None:
        lst = self.path.split("/")
        path = ""
        for p in lst:
            path = f"{p}" if path == "" else f"{path}/{p}"
            self._mkdirs(path)

    def _mkdirs(self, path, *, retry=False):
        try:
            self._config.sftp_client.mkdir(path)
        except OSError:
            ...
            # TODO: should log
        except IOError:
            ...
            # TODO: should log
        except Exception:
            if retry is True:
                self._config.reset()
                self._mkdirs(path, retry=False)

    def makedir(self) -> None:
        self.makedirs()
