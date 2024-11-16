# pylint: disable=C0114
from typing import Dict, List
import os
import json
from typing import NewType
from json import JSONDecodeError
from abc import ABC, abstractmethod
from csvpath import CsvPath
from ..util.exceptions import InputException
from ..util.error import ErrorHandler
from ..util.metadata_parser import MetadataParser
from ..util.reference_parser import ReferenceParser
from .paths_registrar import PathsRegistrar

# types added just for clarity
NamedPathsName = NewType("NamedPathsName", str)
Csvpath = NewType("Csvpath", str)
Identity = NewType("Identity", str)


class CsvPathsManager(ABC):
    """holds paths (the path itself, not a file name or reference) in a named set.
    this allows all paths to be run as a unit, with the results manager holding
    the set's outcomes."""

    @abstractmethod
    def add_named_paths_from_dir(self, *, directory: str, name: str = None) -> None:
        """adds named paths found in a directory. files with multiple paths
        will be handled. if name is not None the named paths for all files
        in the directory will be keyed by name.
        """

    @abstractmethod
    def add_named_paths_from_file(self, *, name: str, file_path: str) -> None:
        """adds one or more csvpaths from a single file. the
        contents of the file is straight cvspath, not json."""

    @abstractmethod
    def add_named_paths_from_json(self, file_path: str) -> None:
        """replaces the named paths dict with a dict found in a JSON file. lists
        of paths are keyed by names."""

    @abstractmethod
    def set_named_paths(self, np: Dict[str, List[str]]) -> None:
        """overwrites"""

    @abstractmethod
    def add_named_paths(
        self,
        *,
        name: str,
        paths: List[str] = None,
        from_file: str = None,
        from_dir: str = None,
        from_json: str = None,
    ) -> None:
        """aggregates the path list under the name. if there is no
        existing list of paths, the name will be added. otherwise,
        the lists will be joined. duplicates are not added.
        - name + paths adds all the paths in the list under the name
        - name + from_file adds all the paths in the file under the name
        - name + from_dir adds all paths in all files in the dir under the name or the file name
        - name + from_json adds the paths contained in the files named in the json dictionary
        """

    @abstractmethod
    def get_named_paths(self, name: str) -> List[str]:  # pylint: disable=C0116
        """returns the csvpaths grouped under the name. remember
        that your csvpaths are in ordered list that determines the
        execution order. when the paths are run serially each csvpath
        completes before the next starts, in the list order. when you
        run the paths breadth-first, line-by-line, the csvpaths are
        applied to each line in the order of the list.
        """

    @abstractmethod
    def remove_named_paths(self, name: str) -> None:  # pylint: disable=C0116
        pass  # pragma: no cover

    @abstractmethod
    def has_named_paths(self, name: str) -> bool:  # pylint: disable=C0116
        pass  # pragma: no cover

    @abstractmethod
    def number_of_named_paths(self) -> bool:  # pylint: disable=C0116
        pass  # pragma: no cover

    @property
    @abstractmethod
    def named_paths_names(self) -> list[str]:
        pass


class PathsManager(CsvPathsManager):  # pylint: disable=C0115, C0116
    MARKER: str = "---- CSVPATH ----"

    def __init__(self, *, csvpaths, named_paths=None):
        if named_paths is None:
            named_paths = {}
        self.named_paths = named_paths
        self.csvpaths = csvpaths
        self._registrar = PathsRegistrar(self.csvpaths.config)

    @property
    def registrar(self) -> PathsRegistrar:
        return self._registrar

    def set_named_paths(self, np: Dict[str, List[str]]) -> None:
        for name in np:
            if not isinstance(np[name], list):
                ie = InputException("Named-path names must key a list of csvpath")
                ErrorHandler(csvpaths=self.csvpaths).handle_error(ie)
                return
        self.named_paths = np
        for k, v in np.items():
            self.add_named_paths(name=k, paths=v)
        self.csvpaths.logger.info(
            "Set named-paths collection to %s groups of csvpaths", len(np)
        )

    def add_named_paths_from_dir(self, *, directory: str, name: str = None) -> None:
        if directory is None:
            ie = InputException("Named paths collection name needed")
            ErrorHandler(csvpaths=self.csvpaths).handle_error(ie)
        if os.path.isdir(directory):
            dlist = os.listdir(directory)
            base = directory
            for p in dlist:
                if p[0] == ".":
                    continue
                if p.find(".") == -1:
                    continue
                ext = p[p.rfind(".") + 1 :].strip().lower()
                if ext not in self.csvpaths.config.csvpath_file_extensions:
                    continue
                path = os.path.join(base, p)
                aname = name
                if aname is None:
                    aname = self._name_from_name_part(p)
                self.add_named_paths_from_file(name=aname, file_path=path)
        else:
            ie = InputException("Dirname must point to a directory")
            ErrorHandler(csvpaths=self.csvpaths).handle_error(ie)

    def add_named_paths_from_file(self, *, name: str, file_path: str) -> None:
        self.csvpaths.logger.debug("Reading csvpaths file at %s", file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            cp = f.read()
            _ = [
                apath.strip()
                for apath in cp.split(PathsManager.MARKER)
                if apath.strip() != ""
            ]
            self.csvpaths.logger.debug("Found %s csvpaths in file", len(_))
            self.add_named_paths(name=name, paths=_)

    def add_named_paths_from_json(self, file_path: str) -> None:
        try:
            self.csvpaths.logger.debug("Opening JSON file at %s", file_path)
            with open(file_path, encoding="utf-8") as f:
                j = json.load(f)
                self.csvpaths.logger.debug("Found JSON file with %s keys", len(j))
                for k in j:
                    self.registrar.store_json_paths_file(k, file_path)
                    v = j[k]
                    for f in v:
                        self.add_named_paths_from_file(name=k, file_path=f)
        except (OSError, ValueError, TypeError, JSONDecodeError) as ex:
            self.csvpaths.logger.error(f"Error: cannot load {file_path}: {ex}")
            ErrorHandler(csvpaths=self.csvpaths).handle_error(ex)

    def add_named_paths(
        self,
        *,
        name: str,
        paths: List[str] = None,
        from_file: str = None,
        from_dir: str = None,
        from_json: str = None,
    ) -> None:
        if from_file is not None:
            return self.add_named_paths_from_file(name=name, file_path=from_file)
        elif from_dir is not None:
            return self.add_named_paths_from_dir(name=name, directory=from_dir)
        elif from_json is not None:
            return self.add_named_paths_from_json(file_path=from_json)

        if not isinstance(paths, list):
            ie = InputException(
                """Paths must be a list of csvpaths.
                                 If you want to load a file use add_named_paths_from_file or
                                 set_named_paths_from_json."""
            )
            ErrorHandler(csvpaths=self.csvpaths).handle_error(ie)
        self.csvpaths.logger.debug("Adding csvpaths to named-paths group %s", name)
        #
        # assure the name-paths name folder
        # create an-all-in-one file
        # assure a manifest
        # write the fingerprint and timestamp in manifest
        # return path to all-in-one file
        #
        if name in self.named_paths:
            for p in paths:
                if p in self.named_paths[name]:
                    self.csvpaths.logger.debug(
                        "csvpaths %s already exists in named-paths group %s", p, name
                    )
                    pass
                else:
                    self.csvpaths.logger.debug("Adding %s to %s", p, name)
                    self.named_paths[name].append(p)
                    self.registrar.register_named_paths(
                        name=name, paths=self.named_paths[name]
                    )
        else:
            for _ in paths:
                self.csvpaths.logger.debug("Adding %s to %s", _, name)
            self.registrar.register_named_paths(name=name, paths=paths)
            self.named_paths[name] = paths

    #
    # ========================
    #
    # adding ref handling for the form: $many.csvpaths.food
    # which is equiv to: many#food
    #
    def get_named_paths(self, name: str) -> List[Csvpath]:
        ret = None
        npn = None
        identity = None
        if name.startswith("$"):
            ref = ReferenceParser(name)
            if ref.datatype != ReferenceParser.CSVPATHS:
                raise InputException(
                    f"Reference datatype must be {ReferenceParser.CSVPATHS}"
                )
            npn = ref.root_major
            identity = ref.name_one
        else:
            npn, identity = self._paths_name_path(name)
        self.load_named_paths_name_if(npn)
        #
        # we need to be able to grab paths up to and starting from like this:
        #   $many.csvpaths.food:to
        #   $many.csvpaths.food:from
        #
        if identity is None and npn in self.named_paths:
            ret = self.named_paths[npn]
        elif identity is not None and identity.find(":") == -1:
            ret = [self._find_one(npn, identity)]
        elif identity is not None:
            i = identity.find(":")
            directive = identity[i:]
            identity = identity[0:i]
            if directive == ":to":
                ret = self._get_to(npn, identity)
            elif directive == ":from":
                ret = self._get_from(npn, identity)
            else:
                raise InputException(
                    f"Reference directive must be :to or :from, not {directive}"
                )
        #
        # if not in self.named_paths we would return None here
        # need to instead look to the named_paths dir to see what
        # has been registered
        #
        return ret

    def load_named_paths_name_if(self, name: str) -> None:
        if name not in self.named_paths:
            #
            # see if we have it in the central dir
            #
            path = self.registrar.named_paths_home(name)
            s = ""
            grp = os.path.join(path, "group.csvpaths")
            if os.path.exists(grp):
                with open(grp, "r", encoding="utf-8") as file:
                    s = file.read()
            cs = s.split("---- CSVPATH ----")
            cs = [s for s in cs if s.strip() != ""]
            # if someone put a new group.csvpaths file by hand we want to
            # capture its fingerprint for future reference.
            self.registrar.update_manifest_if(name=name)
            self.named_paths[name] = cs

    def _paths_name_path(self, pathsname) -> tuple[NamedPathsName, Identity]:
        specificpath = None
        i = pathsname.find("#")
        if i > 0:
            specificpath = pathsname[i + 1 :]
            pathsname = pathsname[0:i]
        return (pathsname, specificpath)

    def _get_to(self, npn: NamedPathsName, identity: Identity) -> list[Csvpath]:
        ps = []
        paths = self._get_identified_paths_in(npn)
        for path in paths:
            ps.append(path[1])
            if path[0] == identity:
                break
        return ps

    def _get_from(self, npn: NamedPathsName, identity: Identity) -> list[Csvpath]:
        ps = []
        paths = self._get_identified_paths_in(npn)
        for path in paths:
            if path[0] != identity and len(ps) == 0:
                continue
            ps.append(path[1])
        return ps

    def _get_identified_paths_in(
        self, nps: NamedPathsName
    ) -> list[tuple[Identity, Csvpath]]:
        paths = self.get_named_paths(nps)
        idps = []
        for path in paths:
            c = CsvPath()
            MetadataParser(c).extract_metadata(instance=c, csvpath=path)
            idps.append((c.identity, path))
        return idps

    def _find_one(self, npn: NamedPathsName, identity: Identity) -> Csvpath:
        if npn is not None:
            paths = self._get_identified_paths_in(npn)
            for path in paths:
                if path[0] == identity:
                    return path[1]
        raise InputException(
            f"Path identified as '{identity}' must be in the group identitied as '{npn}'"
        )

    #
    #
    # ========================
    #
    #

    @property
    def named_paths_names(self) -> list[str]:
        path = self.registrar.named_paths_dir
        names = [n for n in os.listdir(path) if not n.startswith(".")]
        return names

    def remove_named_paths(self, name: str) -> None:
        if name in self.named_paths:
            del self.named_paths[name]
        else:
            raise InputException("{name} not found")

    def has_named_paths(self, name: str) -> bool:
        return self.get_named_paths(name)

    def number_of_named_paths(self) -> bool:
        return len(self.named_paths)  # pragma: no cover

    def _name_from_name_part(self, name):
        i = name.rfind(".")
        if i == -1:
            pass
        else:
            name = name[0:i]
        return name
