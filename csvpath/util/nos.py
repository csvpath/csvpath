# pylint: disable=C0114
import os
import shutil
from pathlib import Path
from .config import Config
from .path_util import PathUtility as pathu
from .class_loader import ClassLoader


class Nos:
    def __init__(self, path, config: Config = None):
        self._path = None
        self._do = None
        self._config = config
        self.path = path

    def __str__(self) -> str:
        return f"{type(self)}: do: {self.do}, path: {self.path}"

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, p: str) -> None:
        if self._protocol_mismatch(p):
            self._do = None
        if p is not None:
            p = pathu.resep(p)
        self._path = p
        if p is None:
            self._do = None
        else:
            self.do.path = p

    def _protocol_mismatch(self, path) -> bool:
        if path is None:
            return True
        if self._path is None:
            return True
        i = path.find("://")
        j = self._path.find("://")
        if i == j == -1:
            return False
        if path[0:i] == self._path[0:j]:
            return False
        return True

    #
    # subclass removes ftps://hostname:port if found, or any similar
    # protocol. s3:// does not need this.
    #
    def strip_protocol(self, path: str) -> str:
        return path

    @property
    def do(self):
        if self.path is not None and self._do is None:
            if self.path.startswith("s3://"):
                instance = ClassLoader.load(
                    "from csvpath.util.s3.s3_nos import S3Do",
                    args=[self.path],
                )
                self._do = instance
            elif self.path.startswith("sftp://"):
                instance = ClassLoader.load(
                    "from csvpath.util.sftp.sftp_nos import SftpDo",
                    args=[self.path],
                )
                self._do = instance
            elif self.path.startswith("azure://"):
                instance = ClassLoader.load(
                    "from csvpath.util.azure.azure_nos import AzureDo",
                    args=[self.path],
                )
                self._do = instance
            elif self.path.startswith("gs://"):
                instance = ClassLoader.load(
                    "from csvpath.util.gcs.gcs_nos import GcsDo",
                    args=[self.path],
                )
                self._do = instance
            #
            # we don't have an https backend at this time, just support for reading files from https.
            # that means we don't have a backend way to find sep. there may be other impacts too.
            #
            else:
                self._do = FileDo(self.path)
        return self._do

    @property
    def sep(self) -> str:
        #
        # should this be checking what our self.do is to see if we need
        # posix/cloud seps?
        #
        # return "/" if self.path.find("\\") == -1 else os.sep
        return self.do.sep

    def join(self, name: str) -> str:
        return self.do.join(name)

    def remove(self) -> None:
        self.do.remove()

    def exists(self) -> bool:
        return self.do.exists()

    def dir_exists(self) -> bool:
        return self.do.dir_exists()

    def physical_dirs(self) -> bool:
        """True if dirs can exist independently. False if there is no concept of dirs
        that are independent from objects. Cloud objects stores like S3 are the latter."""
        return self.do.physical_dirs()

    def rename(self, new_path: str) -> None:
        self.do.rename(new_path)

    def copy(self, new_path) -> None:
        self.do.copy(new_path)

    def makedirs(self) -> None:
        self.do.makedirs()

    def makedir(self) -> None:
        self.do.makedir()

    def listdir(
        self,
        *,
        files_only: bool = False,
        recurse: bool = False,
        dirs_only: bool = False,
    ) -> list[str]:
        return self.do.listdir(
            files_only=files_only, recurse=recurse, dirs_only=dirs_only
        )

    def isfile(self) -> bool:
        return self.do.isfile()


class FileDo:
    def __init__(self, path):
        self._path = None
        path = pathu.resep(path)
        self.path = path

    @property
    def sep(self) -> str:
        return os.sep

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, p: str) -> None:
        self._path = pathu.resep(p)

    def remove(self) -> None:
        isf = os.path.isfile(self.path)
        if isf:
            os.remove(self.path)
        else:
            shutil.rmtree(self.path)

    def copy(self, to) -> None:
        shutil.copy(self.path, to)

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def dir_exists(self) -> bool:
        ret = os.path.exists(self.path)
        return ret

    def physical_dirs(self) -> bool:
        return True

    def rename(self, new_path: str) -> None:
        os.rename(self.path, new_path)

    def makedirs(self) -> None:
        os.makedirs(self.path)

    def makedir(self) -> None:
        Path(self.path).mkdir(parents=True, exist_ok=True)

    def isfile(self) -> bool:
        return os.path.isfile(self.path)

    #
    # listdir returns files in filesystem order, i.e. unordered.
    #
    def listdir(
        self,
        *,
        files_only: bool = False,
        recurse: bool = False,
        dirs_only: bool = False,
    ) -> list[str]:
        if files_only is True and dirs_only is True:
            raise ValueError("Cannot list with neither files nor dirs")
        if recurse is True:
            lst = []
            for root, dirs, files in os.walk(self.path):
                if dirs_only is False:
                    for file in files:
                        lst.append(os.path.join(root, file))  # .replace("//","/")
                if files_only is False:
                    for d in dirs:
                        lst.append(os.path.join(root, d))
            return lst
        paths = os.listdir(self.path)
        if files_only:
            return [_ for _ in paths if os.path.isfile(os.path.join(self.path, _))]
        elif dirs_only:
            return [_ for _ in paths if not os.path.isfile(os.path.join(self.path, _))]
        return paths
