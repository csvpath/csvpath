import os


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
        return apath

    @classmethod
    def resep(cls, path) -> str:
        #
        # in principle we can use '/' in most cases with windows
        # but we didn't start that way and there are at least a
        # couple of corner cases. for now this method doesn't cost
        # us much.
        #
        if path.find("://"):
            path = path.replace("\\", "/")
        if path.startswith("c:"):
            path = path.replace("/", "\\")
        return path

    @classmethod
    def parts(cls, apath: str) -> list[str]:
        # splits https://aserver/my/file/is/here into ["https","aserver","my", "file", "is","here"]
        parts = []
        i = apath.find("://")
        if i > -1:
            prot = apath[0:i]
            parts.append(prot)
            apath = apath[i + 3 :]
            # j = apath.find("/")
            # parts.append(apath[j+1:])
            # apath = apath[j+1:]
        for s in apath.split("/"):
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
