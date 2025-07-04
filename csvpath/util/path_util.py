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
            parts.append(s)
        return parts

    @classmethod
    def stripp(cls, apath: str) -> str:
        i = apath.find("://")
        j = -1
        if i > -1:
            apath = apath[i + 3 :]
            j = apath.find("/")
            if j > -1:
                apath = apath[j + 1 :]
        return apath

    @classmethod
    def equal(cls, pathone: str, pathtwo: str, stripp=False) -> bool:
        #
        # if stripp is True we remove the protocol and server name
        #
        p1 = cls.norm(pathone, stripp)
        p2 = cls.norm(pathtwo, stripp)
        return p1 == p2
