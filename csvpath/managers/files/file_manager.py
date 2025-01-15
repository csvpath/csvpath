import os
import json
import csv
from json import JSONDecodeError
from csvpath.util.error import ErrorHandler
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.reference_parser import ReferenceParser
from csvpath.util.exceptions import InputException, FileException
from csvpath.util.nos import Nos
from .file_registrar import FileRegistrar
from .file_cacher import FileCacher
from .file_metadata import FileMetadata


class FileManager:
    def __init__(self, *, named_files: dict[str, str] = None, csvpaths=None):
        if named_files is None:
            named_files = {}
        self._csvpaths = csvpaths
        self.registrar = FileRegistrar(csvpaths)
        self.cacher = FileCacher(csvpaths)

    @property
    def csvpaths(self):
        return self._csvpaths

    #
    # named file dir is like: inputs/named_files
    #
    @property
    def named_files_dir(self) -> str:
        return self._csvpaths.config.inputs_files_path

    #
    # named-file homes are a dir like: inputs/named_files/March-2024/March-2024.csv
    #
    def named_file_home(self, name: str) -> str:
        #
        # not a named-file name
        #
        if name.find("/") > -1:
            #
            # this is definitely not what we should be returning. but it is what
            # works in the new world of remote and fully-qualified local paths.
            # for now, going with it. the previous implementation was wonky too,
            # in a different and not visible way, but not good, so this is a step
            # up in multiple ways.
            #
            return ""
        #
        # added
        #
        home = None
        if name.startswith("/"):
            home = name
        else:
            #
            # done add
            #
            home = os.path.join(self.named_files_dir, name)
        #
        # added
        #
        if Nos(home).isfile():
            home = home[0 : home.rfind(Nos(home).sep)]
        #
        # done add
        #
        return home

    def assure_named_file_home(self, name: str) -> str:
        home = self.named_file_home(name)
        if not os.path.exists(home):
            Nos(home).makedirs()
        return home

    #
    # file homes are paths to files like:
    #   inputs/named_files/March-2024/March-2024.csv/March-2024.csv
    # which become paths to fingerprint-named file versions like:
    #   inputs/named_files/March-2024/March-2024.csv/12467d811d1589ede586e3a42c41046641bedc1c73941f4c21e2fd2966f188b4.csv
    # once the files have been fingerprinted
    #
    def assure_file_home(self, name: str, path: str) -> str:
        if path.find("#") > -1:
            path = path[0 : path.find("#")]
        sep = Nos(path).sep
        fname = path if path.rfind(sep) == -1 else path[path.rfind(sep) + 1 :]
        home = self.named_file_home(name)
        home = os.path.join(home, fname)
        if not Nos(home).exists():
            Nos(home).makedirs()
        return home

    @property
    def named_files_count(self) -> int:
        return len(self.named_file_names)

    @property
    def named_file_names(self) -> list:
        b = self.named_files_dir
        ns = [n for n in Nos(b).listdir() if not Nos(os.path.join(b, n)).isfile()]
        return ns

    def name_exists(self, name: str) -> bool:
        p = self.named_file_home(name)
        b = Nos(p).dir_exists()
        return b

    def remove_named_file(self, name: str) -> None:
        p = os.path.join(self.named_files_dir, name)
        Nos(p).remove()

    def remove_all_named_files(self) -> None:
        names = self.named_file_names
        for name in names:
            self.remove_named_file(name)

    def set_named_files(self, nf: dict[str, str]) -> None:
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
            ErrorHandler(csvpaths=self._csvpaths).handle_error(ex)

    def add_named_files_from_dir(self, dirname: str):
        dlist = Nos(dirname).listdir()
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
        mdata.file_name = file_home[file_home.rfind(Nos(file_home).sep) + 1 :]
        mdata.name_home = name_home
        mdata.mark = mark
        self.registrar.register_complete(mdata)

    def _copy_in(self, path, home) -> None:
        sep = Nos(path).sep
        fname = path if path.rfind(sep) == -1 else path[path.rfind(sep) + 1 :]
        # creates
        #   a/file.csv -> named_files/name/file.csv/file.csv
        # the dir name matching the resulting file name is correct
        # once the file is landed and fingerprinted, the file
        # name is changed.
        temp = os.path.join(home, fname)
        #
        # this is another place that is too s3 vs. local. we'll have
        # other source/sinks to support.
        #
        if path.startswith("s3:") and not home.startswith("s3"):
            self._copy_down(path, temp, mode="wb")
        elif path.startswith("s3:") and home.startswith("s3"):
            Nos(path).copy(temp)
        elif not path.startswith("s3:") and not home.startswith("s3"):
            self._copy_down(path, temp, mode="wb")
        elif not path.startswith("s3:") and home.startswith("s3"):
            self._copy_down(path, temp, mode="wb")
        else:
            ...  # not possible. just being explicit for the moment.
        return temp

    def _copy_down(self, path, temp, mode="wb") -> None:
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
        if name.startswith("$"):
            ref = ReferenceParser(name)
            if ref.datatype != ReferenceParser.RESULTS:
                raise InputException(
                    f"Reference datatype must be {ReferenceParser.RESULTS}"
                )
            reman = self._csvpaths.results_manager
            ret = reman.data_file_for_reference(name)
        else:
            if not self.name_exists(name):
                return None
            n = self.named_file_home(name)
            ret = self.registrar.registered_file(n)
        return ret

    def get_fingerprint_for_name(self, name) -> str:
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
        path = self.get_named_file(name)
        t = self.registrar.type_of_file(self.named_file_home(name))
        return FileManager.get_reader(path, filetype=t)

    @classmethod
    def get_reader(
        cls, path: str, *, filetype: str = None, delimiter=None, quotechar=None
    ) -> DataFileReader:
        return DataFileReader(
            path, filetype=filetype, delimiter=delimiter, quotechar=quotechar
        )

    def _fingerprint(self, path) -> str:
        sep = Nos(path).sep
        fname = path if path.rfind(sep) == -1 else path[path.rfind(sep) + 1 :]
        t = None
        i = fname.find(".")
        if i > -1:
            t = fname[i + 1 :]
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
            b = Nos(hpath).exists()
            if b:
                Nos(fpath).remove()
                return hpath, h
            #
            # if a first add, rename the file to the fingerprint + ext
            #
            Nos(fpath).rename(hpath)
        return hpath, h
