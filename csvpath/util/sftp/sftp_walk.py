# pylint: disable=C0114
from stat import S_ISREG
from .sftp_config import SftpConfig


class SftpWalk:
    def __init__(self, config: SftpConfig) -> None:
        self._config = config

    def remove(self, path):
        self._config.sftp_client.chdir(".")
        lst = [(path, False)]
        lst += self.listdir(path=path, default=lst)
        lst.reverse()
        for p in lst:
            if p[1] is True:
                self._config.sftp_client.remove(p[0])
            else:
                self._config.sftp_client.rmdir(p[0])

    def listdir(self, *, path, default=None) -> list[[str, bool]]:
        try:
            self._config.sftp_client.chdir(".")
            attributes = self._config.sftp_client.listdir_attr(path)
            names = []
            for entry in attributes:
                p = entry.filename
                if path != "/":
                    p = f"{path}/{p}"
                p = p.lstrip("/")
                file = S_ISREG(entry.st_mode)
                names.append((p, file))
                if not file:
                    names += self.listdir(path=p, default=[])
            return names
        except OSError:
            return default
