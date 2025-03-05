import os
import json
import csv
from typing import NewType
from json import JSONDecodeError
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.reference_parser import ReferenceParser
from csvpath.util.reference_finder import ReferenceFinder
from csvpath.util.exceptions import InputException, FileException
from csvpath.util.nos import Nos
from csvpath.util.box import Box
from csvpath.util.path_util import PathUtility as pathu
from .file_registrar import FileRegistrar
from .lines_and_headers_cacher import LinesAndHeadersCacher
from .file_metadata import FileMetadata

NamedFileName = NewType("NamedFileName", str)
"""@private"""


class FileManager:
    def __init__(self, *, csvpaths=None):
        """@private"""
        self._csvpaths = csvpaths
        self.registrar = FileRegistrar(csvpaths)
        """@private"""
        #
        # used by csvpath direct access
        #
        self.lines_and_headers_cacher = LinesAndHeadersCacher(csvpaths)
        """@private"""
        self._nos = None

    @property
    def nos(self) -> Nos:
        if self._nos is None:
            self._nos = Box.STUFF.get("boto_s3_nos")
            if self._nos is None:
                self._nos = Nos(None)
                Box().add("boto_s3_nos", self._nos)
        return self._nos

    @property
    def csvpaths(self):
        """@private"""
        return self._csvpaths

    #
    # named file dir is like: inputs/named_files
    #
    @property
    def named_files_dir(self) -> str:
        """@private"""
        return self._csvpaths.config.inputs_files_path

    #
    # the root manifest file tracking all name-file stagings. note that
    # this is created by an optional listener. it is possible to run without
    # creating the root manifest or capturing the data with another listener.
    #
    @property
    def files_root_manifest(self) -> dict:
        """@private"""
        p = self.files_root_manifest_path
        nos = self.nos
        nos.path = p
        if nos.exists():
            with DataFileReader(p) as reader:
                return json.load(reader.source)
        return None

    @property
    def files_root_manifest_path(self) -> dict:
        """@private"""
        return os.path.join(self.named_files_dir, "manifest.json")

    def get_named_file_uuid(self, name: NamedFileName) -> str:
        if name is None:
            raise ValueError("Paths name cannot be None")
        if name.startswith("$"):
            path = self.csvpaths.results_manager.get_run_dir_for_reference(name)
            path = os.path.join(path, "manifest.json")
            nos = self.nos
            nos.path = path
            if nos.exists():
                m = self.registrar.get_manifest(path)
                return m["uuid"]
        else:
            path = self.named_file_home(name)
            path = os.path.join(path, "manifest.json")
            nos = self.nos
            nos.path = path
            if nos.exists():
                m = self.registrar.get_manifest(path)
                return m[len(m) - 1]["uuid"]
        raise ValueError(f"No manifest for file named {name}")

    #
    # named-file homes are a dir like: inputs/named_files/March-2024/March-2024.csv
    #
    def named_file_home(self, name: NamedFileName) -> str:
        """@private"""
        #
        # not a named-file name
        #
        if name.find("://") > -1:
            return name
        if name.find("/") > -1:
            #
            # this is definitely not what we should be returning. but it is what
            # works in the new world of remote and fully-qualified local paths.
            # for now, going with it. the previous implementation was wonky too,
            # in a different and not visible way, but not good, so this is a step
            # up in multiple ways.
            #
            return ""
        home = os.path.join(self.named_files_dir, name)
        nos = self.nos
        nos.path = home
        if nos.isfile():
            home = home[0 : home.rfind(nos.sep)]
        home = pathu.resep(home)
        return home

    def assure_named_file_home(self, name: str) -> str:
        """@private"""
        home = self.named_file_home(name)
        nos = self.nos
        nos.path = home
        if not nos.exists():
            nos.makedirs()
        home = pathu.resep(home)
        return home

    #
    # file homes are paths to files like:
    #   inputs/named_files/March-2024/March-2024.csv/March-2024.csv
    # which become paths to fingerprint-named file versions like:
    #   inputs/named_files/March-2024/March-2024.csv/12467d811d1589ede586e3a42c41046641bedc1c73941f4c21e2fd2966f188b4.csv
    # once the files have been fingerprinted
    #
    # remember that blob stores do not handle directories in the same way.
    # this method won't create a directory in a blob store because that's not
    # possible.
    #
    def assure_file_home(self, name: str, path: str) -> str:
        """@private"""
        if path.find("#") > -1:
            path = path[0 : path.find("#")]
        nos = self.nos
        nos.path = path
        sep = nos.sep
        fname = path if path.rfind(sep) == -1 else path[path.rfind(sep) + 1 :]
        fname = self._clean_file_name(fname)
        home = self.named_file_home(name)
        home = os.path.join(home, fname)
        nos.path = home
        if not nos.exists():
            nos.makedirs()
        home = pathu.resep(home)
        return home

    @property
    def named_files_count(self) -> int:
        """@private"""
        return len(self.named_file_names)

    @property
    def named_file_names(self) -> list:
        """@private"""
        nos = self.nos
        b = self.named_files_dir
        ns = []
        nos.path = b
        lst = nos.listdir()
        for n in lst:
            nos.path = os.path.join(b, n)
            if not nos.isfile():
                ns.append(n)
        return ns

    #
    # this feels like the better sig.
    #
    def has_named_file(self, name: NamedFileName) -> bool:
        return self.name_exists(name)

    #
    # deprecated but stable
    #
    def name_exists(self, name: NamedFileName) -> bool:
        """@private"""
        p = self.named_file_home(name)
        nos = self.nos
        nos.path = p
        b = nos.dir_exists()
        return b

    def remove_named_file(self, name: str) -> None:
        """@private"""
        p = os.path.join(self.named_files_dir, name)
        nos = self.nos
        nos.path = p
        nos.remove()

    def remove_all_named_files(self) -> None:
        """@private"""
        names = self.named_file_names
        for name in names:
            self.remove_named_file(name)

    def set_named_files(self, nf: dict[str, str]) -> None:
        """@private"""
        for k, v in nf.items():
            self.add_named_file(name=k, path=v)

    def set_named_files_from_json(self, filename: str) -> None:
        """named-files from json files are always local"""
        try:
            #
            # TODO: named-files json files are always local. they should
            # be able to be on s3 so that we are completely independent of
            # the local disk w/re file manager
            #
            with open(filename, "r", encoding="utf-8") as f:
                j = json.load(f)
                self.set_named_files(j)
        except (OSError, ValueError, TypeError, JSONDecodeError) as ex:
            self.csvpaths.error_manager.handle_error(source=self, msg=f"{ex}")
            if self.csvpaths.ecoms.do_i_raise():
                raise

    def add_named_files_from_dir(self, dirname: str):
        nos = self.nos
        nos.path = dirname
        dlist = nos.listdir()
        base = dirname
        for p in dlist:
            _ = p.lower()
            ext = p[p.rfind(".") + 1 :].strip().lower()
            if ext in self._csvpaths.config.csv_file_extensions:
                name = p if p.rfind(".") == -1 else p[0 : p.rfind(".")]
                path = os.path.join(base, p)
                self.add_named_file(name=name, path=path)
            else:
                self._csvpaths.logger.debug(
                    "%s is not in accept list", os.path.join(base, p)
                )

    #
    # -------------------------------------
    #
    def add_named_file(self, *, name: str, path: str) -> None:
        #
        # path must end up with only legal filesystem chars.
        # the read-only http backend will have ? and possibly other
        # chars that are not legal in some contexts. we have to
        # convert those, but obviously only after obtaining the
        # bytes.
        #
        #
        # create folder tree in inputs/named_files/name/filename
        #
        home = self.assure_file_home(name, path)
        file_home = home
        mark = None
        #
        # find mark if there. mark indicates a sheet. it is found
        # as the trailing word after a # at the end of the path e.g.
        # my-xlsx.xlsx#sheet2
        #
        hm = home.find("#")
        if hm > -1:
            mark = home[hm + 1 :]
            home = home[0:hm]
        pm = path.find("#")
        if pm > -1:
            mark = path[pm + 1 :]
            path = path[0:pm]
        #
        # copy file to its home location
        #
        self._copy_in(path, home)
        name_home = self.named_file_home(name)
        rpath, h = self._fingerprint(home)
        mdata = FileMetadata(self.csvpaths.config)
        mdata.named_file_name = name
        #
        # we need the declared path, incl. any extra path info, in order
        # to know if we are being pointed at a sub-portion of the data, e.g.
        # an excel worksheet.
        #
        path = f"{path}#{mark}" if mark else path
        mdata.origin_path = path
        mdata.archive_name = self._csvpaths.config.archive_name
        mdata.fingerprint = h
        mdata.file_path = rpath
        mdata.file_home = file_home
        nos = self.nos
        nos.path = file_home
        mdata.file_name = file_home[file_home.rfind(nos.sep) + 1 :]
        mdata.name_home = name_home
        mdata.mark = mark
        self.registrar.register_complete(mdata)

    def _clean_file_name(self, fname: str) -> str:
        fname = fname.replace("?", "_")
        fname = fname.replace("&", "_")
        fname = fname.replace("=", "_")
        return fname

    def _copy_in(self, path, home) -> None:
        """@private"""
        nos = self.nos
        nos.path = path
        sep = nos.sep
        fname = path if path.rfind(sep) == -1 else path[path.rfind(sep) + 1 :]
        # creates
        #   a/file.csv -> named_files/name/file.csv/file.csv
        # the dir name matching the resulting file name is correct
        # once the file is landed and fingerprinted, the file
        # name is changed.
        fname = self._clean_file_name(fname)
        temp = os.path.join(home, fname)
        if pathu.parts(path)[0] == pathu.parts(home)[0]:
            nos.path = path
            nos.copy(temp)
        else:
            self._copy_down(path, temp, mode="wb")
        return temp

    def _copy_down(self, path, temp, mode="wb") -> None:
        """@private"""
        with DataFileReader(path) as reader:
            with DataFileWriter(path=temp, mode=mode) as writer:
                for line in reader.next_raw():
                    writer.append(line)

    #
    # can take a reference. the ref would only be expected to point
    # to the results of a csvpath in a named-paths group. it would be
    # in this form: $group.results.2024-01-01_10-15-20.mypath
    # where this gets interesting is the datestamp identifing the
    # run. we need to allow for var sub and/or other shortcuts
    #
    def get_named_file(self, name: str) -> str:
        ret = None
        #
        # references can be to results or to prior versions of a file. in
        # prior file version references we can do:
        #      $myfilename.files.index
        #      $myfilename.files.[yesterday|today]:[last|first|index]
        #      $myfilename.files.fingerprint
        #      $myfilename.files.[yyyy-mm-dd_hh-mm-ss]:[before|after|None]
        #
        if name.startswith("$"):
            reff = ReferenceFinder(self._csvpaths, name)
            ret = reff.resolve()
        else:
            if not self.name_exists(name):
                return None
            n = self.named_file_home(name)
            ret = self.registrar.registered_file(n)
        return ret

    def get_fingerprint_for_name(self, name) -> str:
        """@private"""
        if name.startswith("$"):
            # atm, we don't give fingerprints for references doing rewind/replay
            return ""
        #
        # note: this is not creating fingerprints, just getting existing ones.
        #
        return self.registrar.get_fingerprint(self.named_file_home(name))

    #
    # -------------------------------------
    #
    def get_named_file_reader(self, name: str) -> DataFileReader:
        """@private"""
        path = self.get_named_file(name)
        t = self.registrar.type_of_file(self.named_file_home(name))
        return FileManager.get_reader(path, filetype=t)

    @classmethod
    def get_reader(
        cls, path: str, *, filetype: str = None, delimiter=None, quotechar=None
    ) -> DataFileReader:
        """@private"""
        return DataFileReader(
            path, filetype=filetype, delimiter=delimiter, quotechar=quotechar
        )

    def _fingerprint(self, path) -> str:
        """@private"""
        nos = self.nos
        nos.path = path
        sep = nos.sep
        fname = path if path.rfind(sep) == -1 else path[path.rfind(sep) + 1 :]
        t = None
        i = fname.find(".")
        if i > -1:
            t = fname[i + 1 :]
        else:
            t = fname
        i = t.find("#")
        if i > -1:
            t = t[0:i]
        #
        # creating the initial file name, where the file starts
        #
        fpath = os.path.join(path, fname)
        h = None
        #
        # this version should work local and minimize traffic when in S3
        #
        hpath = None
        remove_fpath = False
        with DataFileReader(fpath) as f:
            h = f.fingerprint()
            #
            # creating the new path using the fingerprint as filename
            #
            hpath = os.path.join(path, h)
            if t is not None:
                hpath = f"{hpath}.{t}"
            #
            # if we're re-adding the file we don't need to make
            # another copy of it. re-adds are fine.
            #
            # need an s3 way to do this
            nos.path = hpath
            remove_fpath = nos.exists()
            #
            # if a first add, rename the file to the fingerprint + ext
            #
        if remove_fpath:
            nos.path = fpath
            nos.remove()
            return hpath, h
        if hpath:
            nos.path = fpath
            nos.rename(hpath)
        return hpath, h
