import os
import json
import csv
from typing import NewType
from json import JSONDecodeError
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.references.reference_parser import ReferenceParser

# from csvpath.util.references.files_reference_finder import FilesReferenceFinder
from csvpath.util.references.files_reference_finder_2 import (
    FilesReferenceFinder2 as FilesReferenceFinder,
)

# from csvpath.util.references.results_reference_finder import ResultsReferenceFinder
from csvpath.util.references.results_reference_finder_2 import (
    ResultsReferenceFinder2 as ResultsReferenceFinder,
)
from csvpath.util.exceptions import InputException, FileException
from csvpath.util.nos import Nos
from csvpath.util.box import Box
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.template_util import TemplateUtility as temu
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
        box = Box()
        if self._nos is None:
            self._nos = box.get("boto_s3_nos")
            if self._nos is None:
                self._nos = Nos(None)
                box.add("boto_s3_nos", self._nos)
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

    #
    # namedfile: a NamedFileName (name or reference)
    # file: fully qualified path to match against the file key in the manifest.
    # only one of these two arguments may be passed.
    #
    # if we're referencing results the file UUID is the instance results UUID
    # because the data.csv doesn't have its own UUID. it does have a fingerprint
    # but we'll stick with the UUID since it shouldn't ever be confusing.
    #
    def get_named_file_uuid(self, *, name: NamedFileName, file=None) -> str:
        if name is None and file is None:
            raise ValueError("Named-file name and file cannot both be None")
        if name is None:
            raise ValueError("File can be None but named-file name must be passed")

        ref = ReferenceParser(name, csvpaths=self.csvpaths) if name.startswith("$") else None
        if ref is not None and file is None:
            if ref.datatype != ref.RESULTS:
                raise ValueError("Reference must be results, not {ref.datatype}")
            #
            # see examples/references/test_ref.py. there we handle references like:
            #    $sourcemode.results.202:last.source1
            #
            # looking at the manifest for a run, not the named-file manifest. the
            # run manifest is just a dict, not a list of dict.
            #
            # removing any names three and four because we want the run manifest
            # not an instance manifest. in results the name_three is always an
            # instance, not a narrower of the name_one.
            #
            ref.name_three = None
            ref.name_three_tokens = None
            ref.name_four_tokens = None
            refinder = ResultsReferenceFinder(self._csvpaths, ref=ref)
            lst = refinder.resolve()
            #
            # we should be more defensive, yes?
            #
            path = lst[0]
            path = os.path.join(path, "manifest.json")
            nos = self.nos
            nos.path = path
            if nos.exists():
                mani = self.registrar.get_manifest(path)
            uuid = mani["named_file_uuid"]
            return uuid
        elif ref is not None and file is not None:
            mani = self.get_manifest(name)
            if ref.datatype == ref.FILES:
                for _ in mani:
                    p = _["file"]
                    if p == file:
                        return _["uuid"]
            elif ref.datatype == ref.RESULTS:
                return mani["uuid"]
            else:
                raise ValueError("Invalid reference type in {name}")
        else:
            mani = self.get_manifest(name)
            if file is None:
                #
                # we assume that if we're not handling a reference and our file is None
                # we are looking for the most recent UUID.
                #
                return mani[len(mani) - 1]["uuid"]
            else:
                for _ in mani:
                    p = _["file"]
                    if p == file:
                        return _["uuid"]
        raise ValueError(f"No matching UUID found for file {file} in {name}")

    def get_manifest(self, name: NamedFileName) -> json:
        if name is None:
            raise ValueError("Paths name cannot be None")
        mani = None
        #
        # find a results manifest by results reference
        #
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            if ref.datatype == ref.RESULTS:
                refinder = ResultsReferenceFinder(self._csvpaths, reference=name)
                lst = refinder.resolve()
                #
                # what about if not found?
                #
                path = lst[0]
                path = os.path.join(path, "manifest.json")
                nos = self.nos
                nos.path = path
                if nos.exists():
                    mani = self.registrar.get_manifest(path)
                    #
                    # TODO: mani should never be a str. fixing. if this is found please delete.
                    #
                    if isinstance(mani, str):
                        mani = json.loads(mani)
                else:
                    ...
            elif ref.datatype == ref.FILES:
                #
                # find a file manifest by reference
                #
                rf = FilesReferenceFinder(self.csvpaths, reference=name)
                mani = rf.manifest
            else:
                raise ValueError("Unhandled type of reference: {name}")
        else:
            #
            # find a file manifest
            #
            path = self.named_file_home(name)
            path = os.path.join(path, "manifest.json")
            nos = self.nos
            nos.path = path
            if nos.exists():
                mani = self.registrar.get_manifest(path)
        if mani is None:
            raise ValueError(f"No manifest for file named {name}")
        if isinstance(mani, str):
            raise ValueError(f"Manifest is str: {mani}")
        return mani

    #
    # named-file homes are a dir like: inputs/named_files/March-2024/March-2024.csv
    #
    def named_file_home(self, name: NamedFileName) -> str:
        """@private"""
        if name is None or name.strip() == "":
            raise ValueError("Name cannot be None or empty")
        #
        # not a named-file name
        #
        if name.find("://") > -1:
            return name
        home = os.path.join(self.named_files_dir, name)
        nos = self.nos
        nos.path = home
        if nos.isfile():
            home = home[0 : home.rfind(nos.sep)]
        home = pathu.resep(home)
        return home

    def assure_named_file_home(self, name: NamedFileName) -> str:
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
    def assure_file_home(self, name: NamedFileName, path: str, template=None) -> str:
        """@private"""
        if name is None or name.strip() == "":
            raise ValueError("Name cannot be None or empty")
        if path.find("#") > -1:
            path = path[0 : path.find("#")]
        nos = self.nos
        nos.path = path
        #
        # nos sep is backend aware. it doesn't know what backend is handling
        # files, only what backend it is itself.
        #
        #sep = self.csvpaths.config.files_sep
        #
        # sadly we don't have an https backend at this time. so we have to test for the protocol.
        #
        sep = '/' if path.startswith("https://") or path.startswith("http://") else nos.sep
        f = path.rfind(sep)
        fname = path if f == -1 else path[f + 1 :]
        fname = self._clean_file_name(fname)
        if template is not None and template.strip() != "":
            fname = self._apply_template(path=path, name=fname, template=template)
        #
        # why is named file home giving a long name when no template?
        #
        home = self.named_file_home(name)
        home = os.path.join(home, fname)
        nos.path = home
        if not nos.exists():
            nos.makedirs()
        home = pathu.resep(home)
        return home

    def _apply_template(self, *, path: str, name: str, template: str) -> str:
        if template is None:
            return name
        if template.find(":filename") == -1:
            raise ValueError(f"Template {template} must include :filename")
        t = template
        #
        # uses the origin path + template to decorate the cleaned filename with
        # origin-path parts and static tokens to make a file path to a version of
        # a file. e.g.
        #   -> path: a/b/c/d/myfile.csv
        #   -> name: myfile.csv
        #   -> template: :3/:1/:filename
        #   -> result: d/b/myfile.csv
        # this will become:
        #   -> d/b/myfile.csv/myfile.csv
        # and then, once fingerprinted:
        #   -> d/b/myfile.csv/0b849c9c1ef....csv
        #
        parts = pathu.parts(path)
        for i, part in enumerate(parts):
            t = t.replace(f":{i}", part)
        t = t.replace(":filename", parts[-1])
        return t

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
        #
        # cannot be a reference or part of a reference. has to just
        # be the simple name of the named file.
        #
        try:
            self.legal_name(name)
        except Exception:
            return False
        #
        # the home should exist if the named file exists.
        #
        p = self.named_file_home(name)
        nos = self.nos
        nos.path = p
        b = nos.dir_exists()
        return b

    #
    # deprecated but stable in the short term. will be removed.
    #
    def name_exists(self, name: NamedFileName) -> bool:
        """@private"""
        return self.has_named_file(name)

    def remove_named_file(self, name: NamedFileName) -> bool:
        """@private"""
        #
        # cannot delete any specific files. this is for the named_file
        # as a whole. the named_file is immutable, so this is all-or-nothing
        # and we expect it to happen rarely in a production env.
        #
        self.legal_name(name)
        p = os.path.join(self.named_files_dir, name)
        nos = self.nos
        nos.path = p
        if nos.dir_exists():
            nos.remove()
            return True
        return False

    def remove_all_named_files(self) -> None:
        """@private"""
        names = self.named_file_names
        for name in names:
            self.remove_named_file(name)

    def set_named_files(self, nf: dict[str, str]) -> None:
        """@private"""
        cfg = {} if nf.get("_config") is None else nf.get("_config")
        for k, v in nf.items():
            if k == "_config":
                continue
            template = None
            if k in cfg and "template" in cfg[k]:
                template = cfg[k]["template"]
            self.add_named_file(name=k, path=v, template=template)

    def set_named_files_from_json(self, filename: str) -> None:
        """named-files from json uses json files to add any number of named files.
        the json files are always local, atm. the json structure is a dict. e.g:
             "orders": "c:\\data\\acme\\orders\\2025-01-30.csv",
             "orders": "c:\\data\\acme\\orders\\2025-01-31.csv",
             "_config":
                 "orders"
                     "template": ":1/:3/:filename"
        """
        try:
            with DataFileReader(filename) as reader:
                j = json.load(reader.source)
                self.set_named_files(j)
        except (OSError, ValueError, TypeError, JSONDecodeError) as ex:
            self.csvpaths.error_manager.handle_error(source=self, msg=f"{ex}")
            if self.csvpaths.ecoms.do_i_raise():
                raise

    def legal_name(self, name: str) -> None:
        if name is None:
            raise ValueError("Name cannot be None")
        if name.strip() == "":
            raise ValueError("Name cannot be empty")
        if name.find("/") > -1 or name.find("\\") > -1:
            raise ValueError(
                f"Not a legal name: {name}. Path seperators are not allowed."
            )
        if name.find(".") > -1:
            raise ValueError(f"Not a legal name: {name}. Periods are not allowed.")
        if name.find("$") > -1:
            raise ValueError(f"Not a legal name: {name}. Dollarsigns are not allowed.")
        if name.find("#") > -1:
            raise ValueError(f"Not a legal name: {name}. Hashmarks are not allowed.")

    #
    # if name is provided all files selected will be registered under the same name in
    # the order they are found; which is likely not deterministic. template, if any, is
    # the way we're going to use the source path to create a consistent path within the
    # files area. recurse is going to typically be True because we want to add all the
    # files we find below the indicated root directory.
    #
    # if we don't pass in a name, each file is registered under its filename, minus the
    # extension
    #
    def add_named_files_from_dir(
        self, dirname: str, *, name=None, template: str = None, recurse=True
    ):
        #
        # legal_name handled at add_named_file
        #
        # self.legal_name(name)
        # if dirname is None or dirname.strip() == "":
        #    raise ValueError("Dirname cannot be None or empty")
        #
        # need to support adding all files from directory under the same name. preferably
        # in order of file created time, if possible.
        #
        nos = self.nos
        nos.path = dirname
        dlist = nos.listdir(files_only=True, recurse=recurse)
        base = dirname
        #
        # collect all full paths that are files and have correct extensions
        #
        for p in dlist:
            _ = p.lower()
            ext = p[p.rfind(".") + 1 :].strip().lower()
            if ext in self._csvpaths.config.csv_file_extensions:
                if name is None:
                    n = p if p.rfind(".") == -1 else p[0 : p.rfind(".")]
                else:
                    n = name
                if n.find(nos.sep) > -1:
                    n = n[n.rfind(nos.sep) + 1 :]
                #
                # we expect when Nos gives us a recursive listing the files are qualified
                # by every dir up to the starting dir.
                #
                if recurse is True:
                    path = p
                else:
                    path = os.path.join(base, p)

                self.add_named_file(name=n, path=path, template=template)
            else:
                self._csvpaths.logger.debug(
                    "%s is not in accept list", os.path.join(base, p)
                )

    def add_named_file(
        self, *, name: NamedFileName, path: str, template: str = None
    ) -> None:
        self.legal_name(name)
        # if name is None or name.strip() == "":
        #    raise ValueError("Name cannot be None or empty")
        if path is None or path.strip() == "":
            raise ValueError("Path cannot be None or empty")
        if template is not None:
            temu.valid(template, file=True)
        path = pathu.resep(path)
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
        #
        home = self.assure_file_home(name, path, template)
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
        self._copy_in(path, home, template)
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
        mdata.template = template
        #
        # TODO: add file_size. move FileInfo into Nos. for now it is 0.
        #
        self.registrar.register_complete(mdata)

    def _clean_file_name(self, fname: str) -> str:
        fname = fname.replace("?", "_")
        fname = fname.replace("&", "_")
        fname = fname.replace("=", "_")
        return fname

    def _copy_in(self, path, home, template=None) -> None:
        nos = self.nos
        nos.path = path
        sep = nos.sep
        sep = '/' if path.startswith("https://") or path.startswith("http://") else sep
        fname = path if path.rfind(sep) == -1 else path[path.rfind(sep) + 1 :]
        #
        # creates
        #   a/file.csv -> named_files/name/file.csv/file.csv
        # the dir name matching the resulting file name is correct
        # once the file is landed and fingerprinted, the file
        # name is changed.
        #
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
    def get_named_file(self, name: NamedFileName) -> str | list:
        if name is None or name.strip() == "":
            raise ValueError("Name cannot be None or empty")
        ret = None
        #
        # references can be to results or to prior versions of a file.
        #
        # at the moment, files and results references are similar but not as much the same
        # as they could be. regardless, there would be differences because of the different
        # data structures they deal with.
        #
        # results references look like:
        #      $myname.results.2025-03-:first.myinstance
        #
        # the pointer in name_one (the name of the run_dir) can be :first, :last, :index. ffr,
        # we can easily swap :today and :yesterday in if needed. see comment in ResultsRefFinder
        #
        # prior file version references we can do:
        #      $myfilename.files.:index
        #           $orders.files.all:2
        #
        #      $myfilename.files.[yesterday|today][:last|:first|:index|:all|None]
        #           $orders.files.yesterday:last
        #
        #      $myfilename.files.fingerprint
        #           $orders.files.a7b0c5d761d74581c8b69481d355b59e6b891e2a1c6bbc3976c52e7a91cd5c28
        #
        #      $myfilename.files.[yyyy-mm-dd_hh-mm-ss][:before|:after|None]
        #           $orders.files.:1
        #
        #      $myfilename.files.filename.[yyyy-mm-dd_hh-mm-ss][:all|:first|:last|:before|:after|None]
        #           $orders.files.march-orders_csv
        #           $orders.files.march-orders_csv:2025-03
        #
        # order:
        #   fingerprint exact match
        #   filename prefix match
        #   index match
        #   yesterday|today
        #   date prefix match
        #
        #   with file templates like ":5/:4/:filename" we can do directory references like:
        #       $orders.files.2025/mar:all
        #
        #
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            if ref.datatype == ref.FILES:
                reff = FilesReferenceFinder(self._csvpaths, reference=name)
                lst = reff.resolve()
                #
                # more defensive? what if multiple?
                #
                if len(lst) > 0:
                    ret = lst[0]
            elif ref.datatype == ref.RESULTS:
                reff = ResultsReferenceFinder(self._csvpaths, reference=name)
                lst = reff.resolve()
                if len(lst) > 0:
                    ret = lst[0]
                    ret = os.path.join(ret, "data.csv")
        else:
            if not self.has_named_file(name):
                return None
            n = self.named_file_home(name)
            ret = self.registrar.registered_file(n)
        return ret

    def get_fingerprint_for_name(self, name: NamedFileName) -> str:
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
    def get_named_file_reader(self, name: NamedFileName) -> DataFileReader:
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
