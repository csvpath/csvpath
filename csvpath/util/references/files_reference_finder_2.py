import os
from datetime import datetime, timezone, timedelta
from .reference_parser import ReferenceParser
from .reference_results import ReferenceResults
from .files_tools.fingerprint_finder import FingerprintFinder
from csvpath.matching.util.expression_utility import ExpressionUtility as exut
from csvpath.util.references.tools.date_completer import DateCompleter


class FilesReferenceFinder2:
    def __init__(
        self, csvpaths, *, ref: ReferenceParser = None, reference: str = None
    ) -> None:
        if ref is None and reference is None:
            raise ValueError("Must provide either ref or reference")
        self._csvpaths = csvpaths
        self.reference = reference
        self._ref = None
        if self.reference is not None:
            if ref is not None:
                raise ValueError("Cannot provide both ref and name")
            self._ref = ReferenceParser(reference, csvpaths=self.csvpaths)
        if self._ref is None:
            self._ref = ref
        if reference is None:
            self.reference = ref.ref_string
        #
        # we need to know the os path segment separator to use. if
        # we're working on a config.ini that points to a cloud service
        # for [inputs]files then we're always '/'.
        #
        self.sep = csvpaths.config.get(section="inputs", name="files").find("://") > -1
        self.sep = "/" if self.sep is True else os.sep
        #self.sep = "/" if self.sep is True or os.sep == "/" else "\\"

    @property
    def ref(self) -> ReferenceParser:
        return self._ref

    @property
    def csvpaths(self):
        return self._csvpaths

    @property
    def manifest(self) -> list:
        results = ReferenceResults(ref=self.ref, csvpaths=self.csvpaths)
        mani = results.manifest
        return mani

    def resolve(self) -> list:
        lst = self.query().files
        return lst

    def query(self) -> ReferenceResults:
        print(f"starting to find files: {self.csvpaths.config.get(section='inputs', name='files')}")
        results = ReferenceResults(ref=self.ref, csvpaths=self.csvpaths)
        #
        # if we find fingerprint we are done
        #
        FingerprintFinder.update(results)
        if len(results) > 0:
            return results
        # print(f"51: results: {len(results)}")
        #
        # other name_one stuff.
        # we'll work off a shared copy of the name_one tokens
        #
        tokens = self.ref.name_one_tokens[:]
        print(f"57: results: {len(results)}")
        #
        # if range exists it impacts everything except an ordinal.
        # otherwise, path or date may exist and if either does, it
        # disallows the other.
        #
        if not self._range_if_name_one(results=results, tokens=tokens):
            print(f"65: results: {len(results)}")
            if not self._date_if_name_one(results=results, tokens=tokens):
                print(f"66: results: {len(results)}")
                self._path_if_name_one(results=results, tokens=tokens)
        print(f"69: results: {len(results)}")
        #
        # ordinals simply pickout an item in results.files, if possible
        #
        self._ordinal_if_name_one(results=results, tokens=tokens)
        print(f"73: results: {len(results)}")
        #
        # name_two stuff
        #
        tokens = self.ref.name_three_tokens[:]
        # print(f"78: results: {len(results)}")
        #
        # this is no longer true with added ordinals
        # if len(tokens) > 1:
        #    raise ValueError("Only one token expected")
        #
        # only one branch hits an ordinal in name_three and if it does
        # nothing else happens. so we can do this first.
        #
        if not self._ordinal_if_name_three(results=results, tokens=tokens):
            # print(f"86:: results: {len(results)}, tokens: {tokens}")
            if self._range_if_name_three(results=results, tokens=tokens):
                # print(f"87:: results: {len(results)}, tokens: {tokens}")
                # 1. test me!!!
                self._ordinal_if_name_three(results=results, tokens=tokens)
            # if not an ordinal and not a date+range we may be a date+ordinal
            # 2. test me!!!
            elif self._arrival_ordinal_if_name_three(results=results, tokens=tokens):
                # 3. which includes me!!!
                self._ordinal_if_name_three(results=results, tokens=tokens)
        # print(f"88: results: {len(results)}, tokens: {tokens}")
        #
        # done
        #
        return results

    # ==============================================

    def _range_if_name_one(self, *, results, tokens) -> bool:
        rrange = self._get_range_from_tokens(results, tokens)
        if rrange is None:
            return False
        print(f"_range_if_name_one: results: {results}, tokens: {tokens}")
        #
        # a 3-parts range where the range tells the date which way to look:
        #   path >> date >> range
        #
        thedate = None
        if len(tokens) > 0:
            thedate = DateCompleter.to_date(tokens[0])
        if thedate is not None:
            if rrange in ["yesterday", "today"]:
                raise ValueError("Cannot have both a date and also yesterday or today")
            return self._range_of_date_limited_paths(
                results=results, rrange=range, thedate=thedate
            )
        #
        # a timeboxed range:
        #   path >> within day
        #   date >> within day
        #
        elif rrange in ["yesterday", "today"]:
            return self._name_one_within_time_box(
                results=results, rrange=rrange, thedate=thedate
            )
        #
        # a regular range. one of:
        #   path >> range
        #   date >> range
        #
        else:
            # not done
            return self._range_of_name_one(results=results, rrange=rrange)

    def _name_one_within_time_box(
        self, *, results, rrange: str, thedate: datetime
    ) -> None:
        mani = self.manifest
        return self._do_name_one_within_time_box(
            results=results, rrange=rrange, thedate=thedate, mani=mani
        )

    def _do_name_one_within_time_box(
        self, *, results, rrange: str, thedate: datetime, mani: list
    ) -> None:
        #
        #
        if len(results.ref.name_one_tokens) == 0:
            return False
        prefix = self._prefix(results)
        px = len(prefix)
        #
        #
        #
        ds = self._range_as_timestring(rrange)
        ffrom, tto = DateCompleter.get_bracket_dates(ds, unit="day")
        #
        #
        #
        keep = []
        nameone = results.ref.name_one
        if nameone is None:
            nameone = ""
        for i, _ in enumerate(mani):
            path = _["file"]
            pp = path[px + 1 :]
            if self._starts_with(pp, nameone):
                dat = exut.to_datetime(_["time"])
                if ffrom < dat < tto:
                    keep.append(path)
        results.files = keep
        return True

    def _path_minus_prolog(
        self, *, path: str, results=None, named_file_name: str = None
    ) -> str:
        root_major = results.ref.root_major if results is not None else named_file_name
        if root_major is None:
            root_major = self.ref.root_major
        p = root_major
        sepped = f"{p}{self.sep}"
        # sepped = f"{p}/"
        i = path.find(sepped)
        #
        # we expect either p/ or /p/ in path
        #
        if i != 0 and path[i - 1] != self.sep:
            # if i != 0 and path[i - 1] != "/":
            #
            # one fallback in case we found the same name in inputs and name_one
            #
            i = path.find(sepped, i + 1)
        if i > -1:
            path = path[i + len(p) :]
            path = path.lstrip(self.sep)
            # path = path.lstrip("/")
        return path

    def _range_of_name_one(self, *, results, rrange: str) -> None:
        mani = self.manifest
        return self._do_range_of_name_one(results=results, rrange=rrange, mani=mani)

    def _do_range_of_name_one(self, *, results, rrange: str, mani: list) -> None:
        #
        # gets the range of files that are after a point.
        # the point is a date or the first match of a path prefix.
        #
        print(f"_do_range_of_name_one: results: {results}, rrange: {rrange}, results.ref.name_one: {results.ref.name_one}")
        for _ in mani:
            print(f"   ...{_['file']}")
        
        
        date = DateCompleter.to_date(results.ref.name_one)
        px = -1
        if date is None:
            prefix, px = self._prefix(results)  # os.path.join(inputs, named_file)
            print(f"_do_range_of_name_one: prefix: {prefix}, px: {px}")
        before = rrange in ["before", "to"]
        after = rrange in ["after", "from"]
        nameone = results.ref.name_one
        if nameone is None:
            nameone = ""
        keeping = (
            False  # if a path, when that path is first matched we switch the keeping on
        )
        keep = []
        for i, _ in enumerate(mani):
            if date is None:
                path = _["file"]
                print(f"_do_range_of_name_one: path: {path}, nameone: {nameone}")
                # minus = self._path_minus_prolog(named_file_name=self.ref.root_major, path=path)
                sw = self._starts_with(path, nameone)
                if rrange == "all":
                    if sw:
                        keep.append(path)
                    continue
                elif keeping and before and sw:
                    if rrange == "to":
                        keep.append(path)
                    break
                elif keeping and before and not sw:
                    ...
                elif keeping and after and sw:
                    ...  # never toggles off
                elif not keeping and before and not sw:
                    keeping = True
                elif not keeping and before and sw:
                    if rrange == "to":
                        keep.append(path)
                    break
                elif not keeping and after and sw:
                    keeping = True
                    if rrange == "from":
                        keep.append(path)
                    continue
                elif not keeping and after and not sw:
                    continue
                keep.append(path)
            else:
                dat = exut.to_datetime(_["time"])
                if after:
                    if dat >= date:
                        keep.append(_["file"])
                    else:
                        ...
                elif before:
                    if dat <= date:
                        keep.append(_["file"])
                    else:
                        ...
                else:  # all?
                    keep.append(_["file"])
        results.files = keep
        return True

    def _range_of_date_limited_paths(
        self, *, results, rrange: str, thedate: datetime
    ) -> None:
        mani = self.manifest
        return self._do_range_of_date_limited_paths(
            results=results, rrange=rrange, thedate=thedate, mani=mani
        )

    def _do_range_of_date_limited_paths(
        self, *, results, rrange: str, thedate: datetime, mani: list
    ) -> None:
        #
        # in this case we:
        #   1. get all the files matching the path
        #   2. get the date
        #   3. slice the files at the date according to the range
        #   4. put the _["file"] into the result
        #
        prefix, px = self._prefix(results)
        lt = rrange in ["before", "to"]
        keep = []
        nameone = results.ref.name_one
        if nameone is None:
            nameone = ""
        for _ in mani:
            path = _["file"]
            minus = self._path_minus_prolog(
                named_file_name=self.ref.root_major, path=path
            )
            if self._starts_with(minus, nameone):
                dat = exut.to_datetime(_["time"])
                if lt and dat < thedate:
                    keep.append(path)
                elif not lt and dat > thedate:
                    keep.append(path)
        results.files = keep
        return True

    # ==============================================
    # ==============================================

    def _date_if_name_one(self, *, results, tokens) -> bool:
        mani = self.manifest
        return self._do_date_if_name_one(results=results, tokens=tokens, mani=mani)

    def _do_date_if_name_one(self, *, results, tokens: list, mani: list) -> bool:
        #
        # no range involved
        #
        # a date in name_one with no range token is its own range.
        # the date string gives the smallest bracketing unit. e.g.
        # 2025-04- means the range is bracketed as first moment in
        # April 2025 to last moment in April 2025.
        #
        name = results.ref.name_one
        datestr = DateCompleter.complete_if(name)
        if datestr is None:
            return False
        ffrom, tto = DateCompleter.get_bracket_dates(name)
        #
        # otherwise, items within nearest unit
        #
        keep = []
        for _ in mani:
            d = exut.to_datetime(_["time"])
            d = d.astimezone(timezone.utc)
            if ffrom < d < tto:
                keep.append(_["file"])
        results.files = keep
        return True

    def _path_if_name_one(self, *, results, tokens) -> bool:
        mani = self.manifest
        return self._do_path_if_name_one(results=results, tokens=tokens, mani=mani)

    def _do_path_if_name_one(self, *, results, tokens: list, mani: list) -> bool:
        #
        # a simple prefix match, no range involved
        #
        name = results.ref.name_one
        if name is None:
            return False
        #
        # we have to account for path>:date>:ordinal. ordinal is separate and comes after.
        # here we need to either limit by path and then by date, if needed, or do both at
        # once if both are called for.
        #
        first, last = None, None
        if len(tokens) > 0 and DateCompleter.is_date_or_date_prefix(tokens[0]):
            first, last = DateCompleter.get_bracket_dates(tokens[0])
        #
        #
        #
        # prefix, px = self._prefix(results)
        keep = []
        for _ in mani:
            path = _["file"]
            sw = self._starts_with(path, name)
            if not sw:
                ...
            if sw:
                if first is None:
                    keep.append(path)
                else:
                    date = exut.to_datetime(_["time"])
                    if first < date < last:
                        keep.append(path)
        results.files = keep
        return True

    def _starts_with(self, path, prefix) -> bool:
        path = self._path_minus_prolog(path=path)
        print(f"_starts_with: path: {path}, prefix: {prefix}")
        if path.startswith(prefix):
            return True
        i = path.rfind(".")
        if i == -1:
            return False
        path = path.replace(".", "_")
        return path.startswith(prefix)

    # ==============================================

    def _range_if_name_three(self, *, results, tokens) -> bool:
        mani = self.manifest
        return self._do_range_if_name_three(results=results, tokens=tokens, mani=mani)

    def _do_range_if_name_three(self, *, results, tokens: list, mani: list) -> bool:
        if tokens is None:
            raise ValueError("Name three tokens cannot be None")
        if len(tokens) == 0:
            return False
        if tokens[0] in ["yesterday", "today"]:
            raise ValueError(
                "Range of explictly given date cannot be limited to yesterday or today"
            )
        if results.files is None:
            raise ValueError("Results file list cannot be None")
        if len(results) == 0:
            return False
        name = results.ref.name_three
        date = DateCompleter.to_date(name)
        if date is None:
            return False
        #
        # if we have a few times to find we'll index first. it isn't
        # great, but if we have a performance issue in the field we'll
        # switch to a database version.
        #
        index = None
        if len(results) > 3:
            index = {}
            for m in mani:
                index[m["file"]] = m["time"]
        keep = []
        for _ in results.files:
            #
            #
            #
            t = None
            if index is None:
                for m in mani:
                    path = m["file"]
                    #
                    # because this is file v. file we need to apply minus to _, the "prefix",
                    # because starts_with assumes the prefix is name_one
                    #
                    minus = self._path_minus_prolog(
                        named_file_name=self.ref.root_major, path=_
                    )
                    if self._starts_with(path, minus):
                        t = m["time"]
                        break
            else:
                t = index.get(_)
            if t is None:
                raise ValueError(f"Cannot find a time for {_}")
            t = exut.to_datetime(t)
            if tokens[0] in ["before", "to"]:
                if t < date:
                    keep.append(_)
            elif tokens[0] in ["after", "from"]:
                if t > date:
                    keep.append(_)
            else:
                keep.append(_)
        results.files = keep
        #
        # consume the token. if we have an ordinal in name_three_tokens
        # it expects to be the last remaining token.
        #
        del tokens[0]
        return True

    # ==============================================

    def _arrival_ordinal_if_name_three(self, *, results, tokens: list[str]) -> bool:
        mani = self.manifest
        return self._do_arrival_ordinal_if_name_three(
            results=results, tokens=tokens, mani=mani
        )

    def _do_arrival_ordinal_if_name_three(
        self, *, results, tokens: list, mani: list
    ) -> bool:
        if results.ref.name_three is None:
            return False
        #
        # we can check the ordinal exists here, but we're going to handle it in
        # a specific name_three ordinals method.
        #
        if len(tokens) == 0:
            raise ValueError("Cannot have a name_three without tokens")
        if not tokens[0] in ["first", "last"] or tokens[0].isdigit():
            return False
        ffrom, tto = DateCompleter.get_bracket_dates(results.ref.name_three)
        if ffrom is None:
            return False
        #
        # we are limiting by date but we only have file paths in results.files,
        # so we need to loop the manifest to find the dates.
        #
        index = None
        if len(results) > 3:
            index = {}
            for m in mani:
                index[m["file"]] = m["time"]
        keep = []
        for _ in results.files:
            t = None
            if index is None:
                for m in mani:
                    if m["file"] == _:
                        t = m["time"]
                        break
            else:
                t = index.get(_)
            if t is None:
                raise ValueError("Cannot find a time for {_}")
            t = exut.to_datetime(t)
            if ffrom < t < tto:
                keep.append(_)
        results.files = keep

    def _ordinal_if_name_one(self, *, results, tokens: list[str]) -> bool:
        self._ordinal_if(
            results=results, tokens=tokens, name_exists=results.ref.name_one is not None
        )

    def _ordinal_if_name_three(self, *, results, tokens: list[str]) -> bool:
        # name_three never exists in the sense that we never want name_three tokens
        # to look to the manifest. they only filter what name_one found. if that is
        # nothing than we have nothing to filter. in the case of name_one we would
        # look to the manifest if name_one is None.
        return self._ordinal_if(results=results, tokens=tokens, name_exists=True)

    def _ordinal_if(self, *, results, tokens: list[str], name_exists: bool) -> bool:
        mani = self.manifest
        return self._do_ordinal_if(
            results=results, tokens=tokens, mani=mani, name_exists=name_exists
        )

    def _do_ordinal_if(
        self, *, results, tokens: list[str], mani: list, name_exists: bool
    ) -> bool:
        if len(tokens) == 0:
            return False
        if tokens[0] not in ["first", "last"] and not tokens[0].isdigit():
            return False
        #
        # if results.files is None or 0 and name_one is None we need to pick
        # from all the files
        #
        if tokens[0] in ["first", "last"]:
            if (
                results.files is None or len(results.files) == 0
            ) and name_exists is False:
                if len(mani) > 0:
                    results.files = (
                        [mani[0]["file"]]
                        if tokens[0] == "first"
                        else [mani[-1]["file"]]
                    )
                else:
                    results.files = []
                return True if len(results.files) == 0 else False
            if len(results.files) == 0:
                return False
            if tokens[0] == "first":
                results.files = [results.files[0]]
                return True
            else:
                results.files = [results.files[-1]]
                return True
        i = int(tokens[0])
        if (results.files is None or len(results.files) == 0) and name_exists is False:
            if len(mani) > i:
                results.files = [mani[i]["file"]]
            else:
                results.files = []
            return True if len(results.files) == 0 else False
        elif i >= len(results):
            results.files = []
            return False
        results.files = [results.files[i]]
        return True

    # ==============================================
    # ==============================================

    def _range_as_timestring(self, rrange: str) -> str:
        if rrange == "today":
            dat = datetime.now(timezone.utc)
        elif rrange == "yesterday":
            dat = datetime.now(timezone.utc) - timedelta(days=1)
        return dat.strftime("%Y-%m-%d_%H-%M-%S")

    def _prefix(self, results) -> tuple[str, int]:
        inputs = self.csvpaths.config.get(section="inputs", name="files")
        named_file = results.ref.root_major
        prefix = os.path.join(inputs, named_file)
        return (prefix, len(prefix))

    def _get_range_from_tokens(self, results, tokens) -> str:
        rrange = results.ref.get_range_from_tokens(tokens)
        if rrange is not None:
            tokens.remove(rrange)
        return rrange
