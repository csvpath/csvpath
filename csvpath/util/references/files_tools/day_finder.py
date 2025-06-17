import datetime
from datetime import timedelta, timezone
from csvpath.matching.util.expression_utility import ExpressionUtility as exut
from csvpath.util.references.reference_results import ReferenceResults


class DayFinder:
    @classmethod
    def update(cls, results: ReferenceResults, tokens: list[str], token: str) -> bool:
        files = results.files
        lst = cls.get(results, tokens, token)
        if lst == []:
            return False
        remove = []
        for _ in files:
            if _ not in lst:
                remove.append(_)
        for _ in remove:
            files.remove(_)
        #
        # day finder consumes the 2nd token. e.g. today:1 or today:last are both
        # handled at the same time. we get two tokens. that means after dayfinder
        # we're done.
        #
        tokens.clear()
        return True

    @classmethod
    def get(cls, results, tokens: list[str], token: str) -> list[str]:
        #
        # takes :first, :last, :all, :<index>
        #
        if not cls._is_day(token):
            return []
        dat = None
        if token == "today":
            dat = datetime.datetime.now(timezone.utc)
        elif token == "yesterday":
            dat = datetime.datetime.now(timezone.utc) - timedelta(days=1)
        #
        # what if none?
        #
        ds = cls._records_by_date(results, dat)
        #
        #
        #
        if "last" in tokens:
            cls._version_index = len(ds) - 1
            return [ds[cls._version_index]["file"]]
        if "first" in tokens:
            cls._version_index = 0
            return [ds[0]["file"]]
        elif "all" in tokens:
            multi = []
            for d in ds:
                multi.append(d["file"])
            return multi
        #
        # check index
        #

        for _ in tokens:
            if _ == token:
                #
                #
                #
                continue
            i = exut.to_int(_)
            if not isinstance(i, int):
                raise ValueError(
                    f"Token {token} should be :first, :last, :all, or :N where N is an int"
                )
            #
            # is this still needed?
            #
            if len(ds) > i:
                return [ds[i]["file"]]
        return [ds[i]["file"]]

    @classmethod
    def _records_by_date(cls, results, adate=None) -> list:
        mani = results.manifest
        lst = []
        adate = adate.astimezone(timezone.utc) if adate is not None else None
        for _ in mani:
            t = _["time"]
            td = exut.to_datetime(t)
            # exp. exut does not do this already. needed?
            td = td.astimezone(timezone.utc)
            #
            if adate is None:
                lst.append(_)
            elif (
                adate.year == td.year
                and adate.month == td.month
                and adate.day == td.day
            ):
                lst.append(_)
        return lst

    @classmethod
    def _is_day(cls, token) -> bool:
        return token in ["yesterday", "today"]
