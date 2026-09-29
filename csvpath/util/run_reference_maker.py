from csvpath.util.config import Config
from csvpath.util.references.reference_parser import ReferenceParser


class RunReferenceMaker:
    #
    # we will remove any leading archive path and/or named-paths name.
    # if given /data/archive/orders/x/y/2026-01-01_00-00-00
    # we return $orders.results.x/y/2026-01-01_00-00-00.
    #
    # this class is not foolproof: if you have a fully qualified crt
    # string and a relative archive path it will be trimmed correctly
    # iff the archive path is not found multiple times in the crt.
    # we can't expect crt strings to always be a run home relative to
    # the name home, but we will make the assumption that there won't
    # a path like /Users/archive/csvpaths/data/archive. obviously that
    # could happen, but isn't likely. we'll have to document the
    # requirement.
    #
    @classmethod
    def _trim_archive_name_if(cls, *, archive: str, home: str) -> str:
        if home.startswith(archive):
            home = home[len(archive) + 1 :]
            return home
        elif home.find(archive) > -1:
            home = home[home.find(archive) + len(archive) + 1 :]
            return home
        return home

    @classmethod
    def _trim_archive_if(cls, *, config: Config, home: str) -> str:
        archive = cls.config.get(section="results", name="archive")
        return cls._trim_archive_name_if(archive=archive, home=home)

    @classmethod
    def _trim_results_name_if(cls, *, name: str, home: str) -> str:
        if home.startswith(name):
            home = home[len(name) + 1 :]
        return home

    @classmethod
    def make_run_reference(cls, *, config: Config, pathsname: str, crt: str) -> str:
        if config is None:
            raise ValueError("Config cannot be None")
        archive = config.get(section="results", name="archive")
        return cls.run_reference(archive=archive, pathsname=pathsname, crt=crt)

    @classmethod
    def run_reference(cls, *, archive: str, pathsname: str, crt: str) -> str:
        if archive is None:
            raise ValueError("archive cannot be None")
        if pathsname is None:
            raise ValueError("pathsname cannot be None")
        if crt is None:
            raise ValueError("crt cannot be None")
        if "$" in pathsname:
            pathsname = ReferenceParser(pathsname).root_major
        arch = cls._trim_archive_name_if(archive=archive, home=crt)
        name = cls._trim_results_name_if(name=pathsname, home=arch)
        return f"${pathsname}.results.{name}"
