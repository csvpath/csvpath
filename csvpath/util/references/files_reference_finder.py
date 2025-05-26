# pylint: disable=C0114
import os
import datetime
from datetime import timedelta, timezone
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.date_util import DateUtility as daut
from .reference_parser import ReferenceParser
from .ref_utils import ReferenceUtility as refu


class FilesReferenceFinder:
    #
    # references to prior versions of a file
    #    >> by index:
    #         $myfilename.files.:3
    #    >> by day [today|yesterday] and [:first|:last|:index]:
    #         $myfilename.files.yesterday:last
    #    >> by date and [:before|:after|None]:
    #         $myfilename.files.2025-01-01_14-30-00:before
    #    >> by fingerprint:
    #         $myfilename.files.12467d811d1589ede586e3a42c41046641bedc1c73941f4c21e2fd2966f188b4
    #  TODO:
    #    >> by original file name:
    #         $myfilename.files.orders-march_csv[:first|:last|:index|:all]
    #         $myfilename.files.orders-march_csv.2025-02-28[:after|:before]
    #
    # NOTE: adding :all and possibly other ways to get multiple file paths results. if we get multiple
    # paths when not expected we will raise an exception. if we get multiple at the CsvPaths that
    # would be expected and we'll handle it by iterating the collect/fast-forward/next calls. next()
    # may be an odd-ball because of the iteration on actual lines. have to think about that. worst case
    # we could raise an error as unsupported.
    #
    # if both ref and name are passed in name wins
    #
    def __init__(self, csvpaths, *, ref: ReferenceParser = None, name=None) -> None:
        self._csvpaths = csvpaths
        self._name = name
        self._ref = None
        if self._name is not None:
            if ref is not None:
                raise ValueError("Cannot provide both ref and name")
            self._ref = ReferenceParser(name)
        if self._ref is None:
            self._ref = ref
        if name is None:
            self._name = ref.ref_string
        self._mani = None
        self._version_index = -1

    @property
    def ref(self) -> ReferenceParser:
        return self._ref

    @property
    def name(self) -> str:
        return self._name

    @property
    def version_index(self) -> int:
        if self._version_index == -1:
            self.resolve()
        return self._version_index

    @property
    def manifest(self):
        if self._mani is None:
            fm = self._csvpaths.file_manager
            r = fm.registrar
            rm = self._ref.root_major
            home = fm.named_file_home(rm)
            mani_path = r.manifest_path(home)
            self._mani = r.get_manifest(mani_path)
        return self._mani

    def get_manifest_entry_for_reference(self) -> dict:
        mani = self.manifest
        file = self.resolve()
        if isinstance(file, list):
            file = file[len(file) - 1]
        for _ in mani:
            if file == _["file"]:
                return _
        raise ValueError(
            f"Cannot match reference {self.ref._ref_string} pointing to file {file} to a manifest entry"
        )

    # $invoices.files.acme/2025/Jan/Acme_invoices_2025-01-31_csv

    def resolve(self) -> str | list:
        #
        # search order:
        #   fingerprint         exact match
        #   filename            prefix match
        #   yesterday|today
        #   date prefix match
        #
        # exact fingerprint
        #
        file = self._path_for_fingerprint_if()
        if file is not None:
            return file
        #
        # progressive or exact filename
        #
        file = self._paths_for_filename_if()
        if file and len(file) > 0:
            return file
        #
        # bare index -- a :n
        #
        file = self._path_for_bare_index_if()
        if file is not None:
            return file
        #
        # day: yesterday, today
        #
        file = self._path_for_day_if()
        if file is not None:
            return file
        #
        # progressive arrival date match
        #
        file = self._path_for_date_if()
        if file is not None:
            return file
        #
        # should this really be an exception? if we think of refs as a query language we
        # would not want a query without results to be exceptional.
        #
        # from that point of view we maybe should return [].
        #
        return []
        """
        raise ValueError(
            f"Reference {self.name} does not identify files with {self._ref}"
        )
        """

    def _paths_for_filename_if(self, exact: bool = False) -> list:
        res = self._filename_if(exact)
        if res:
            res = self._filename_filter(res)
        return res

    def _filename_filter(self, files: list) -> list:
        #
        # if we have a third ref component (name_three) it would be a date prefix. possibly
        # with a filter. (:first|:last|:all|:index)
        #
        n = self._ref.name_three
        if n is None:
            return files
        pointer = refu.pointer(n, ":all")
        s = refu.not_pointer(n)
        s = self._complete_date_string(s)
        adate = datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
        lst = self._find_in_range(adate=adate, pointer=pointer)
        ret = []
        #
        # we reverse the original way of doing it because _find_in_date is looking at the
        # manifest; whereas, the files var is populated from Nos.listdir, which is order
        # unknown. this gotcha is going to come up again at some point.
        #
        if not isinstance(lst, list):
            lst = [lst]
        if lst and len(lst) > 0:
            for file in lst:
                if file in files:
                    ret.append(file)
        return ret

    def _filename_if(self, exact: bool = False) -> list:
        #
        # remember that files are coming in manifest order supposedly. however,
        # there may be cases where we get filesystem / bucket order, which is
        # not ordered.
        #
        #
        # a progressive match filename search that can be limited by a date in name_three
        # if we wanted to set a range we could use name_four (using a # delimiter) but
        # we don't know that's a real need yet.
        #
        looking_for = self._ref.name_one
        i = looking_for.find(":")
        if i == 0:
            return
        name_filter = looking_for[i:] if i > -1 else None
        looking_for = looking_for[0:i] if i > -1 else looking_for
        files = self._collect_paths_for_filename_if(looking_for, exact)
        files = self._filter(files, name_filter)
        #
        # we convert the . extension of a file to _ extension so it doesn't conflict with a
        # references dotted segments. here we convert back to a . extension.
        #
        for i, f in enumerate(files):
            base = os.path.dirname(f)
            ending = f[len(base) :]
            found = False
            for ext in self._csvpaths.config.csv_file_extensions:
                if base.endswith(f"_{ext}"):
                    f2 = base[0 : base.rfind(f"_{ext}")]
                    f2 = f"{f2}.{ext}"
                    base = f2
                    found = True
                    break
            if found:
                f = f"{base}{ending}"
                files[i] = f
        return files

    def _filter(self, files: list, name_filter) -> list:
        if files is None:
            return []
        if len(files) == 0:
            return files
        if name_filter is None:
            #
            # we were always returning the last bytes. but given that :last is now an
            # explicit option and we have reasons to want multiple files, we should not
            # assume :last
            #
            return files
        name_filter = name_filter.strip()
        if name_filter == ":all":
            return files
        #
        # for first, last and index we need the possibles in an arrival-date ordered list
        #
        ordered = self._to_arrival_date_order(files)
        if name_filter == ":last" or name_filter == "" or name_filter == ":":
            return [ordered[len(ordered) - 1]]
        if name_filter == ":first":
            return [ordered[0]]
        n = name_filter[1:]
        n = ExpressionUtility.to_int(n)
        if isinstance(n, int):
            if n >= len(ordered) or n < 0:
                return []
            return [ordered[n]]
        raise RuntimeError(f"Unable to filter files {files} with {name_filter}")

    def _to_arrival_date_order(self, files: list[str]) -> list[str]:
        mani = self.manifest
        arrivals = {}
        # create a date->fingerprint dictionary.
        for file in files:
            fingerprint = file.replace("\\", "/")
            fingerprint = fingerprint[fingerprint.rfind("/") + 1 :]
            fingerprint = fingerprint[0 : fingerprint.rfind(".")]
            for item in mani:
                if item["fingerprint"] == fingerprint:
                    d = ExpressionUtility.to_datetime(item["time"])
                    arrivals[d] = item
        # sort the keys
        dates = list(arrivals.keys())
        dates.sort()
        ordered = []
        for d in dates:
            ordered.append(arrivals[d]["file"])
        return ordered

    def _collect_paths_for_filename_if(
        self, looking_for: str, exact: bool = False
    ) -> list:
        #
        # this is an exact match, or, if no exact match, a prefix match. it takes:
        #   > :first|:last|:all
        #   > a prefix date in the ref.name_three position (i.e. $n.files.x.date
        #
        name = self._ref.root_major
        base = self._csvpaths.config.get(section="inputs", name="files")
        starting = os.path.join(base, name)
        #
        #
        #
        e = os.path.join(starting, looking_for)
        if exact is True:
            nos = Nos(e)
            #
            # need to check dir for being 1) exact match and 2) the direct parent
            # of actual data files. we can assume that any files we find means we're
            # in the right place. we return all the files.
            #
            if not nos.dir_exists():
                return None
            files = nos.listdir(files_only=True, recurse=False)
            possibles = []
            for file in files:
                possibles.append(os.path.join(nos.path, file))
            return possibles
        else:
            possibles = []
            #
            # this cannot be os.walk!
            #
            lf = os.path.join(starting, looking_for)
            lf = pathu.resep(lf)
            nos = Nos(starting)
            lst = nos.listdir(files_only=True, recurse=True)
            for file in lst:
                if file.find("manifest.json") > -1:
                    continue
                #
                # if we have a prefix match and there are no directories we are at the
                # physical file level. every file should be a delimited data file named
                # by its sha256 fingerprint + extension.
                #
                match = file.startswith(lf)
                if match:
                    possibles.append(file)
                    continue
                #
                # check if we have an extension that needs dot to become underscore because
                # dots don't work for references.
                #
                i = file.find(".")
                j = i + 1
                file = f"{file[0:i]}_{file[j:]}"
                match = file.startswith(lf)
                if match:
                    possibles.append(file)
            return possibles

    def _is_day(self) -> bool:
        return (
            self._ref.name_one.find(":yesterday") > -1
            or self._ref.name_one.find(":today") > -1
        )
        """
        n = self._ref.name_one
        if n.find(":"):
            n = n[0 : n.find(":")]
        return n in ["yesterday", "today"]
        """

    def _path_for_day_if(self) -> list[str]:
        #
        # takes :first, :last, :all, :<index>
        #
        if self._is_day():
            day = self._ref.name_one[1:]
            i = day.find(":")
            if i > -1:
                pointer = day[i + 1 :]
                day = day[0:i]
            else:
                pointer = "last"
            dat = None
            if day == "today":
                dat = datetime.datetime.now(timezone.utc)
            elif day == "yesterday":
                dat = datetime.datetime.now(timezone.utc) - timedelta(days=1)
            #
            # what if none?
            #
            ds = self._list_of_records_by_date(dat)
            #
            #
            #
            if pointer == "last":
                self._version_index = len(ds) - 1
                return [ds[self._version_index]["file"]]
            if pointer == "first":
                self._version_index = 0
                return [ds[0]["file"]]
            elif pointer == "all":
                multi = []
                for d in ds:
                    multi.append(d["file"])
                return multi
            i = ExpressionUtility.to_int(pointer)
            if not isinstance(i, int):
                raise ValueError(
                    f"Pointer {pointer} should be :first, :last, :all, or :N where N is an int"
                )
            self._version_index = i
            return [ds[i]["file"]]

    def _path_for_date_if(self) -> str | list:
        try:
            name_one = self._ref.name_one
            pointer = refu.pointer(name_one, "after")
            s = refu.not_pointer(name_one)
            s = self._complete_date_string(s)
            dat = datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
            #
            # this is an interesting point because what we do depends on pointers
            # and may have been different intentions at different times. today --
            # and i think this is logical
            #  - after takes a timestamp forward to the present
            #  - before takes the history from moment 1 to the timestamp
            #  - all is all
            #  - last-before (or last?) is the most recent to the timestamp
            #  - first is the first following the timestamp
            # and for the future
            #  - if we do 'on' it would be within the most specific unit (e.g. '2025-05-10' would be on that day
            #  - if we did a between it would be timestamp:timestamp
            #
            # long story short, we can keep _find_in_date for the other place used, but we need
            # a method that looks at a range of dates, not just a day
            #
            # exp.
            #
            _ = self._find_in_range(dat, pointer)
            #
            #
            # _ = self._find_in_date(dat, pointer)
            return _
        except ValueError:
            #
            # we return none because this is expected. we won't like the date
            # string in some cases because it's not a date string. in those cases
            # we want the if/else series of checks above to continue with other
            # strategies for finding results.
            #
            return None

    def _find_in_range(self, adate, pointer) -> list:
        if pointer == "after":
            return self._all_after(adate)
        elif pointer == "before":
            return self._all_before(adate)
        elif pointer == "first":
            ret = self._first_after(adate)
            if not isinstance(ret, list):
                ret = [ret]
            return ret
        elif pointer == "last":
            ret = self._last_before(adate)
            if not isinstance(ret, list):
                ret = [ret]
            return ret
        else:
            raise ValueError("Unknown pointer: {pointer}")

    def _all_after(self, adate) -> list:
        lst = [t["time"] for t in self.manifest]
        lst2 = daut.all_after(adate, lst)
        lst3 = []
        for i, t in enumerate(lst2):
            if t is not None:
                lst3.append(self.manifest[i]["file"])
        return lst3

    def _all_before(self, adate) -> list:
        lst = []
        for t in self.manifest:
            lst.append(t["time"])
        lst2 = daut.all_before(adate, lst)
        lst3 = []
        for i, t in enumerate(lst2):
            if t is not None:
                lst3.append(self.manifest[i]["file"])
        return lst3

    def _first_after(self, adate) -> str:
        lst = [t["time"] for t in self.manifest]
        lst2 = daut.all_after(adate, lst)
        for i, t in enumerate(lst2):
            if t is not None:
                return self.manifest[i]["file"]

    def _last_before(self, adate) -> str:
        lst = [t["time"] for t in self.manifest]
        lst2 = daut.all_before(adate, lst)
        for i, t in enumerate(lst2):
            if t is None:
                if i == 0:
                    return None
                else:
                    return self.manifest[i - 1]["file"]

    def _find_in_date(self, adate, pointer) -> list:
        mani = self.manifest
        lst = []
        adate = adate.replace(tzinfo=timezone.utc)
        for _ in mani:
            t = _["time"]
            td = ExpressionUtility.to_datetime(t)
            td = td.replace(tzinfo=timezone.utc)
            #
            # determine if td is within adate's day.
            # we'll take all the dates and the pointer will
            # tell us what to do. :all will give any dates that
            # are before the datetime we use as a search.
            #
            # this can't be right? we want all dates on a day, before a day or after a day, right?
            # maybe not in all cases, but in the case i'm looking at this doesn't work.
            #
            if (
                td.year == adate.year
                and td.month == adate.month
                and td.day == adate.day
            ):
                lst.append(td)
        #
        # find the right date
        #
        i = self._find_in_dates(lst, adate, pointer)
        if i is None:
            return None
        multi = []
        for ii in i:
            multi.append(mani[ii]["file"])
        self._version_index = -1
        return multi

    def _find_in_dates(
        self, lst: list[datetime.datetime], adate: datetime.datetime, pointer: str
    ) -> list:
        if not lst or len(lst) == 0:
            return None
        adate = adate.replace(tzinfo=timezone.utc)
        multi = []
        if pointer == "last":
            return [len(lst) - 1]
        for i, d in enumerate(lst):
            d = d.replace(tzinfo=timezone.utc)
            if pointer == "before":
                if d < adate:
                    multi.append(i)
            elif pointer == "first":
                if d >= adate:
                    return [i]
            elif pointer == "after":
                if d > adate:
                    multi.append(i)
            elif pointer is None:
                if (
                    d.year == adate.year
                    and d.month == adate.month
                    and d.day == adate.day
                    and d.hour == adate.hour
                    and d.minute == adate.minute
                    and d.second == adate.second
                ):
                    return [i]
            elif pointer == "all":
                multi.append(i)
            else:
                raise ValueError(
                    f"Pointer {pointer} is incorrect. Only 'before', 'first', 'after', 'all', and None are allowed, not {pointer}"
                )
        return None if len(multi) == 0 else multi

    def _list_of_records_by_date(self, adate=None) -> list:
        mani = self.manifest
        lst = []
        adate = adate.astimezone(timezone.utc) if adate is not None else None
        for _ in mani:
            t = _["time"]
            td = ExpressionUtility.to_datetime(t)
            if adate is None:
                lst.append(_)
            elif (
                adate.year == td.year
                and adate.month == td.month
                and adate.day == td.day
            ):
                lst.append(_)
        return lst

    def _complete_date_string(self, n: str) -> str:
        dat = ""
        chk = 0
        for c in n:
            #
            # 2025-03-23_13-30-00
            #
            if chk == 0:
                if c != "2":
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 2, not {c}"
                    )
            elif chk == 1:
                if c != "0":
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0, not {c}"
                    )
            elif chk in [2, 3, 6, 12, 15, 18]:
                if c not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be an integer, not {c}"
                    )
            elif chk in [4, 7, 13, 16] and c != "-":
                raise ValueError(
                    f"Character in position 5 of date string {n} must be a '-', not {c}"
                )
            elif chk == 5:
                if c not in ["0", "1", "2", "3"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0 - 3, not {c}"
                    )
            elif chk == 11:
                if c not in ["0", "1", "2"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0 - 2, not {c}"
                    )
            elif chk in [14, 17]:
                if c not in ["0", "1", "2", "3", "4", "5"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0 - 5, not {c}"
                    )
            elif chk == 10:
                if c != "_":
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be an '_', not {c}"
                    )
            chk += 1
        t = "2025-01-01_00-00-00"
        dat = n
        dat = f"{n}{t[chk:]}"
        return dat

    def _path_for_fingerprint_if(self) -> str:
        n = self._ref.name_one
        mani = self.manifest
        for r in mani:
            if r.get("fingerprint") == n:
                return r.get("file")

    def _path_for_bare_index_if(self) -> str:
        n = self._ref.name_one
        n = refu.bare_index_if(n)
        if n is not None:
            self._version_index = n
            mani = self.manifest
            for i, r in enumerate(mani):
                if n == i:
                    return [r.get("file")]
