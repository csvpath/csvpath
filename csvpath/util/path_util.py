import os


class PathUtility:
    @classmethod
    def norm(cls, apath: str, stripp=False) -> str:
        # if stripp is True we remove the protocol and server name
        if apath is None:
            return None
        apath = os.path.normpath(os.path.normcase(apath))
        if stripp:
            apath = cls.stripp(apath)
        return apath

    """
    # splits https://aserver/my/file/is/here into ["https","aserver","my/file/is/here"]
    # add test before using. not needed today.
    def parts(cls, apath:str) -> list[str]:
        parts = []
        i = apath.find("://")
        if i > -1:
            prot = apath[0:i]
            parts.append(prot)
            apath = apath[i+3:]
            j = apath.find("/")
            parts.append(apath[j+1:]
        return parts
    """

    @classmethod
    def stripp(cls, apath: str) -> str:
        i = apath.find("://")
        if i > -1:
            apath = apath[i + 3 :]
            i = apath.find("/")
            if i > -1:
                apath = apath[i + 1 :]
        return apath

    @classmethod
    def equal(cls, pathone: str, pathtwo: str) -> bool:
        return cls.norm(pathone) == cls.norm(pathtwo)
