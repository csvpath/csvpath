import os
from pathlib import PurePosixPath


class PathUtility:
    @classmethod
    def norm(cls, apath: str, stripp=False) -> str:
        #
        # if stripp is True we remove the protocol and server name
        #
        if apath is None:
            return None
        if stripp is True:
            apath = cls.stripp(apath)
        apath = os.path.normpath(os.path.normcase(apath))
        #
        # exp!
        #
        apath = str(PurePosixPath(apath))
        return apath

    @classmethod
    def resep(cls, path: str, *, hint=None) -> str:
        sep, notsep = cls.sep(path, hint=hint)
        return path.replace(notsep, sep)

    @classmethod
    def lresep(cls, paths: list) -> list:
        return [cls.resep(path) for path in paths]

    @classmethod
    def sep(cls, path: str, *, hint: str = None) -> tuple[str, str]:
        if path is None:
            raise ValueError("Path cannot be None")
        #
        # returns a tuple of sep and not-sep. e.g. for Windows:
        # ("\\", "/")
        #
        osname = os.name if hint is None else hint
        if path.find("://") > -1:
            return ("/", "\\")
        elif osname in [
            "win",
            "windows",
            "nt",
        ]:
            return ("\\", "/")
        else:
            return ("/", "\\")

    @classmethod
    def dir_name(cls, apath: str) -> str:
        parts = cls.parts(apath)
        path = ""
        if len(parts) > 1:
            last = parts[len(parts) - 1]
            path = apath[0 : apath.rfind(last)]
            path = path.rstrip("/")
            path = path.rstrip("\\")
        return path

    @classmethod
    def parts(cls, apath: str) -> list[str]:
        apath = cls.resep(apath)
        parts = []
        i = apath.find("://")
        hint = None
        if i > -1:
            prot = apath[0:i]
            parts.append(prot)
            apath = apath[i + 3 :]
            hint = "/"
        sep = cls.sep(apath, hint=hint)
        for s in apath.split(sep[0]):
            s = s.strip()
            if s != "":
                parts.append(s)
        return parts

    @classmethod
    def stripp(cls, apath: str) -> str:
        #
        # removes protocol + location, incl. port.
        #
        i = apath.find("://")
        j = -1
        if i > -1:
            apath = apath[i + 3 :]
            j = apath.find("/")
            if j > -1:
                apath = apath[j + 1 :]
        return apath

    @classmethod
    def location(cls, path: str):
        #
        # find the location of a non-local path. i.e. in sftp://mylocation:22/a file.txt
        # the return would be mylocation:22
        #
        i = path.find("://")
        if i == -1:
            return None
        path = path[i + 3 :]
        i = path.find("/")
        if i == -1:
            return path
        return path[0:i]

    @classmethod
    def location_and_port(cls, path: str) -> tuple[str, int]:
        #
        # find the location of a non-local path. \
        #
        # in sftp://mylocation:22/a file.txt  the return would be (mylocation,22)
        # in sftp://mylocation/a file.txt  the return would be (mylocation,None)
        #
        location = cls.location(path)
        if location is None:
            return None
        i = location.find(":")
        if i == -1:
            return (location, None)
        port = location[i + 1 :]
        return location[0:i], int(port)

    @classmethod
    def equal(cls, pathone: str, pathtwo: str, stripp=False) -> bool:
        #
        # if stripp is True we remove the protocol and server name
        #
        p1 = cls.norm(pathone, stripp)
        p2 = cls.norm(pathtwo, stripp)
        return p1 == p2
