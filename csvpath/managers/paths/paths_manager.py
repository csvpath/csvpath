# pylint: disable=C0114
import os
import json
from typing import NewType
from json import JSONDecodeError
from csvpath import CsvPath
from csvpath.util.exceptions import InputException
from csvpath.util.metadata_parser import MetadataParser
from csvpath.util.reference_parser import ReferenceParser
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.box import Box
from csvpath.util.nos import Nos
from .paths_registrar import PathsRegistrar
from .paths_metadata import PathsMetadata

# types added just for clarity
NamedPathsName = NewType("NamedPathsName", str)
"""@private"""
Csvpath = NewType("Csvpath", str)
"""@private"""
Identity = NewType("Identity", str)
"""@private"""


class PathsManager:
    MARKER: str = "---- CSVPATH ----"

    def __init__(self, *, csvpaths, named_paths=None):
        """@private"""
        self.csvpaths = csvpaths
        """@private"""
        self._registrar = None
        self._nos = None

    @property
    def nos(self) -> Nos:
        if self._nos is None:
            self._nos = Box.STUFF.get("boto_s3_nos")
            if self._nos is None:
                self._nos = Nos(None)
                Box().add("boto_s3_nos", self._nos)
        return self._nos

    #
    # ================== publics =====================
    #
    @property
    def paths_root_manifest_path(self) -> str:
        """@private"""
        r = self.csvpaths.config.get(section="inputs", name="csvpaths")
        p = os.path.join(r, "manifest.json")
        nos = self.nos
        nos.path = r
        if not nos.dir_exists():
            nos.makedirs()
        nos.path = p
        if not nos.exists():
            with DataFileWriter(path=p) as writer:
                writer.write("[]")
        return p

    @property
    def paths_root_manifest(self) -> str:
        """@private"""
        p = self.paths_root_manifest_path
        with DataFileReader(p) as reader:
            return json.load(reader.source)

    @property
    def registrar(self) -> PathsRegistrar:
        """@private"""
        if self._registrar is None:
            self._registrar = PathsRegistrar(self.csvpaths)
        return self._registrar

    def named_paths_home(self, name: NamedPathsName) -> str:
        """@private"""
        home = os.path.join(self.named_paths_dir, name)
        nos = self.nos
        nos.path = home
        b = nos.dir_exists()
        if not b:
            nos.makedirs()
        return home

    def get_named_paths_uuid(self, name: NamedPathsName) -> str:
        if name is None:
            raise ValueError("Paths name cannot be None")
        if name.find("#") > -1:
            name = name[0 : name.find("#")]
        if name.startswith("$"):
            ref = ReferenceParser(name)
            if ref.datatype != ReferenceParser.CSVPATHS:
                raise ValueError(
                    "Must be a reference of type {ReferenceParser.CSVPATHS}"
                )
            name = ref.root_major

        path = self.named_paths_home(name)
        path = os.path.join(path, "manifest.json")
        nos = self.nos
        nos.path = path
        if nos.exists():
            with DataFileReader(path) as reader:
                m = json.load(reader.source)
                return m[len(m) - 1]["uuid"]
        raise ValueError(f"No manifest for path named {name}")

    @property
    def named_paths_dir(self) -> str:
        """@private"""
        return self.csvpaths.config.inputs_csvpaths_path

    def set_named_paths(self, np: dict[NamedPathsName, list[Csvpath]]) -> None:
        for name in np:
            if not isinstance(np[name], list):
                msg = f"{name} does not key a list of csvpaths"
                self.csvpaths.error_manager.handle_error(source=self, msg=msg)
                if self.csvpaths.ecoms.do_i_raise():
                    raise InputException(msg)
                return
        for k, v in np.items():
            self.add_named_paths(name=k, paths=v)
        self.csvpaths.logger.info("Set named-paths to %s groups", len(np))

    def add_named_paths_from_dir(
        self, *, directory: str, name: NamedPathsName = None
    ) -> None:
        if directory is None:
            msg = "Named paths collection name needed"
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            if self.csvpaths.ecoms.do_i_raise():
                raise InputException(msg)
        nos = self.nos
        nos.path = directory
        if not nos.isfile():
            dlist = nos.listdir()
            base = directory
            agg = []
            for p in dlist:
                if p[0] == ".":
                    continue
                if p.find(".") == -1:
                    continue
                ext = p[p.rfind(".") + 1 :].strip().lower()
                if ext not in self.csvpaths.config.csvpath_file_extensions:
                    continue
                path = os.path.join(base, p)
                if name is None:
                    #
                    # add files one by one under their own names
                    #
                    aname = self._name_from_name_part(p)
                    self.add_named_paths_from_file(name=aname, file_path=path)
                else:
                    #
                    # if a name, aggregate all the files
                    #
                    _ = self._get_csvpaths_from_file(path)

                    #
                    # try to find a run-index: N metadata and use it
                    # to try to impose order? we could do this, but it would
                    # be messy and a work-around to avoid making people
                    # use the ordered ways of creating named-paths that
                    # already exist: JSON and all-in-ones
                    #
                    """
                    c = self.csvpaths.csvpath()
                    MetadataParser(c).extract_metadata(instance=c, csvpath=path)
                    """
                    agg += _
            if len(agg) > 0:
                self.add_named_paths(name=name, paths=agg, source_path=directory)
        else:
            msg = "Dirname must point to a directory"
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            if self.csvpaths.ecoms.do_i_raise():
                raise InputException(msg)

    def add_named_paths_from_file(
        self, *, name: NamedPathsName, file_path: str
    ) -> None:
        self.csvpaths.logger.debug("Reading csvpaths file at %s", file_path)
        _ = self._get_csvpaths_from_file(file_path)
        self.add_named_paths(name=name, paths=_, source_path=file_path)

    def add_named_paths_from_json(self, file_path: str) -> None:
        try:
            self.csvpaths.logger.debug("Opening JSON file at %s", file_path)
            with open(file_path, encoding="utf-8") as f:
                j = json.load(f)
                self.csvpaths.logger.debug("Found JSON file with %s keys", len(j))
                for k in j:
                    self.store_json_paths_file(k, file_path)
                    v = j[k]
                    paths = []
                    for f in v:
                        _ = self._get_csvpaths_from_file(f)
                        paths += _
                    self.add_named_paths(name=k, paths=paths, source_path=file_path)
        except (OSError, ValueError, TypeError, JSONDecodeError) as ex:
            self.csvpaths.error_manager.handle_error(source=self, msg=f"{ex}")
            if self.csvpaths.ecoms.do_i_raise():
                raise

    def add_named_paths(
        self,
        *,
        name: NamedPathsName,
        paths: list[Csvpath] = None,
        from_file: str = None,
        from_dir: str = None,
        from_json: str = None,
        source_path: str = None,
    ) -> None:
        if from_file is not None:
            return self.add_named_paths_from_file(name=name, file_path=from_file)
        elif from_dir is not None:
            return self.add_named_paths_from_dir(name=name, directory=from_dir)
        elif from_json is not None:
            return self.add_named_paths_from_json(file_path=from_json)
        if not isinstance(paths, list):
            msg = """Paths must be a list of csvpaths.
                    If you want to load a file use add_named_paths_from_file or
                    set_named_paths_from_json."""
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            if self.csvpaths.ecoms.do_i_raise():
                raise InputException(msg)
            return
        self.csvpaths.logger.debug("Adding csvpaths to named-paths group %s", name)
        for _ in paths:
            self.csvpaths.logger.debug("Adding %s to %s", _, name)
        s = self._str_from_list(paths)
        t = self._copy_in(name, s)
        grp_paths = self.get_identified_paths_in(name, paths=paths)
        ids = [t[0] for t in grp_paths]
        for i, t in enumerate(ids):
            if t is None or t.strip() == "":
                ids[i] = f"{i}"
        mdata = PathsMetadata(self.csvpaths.config)
        mdata.archive_name = self.csvpaths.config.archive_name
        mdata.named_paths_name = name
        nos = self.nos
        nos.path = mdata.named_paths_root
        sep = nos.sep
        mdata.named_paths_home = f"{mdata.named_paths_root}{sep}{name}"
        mdata.group_file_path = f"{mdata.named_paths_home}{sep}group.csvpaths"
        mdata.named_paths = paths
        mdata.named_paths_identities = ids
        mdata.named_paths_count = len(ids)
        mdata.source_path = source_path
        self.registrar.register_complete(mdata)

    #
    # adding ref handling for the form: $many.csvpaths.food
    # which is equiv to: many#food
    #
    def get_named_paths(self, name: NamedPathsName) -> list[Csvpath]:
        self.csvpaths.logger.info("Getting named-paths for %s", name)
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
        if identity is None and self.has_named_paths(npn):
            ret = self._get_named_paths(npn)
        elif identity is not None and identity.find(":") == -1:
            ret = [self._find_one(npn, identity)]
        #
        # we need to be able to grab paths up to and starting from like this:
        #   $many.csvpaths.food:to
        #   $many.csvpaths.food:from
        #
        elif identity is not None:
            i = identity.find(":")
            directive = identity[i:]
            identity = identity[0:i]
            if directive == ":to":
                ret = self._get_to(npn, identity)
            elif directive == ":from":
                ret = self._get_from(npn, identity)
            else:
                self.csvpaths.logger.error(
                    "Incorrect reference directive: name: %s, paths-name: %, identity: %",
                    name,
                    npn,
                    identity,
                )
                raise InputException(
                    f"Reference directive must be :to or :from, not {directive}"
                )
        else:
            ...
        return ret

    def store_json_paths_file(self, name: str, jsonpath: str) -> None:
        """@private"""
        home = self.named_paths_home(name)
        j = ""
        with DataFileReader(jsonpath) as file:
            j = file.read()
        p = os.path.join(home, "definition.json")
        with DataFileWriter(path=p) as writer:
            writer.write(j)

    @property
    def named_paths_names(self) -> list[str]:
        """@private"""
        path = self.named_paths_dir
        names = []
        nos = self.nos
        nos.path = path
        lst = nos.listdir()
        for n in lst:
            nos.path = os.path.join(path, n)
            if not nos.isfile():
                names.append(n)
        return names

    def remove_named_paths(self, name: NamedPathsName, strict: bool = False) -> None:
        """@private"""
        if not self.has_named_paths(name) and strict is True:
            raise InputException(f"Named-paths name {name} not found")
        if not self.has_named_paths(name):
            return
        home = self.named_paths_home(name)
        nos = self.nos
        nos.path = home
        nos.remove()

    def remove_all_named_paths(self) -> None:
        """@private"""
        names = self.named_paths_names
        for name in names:
            self.remove_named_paths(name)

    def has_named_paths(self, name: NamedPathsName) -> bool:
        """@private"""
        path = os.path.join(self.named_paths_dir, name)
        nos = self.nos
        nos.path = path
        return nos.dir_exists()

    def number_of_named_paths(self, name: NamedPathsName) -> int:
        """@private"""
        return len(self._get_named_paths(name))

    def total_named_paths(self) -> bool:
        """@private"""
        return len(self.named_paths_names)  # pragma: no cover

    #
    # ================== internals =====================
    #

    def _get_named_paths(self, name: NamedPathsName) -> list[Csvpath]:
        if not self.has_named_paths(name):
            return None
        s = ""
        path = self.named_paths_home(name)
        grp = os.path.join(path, "group.csvpaths")
        nos = self.nos
        nos.path = grp
        if nos.exists():
            with DataFileReader(grp) as reader:
                s = reader.read()
        cs = s.split("---- CSVPATH ----")
        cs = [s for s in cs if s.strip() != ""]
        #
        # this update may not happen. it depends on if the group.csvpaths file has changed.
        # if someone put a new group.csvpaths file by hand we want to capture its fingerprint
        # for future reference. this shouldn't happen, but it probably will happen.
        #
        self.registrar.update_manifest_if(name=name, group_file_path=grp, paths=cs)
        return cs

    def _str_from_list(self, paths: list[Csvpath]) -> str:
        """@private"""
        f = ""
        for _ in paths:
            f = f"{f}\n\n---- CSVPATH ----\n\n{_}"
        return f

    def _copy_in(self, name, csvpathstr) -> None:
        temp = self._group_file_path(name)
        #
        # TODO: use a DataFileWriter that supports S3, local, etc. to write.
        #
        with DataFileWriter(path=temp, mode="w") as writer:
            writer.append(csvpathstr)
        return temp

    def _group_file_path(self, name: NamedPathsName) -> str:
        temp = os.path.join(self.named_paths_home(name), "group.csvpaths")
        return temp

    def _get_csvpaths_from_file(self, file_path: str) -> list[str]:
        #
        # TODO: use DataFileReader to support S3 and local
        #
        with DataFileReader(file_path) as reader:
            cp = reader.read()
            _ = [
                apath.strip()
                for apath in cp.split(PathsManager.MARKER)
                if apath.strip() != ""
            ]
            self.csvpaths.logger.debug("Found %s csvpaths in file", len(_))
            return _

    def _paths_name_path(self, pathsname) -> tuple[NamedPathsName, Identity]:
        specificpath = None
        i = pathsname.find("#")
        if i > 0:
            specificpath = pathsname[i + 1 :]
            pathsname = pathsname[0:i]
        return (pathsname, specificpath)

    def _get_to(self, npn: NamedPathsName, identity: Identity) -> list[Csvpath]:
        ps = []
        paths = self.get_identified_paths_in(npn)
        for path in paths:
            ps.append(path[1])
            if path[0] == identity:
                break
        return ps

    def _get_from(self, npn: NamedPathsName, identity: Identity) -> list[Csvpath]:
        ps = []
        paths = self.get_identified_paths_in(npn)
        for path in paths:
            if path[0] != identity and len(ps) == 0:
                continue
            ps.append(path[1])
        return ps

    def get_identified_paths_in(
        self, nps: NamedPathsName, paths: list[Csvpath] = None
    ) -> list[tuple[Identity, Csvpath]]:
        """@private"""
        # used by PathsRegistrar
        if paths is None:
            paths = self.get_named_paths(nps)
        idps = []
        for path in paths:
            #
            # we can get this from our self.csvpath, should we?
            #
            c = CsvPath()
            MetadataParser(c).extract_metadata(instance=c, csvpath=path)
            idps.append((c.identity, path))
        return idps

    def _find_one(self, npn: NamedPathsName, identity: Identity) -> Csvpath:
        if npn is not None:
            paths = self.get_identified_paths_in(npn)
            for path in paths:
                if path[0] == identity:
                    return path[1]
        raise InputException(
            f"Path identified as '{identity}' must be in the group identitied as '{npn}'"
        )

    def _name_from_name_part(self, name):
        i = name.rfind(".")
        if i == -1:
            pass
        else:
            name = name[0:i]
        return name
