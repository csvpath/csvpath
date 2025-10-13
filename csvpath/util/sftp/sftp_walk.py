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
            _ = None
            if p[0] == path:
                _ = p[0]
            else:
                _ = f"{path}/{p[0]}"
            if p[1] is True:
                self._config.sftp_client.remove(_)
            else:
                self._config.sftp_client.rmdir(_)

    def listdir(
        self, *, path, default=None, origin: str = None, recurse: bool = True
    ) -> list[[str, bool]]:
        try:
            if origin is None:
                origin = path.lstrip("/")
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
                if not file and recurse is True:
                    names += self.listdir(path=p, default=[], origin=origin)
            for i, name in enumerate(names):
                names[i] = (
                    (name[0][len(origin) + 1 :], name[1])
                    if name[0].startswith(origin)
                    else name
                )
            return names
        except OSError:
            return default
