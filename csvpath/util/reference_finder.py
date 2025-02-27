# pylint: disable=C0114
from datetime import timedelta, timezone
import datetime
from csvpath.util.reference_parser import ReferenceParser

# TODO: probably we should hoist up expr utility, but for now leaving it in matching
from csvpath.matching.util.expression_utility import ExpressionUtility


class ReferenceFinder:
    def __init__(self, csvpaths, name) -> None:
        ...

    def resolve(self) -> str:
        ...

    def __new__(cls, csvpaths, name):
        if cls == ReferenceFinder:
            ref = ReferenceParser(name)
            if ref.datatype == ReferenceParser.FILES:
                return FilesReferenceFinder(csvpaths, ref=ref, name=name)
            elif ref.datatype == ReferenceParser.RESULTS:
                return ResultsReferenceFinder(csvpaths, name=name)
            else:
                raise ValueError(
                    f"Reference datatype must be in [{ReferenceParser.RESULTS}, {ReferenceParser.FILES}]"
                )
        else:
            instance = super().__new__(cls)
            return instance


class FilesReferenceFinder:
    #
    # references to prior versions of a file
    #    >> by index:
    #         $myfilename.files.3
    #    >> by day [today|yesterday] and [:first|:last|:index]:
    #         $myfilename.files.yesterday:last
    #    >> by date and [:before|:after|None]:
    #         $myfilename.files.2025-01-01_14-30-00:before
    #    >> by fingerprint:
    #         $myfilename.files.12467d811d1589ede586e3a42c41046641bedc1c73941f4c21e2fd2966f188b4
    #
    def __init__(self, csvpaths, *, ref, name) -> None:
        self._csvpaths = csvpaths
        self._ref = ref
        self._name = name
        self._mani = None

    def resolve(self) -> str:
        n = self._ref.name_one
        #
        # fingerprint
        #
        file = self._path_for_fingerprint_if(n)
        if file is not None:
            return file
        #
        # index
        #
        file = self._path_for_index_if(n)
        if file is not None:
            return file
        #
        # day
        #
        file = self._path_for_day_if(n)
        if file is not None:
            return file
        #
        # date
        #
        file = self._path_for_date_if(n)
        if file is not None:
            return file
        raise ValueError(f"Reference {self._name} is not valid")

    def _is_day(self) -> bool:
        n = self._ref.name_one
        if n.find(":"):
            n = n[0 : n.find(":")]
        return n in ["yesterday", "today"]

    def _path_for_day_if(self) -> str:
        if self._is_day():
            day = None
            pointer = None
            n = self._ref.name_one
            i = n.find(":")
            if i > -1:
                day = n[0:i]
                pointer = n[i + 1 :]
            else:
                day = n
                pointer = "last"
            pointer = self._pointer(n, "last")
            dat = None
            if day == "today":
                dat = datetime.datetime.now()
            if day == "yesterday":
                dat = datetime.datetime.now() - timedelta(days=1)
            ds = self._list_of_records_by_date(dat)
            #
            #
            #
            if pointer == "last":
                return ds[len(ds) - 1]["file"]
            if pointer == "first":
                return ds[0]["file"]
            i = ExpressionUtility.to_int(pointer)
            if not isinstance(i, int):
                raise ValueError(
                    f"Pointer {pointer} should be :first, :last, or :N where N is an int"
                )
            return ds[i]["file"]

    def _path_for_date_if(self) -> str:
        s = self._complete_date_string()
        dat = datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
        pointer = self._pointer(self._ref.name_one, "after")
        return self._find_in_date(dat, pointer)

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

    def _find_in_date(self, adate, pointer) -> list:
        mani = self.manifest
        lst = []
        for _ in mani:
            t = mani["time"]
            td = ExpressionUtility.to_datetime(t)
            lst.append(td)
        #
        # find the right date
        #
        i = self._find_in_dates(lst, adate, pointer)
        if i is None:
            return None
        return mani[i]["file"]

    def _find_in_dates(
        self, lst: list[datetime.datetime], adate: datetime.datetime, pointer: str
    ) -> str:
        for i, d in enumerate(lst):
            if pointer == "before":
                if d > adate:
                    if i == 0:
                        return None
                    else:
                        return i - 1
            elif pointer == "after":
                if d > adate:
                    return i
            elif pointer is None:
                if (
                    d.year == adate.year
                    and d.month == adate.month
                    and d.day == adate.day
                    and d.hour == adate.hour
                    and d.minute == adate.minute
                    and d.second == adate.second
                ):
                    return i
            else:
                raise ValueError(
                    f"Pointer {pointer} is incorrect. Only 'before' and 'after' are allowed"
                )
        return None

    def _complete_date_string(self) -> str:
        n = self._not_pointer(self._ref.name_one)
        dat = ""
        chk = 0
        for c in n:
            #
            # 2025-03-23_13-30-00
            #
            # print(f"n[{chk}] = {c}")
            if chk == 0:
                if c != "2":
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 2"
                    )
            elif chk == 1:
                if c != "0":
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0"
                    )
            elif chk in [2, 3, 6, 12, 15, 18]:
                if c not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be an integer"
                    )
            elif chk in [4, 7, 13, 16] and c != "-":
                raise ValueError(
                    f"Character in position 5 of date string {n} must be a '-'"
                )
            elif chk == 5:
                if c not in ["0", "1", "2", "3"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0 - 3"
                    )
            elif chk == 11:
                if c not in ["0", "1", "2"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0 - 2"
                    )
            elif chk in [14, 17]:
                if c not in ["0", "1", "2", "3", "4", "5"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0 - 5"
                    )
            elif chk == 10:
                if c != "_":
                    raise ValueError(
                        "Character in position {chk} of date string {n} must be an '_'"
                    )
            chk += 1

        t = "2025-01-01_00-00-00"
        dat = n
        dat = f"{n}{t[chk:]}"
        print(f"dat: {dat}")
        return dat

    def _pointer(self, n: str, default: str = None) -> str:
        if n is None:
            return None
        if n.find(":") == -1:
            return default
        return n[n.find(":") + 1 :]

    def _not_pointer(self, n: str) -> str:
        if n is None:
            return None
        if n.find(":") == -1:
            return n
        return n[0 : n.find(":")]

    def _path_for_fingerprint_if(self) -> str:
        n = self._ref.name_one
        mani = self.manifest
        for r in mani:
            if r.get("fingerprint") == n:
                return r.get("file")

    def _path_for_index_if(self) -> str:
        n = self._ref.name_one
        if not ExpressionUtility.is_number(n):
            return
        n = ExpressionUtility.to_int(n)
        mani = self.manifest
        for i, r in enumerate(mani):
            if n == i:
                return r.get("file")

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


class ResultsReferenceFinder:
    def __init__(self, csvpaths, *, name) -> None:
        self._csvpaths = csvpaths
        self._name = name

    def resolve(self) -> str:
        reman = self._csvpaths.results_manager
        ret = reman.data_file_for_reference(self._name)
        return ret
