# pylint: disable=C0114
import os
import shutil
from pathlib import Path
from .config import Config
from .s3.s3_nos import S3Do
from .azure.azure_nos import AzureDo
from .sftp.sftp_nos import SftpDo
from .gcs.gcs_nos import GcsDo


class Nos:
    def __init__(self, path, config: Config = None):
        self._path = path
        self._do = None
        self._config = config

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, p: str) -> None:
        if self._protocol_mismatch(p):
            self._do = None
        self._path = p
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
                self._do = S3Do(self.path)
            elif self.path.startswith("sftp://"):
                self._do = SftpDo(self.path)
            elif self.path.startswith("azure://"):
                self._do = AzureDo(self.path)
            elif self.path.startswith("gs://"):
                self._do = GcsDo(self.path)
            else:
                self._do = FileDo(self.path)
        return self._do

    @property
    def sep(self) -> str:
        return "/" if self.path.find("\\") == -1 else os.sep

    def join(self, name: str) -> str:
        return self.do.join(name)

    def remove(self) -> None:
        self.do.remove()

    def exists(self) -> bool:
        return self.do.exists()

    def dir_exists(self) -> bool:
        return self.do.dir_exists()

    def physical_dirs(self) -> bool:
        """True if dirs may exist.
        False if there is no concept of dirs
        that are independent from objects.
        Cloud objects stores like S3 are the
        latter.
        """
        return self.do.physical_dirs()

    def rename(self, new_path: str) -> None:
        self.do.rename(new_path)

    def copy(self, new_path) -> None:
        self.do.copy(new_path)

    def makedirs(self) -> None:
        self.do.makedirs()

    def makedir(self) -> None:
        self.do.makedir()

    def listdir(self) -> list[str]:
        return self.do.listdir()

    def isfile(self) -> bool:
        return self.do.isfile()


class FileDo:
    def __init__(self, path):
        self.path = path

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

    def listdir(self) -> list[str]:
        return os.listdir(self.path)

    def isfile(self) -> bool:
        return os.path.isfile(self.path)
