import datetime
from datetime import timedelta, timezone, date
from csvpath.util.references.reference_results import ReferenceResults
from csvpath.util.references.tools.date_completer import DateCompleter
from csvpath.matching.util.expression_utility import ExpressionUtility as exut
from csvpath.util.nos import Nos
from dateutil.relativedelta import relativedelta


class DateFilter:
    @classmethod
    def update(
        cls,
        results: ReferenceResults,
        *,
        name_or_token: str = None,
        tokens: list[str] = None
    ) -> None:
        if tokens is None or len(tokens) == 0 and name_or_token is None:
            name_or_token = results.ref.name_one
        ref = results.ref
        #
        # if we have a date and no tokens we return the range
        #
        if not tokens or len(tokens) == 0 or (len(tokens) == 1 and "all" in tokens):
            #
            # if name_one is not a date this will fail quietly
            #
            cls._possibles_for_range(results, name_or_token)
            return
        #
        # rightly or wrongly this isn't possible. see the excalidraw schematic.
        #
        # if cls.is_date(ref.name_one) and cls.has_date(tokens):
        #    cls._possibles_between_name_and_token(results)
        #    return
        if cls.is_date(ref.name_one) and "before" in tokens or "to" in tokens:
            cls.everything_before(results, name_or_token)
            return
        if cls.is_date(ref.name_one) and "after" in tokens or "from" in tokens:
            cls.everything_after(results, name_or_token)
            return
        #
        # we're done. if name_one is not a date we'll call the below methods
        # from the tokens filter, if needed.
        #
        return

    @classmethod
    def _possibles_between_name_and_token(cls, results) -> None:
        # this must be between name_one and a token. because we're a
        # result we must have a token to limit the range because we
        # can only return 1 results path. one of: date:date:first or
        # date:date:last or date:date[3]
        #
        # unless I'm wrong and we should allow more than one result...?
        # if we want to allow for a results to have multiple results
        # paths we can do it from the token filters by calling the
        # according_to_limit() method.
        #
        # regardless, only thing important now is that here we're using
        # name_one.
        #
        cls._possibles_between(
            results, results.ref.name_one, results.ref.name_one_tokens
        )
        return

    @classmethod
    def _possibles_between(cls, results, s: str, tokens) -> None:
        begin = cls.to_date(s)
        end = cls.find_date(tokens)
        if end is None:
            return
        cls.according_to_limit(results, begin, end)
        return

    @classmethod
    def _has_date(cls, tokens: list[str]) -> datetime:
        return cls.find_date(tokens) is not None

    @classmethod
    def find_date(cls, tokens: list[str]) -> datetime:
        for t in tokens:
            d = cls.to_date(t)
            if d:
                return d
        return None

    @classmethod
    def according_to_limit(
        cls, results, first: datetime, last: datetime, filter=False
    ) -> None:
        #
        # if filter is true, only select what to keep from results; otherwise
        # add from manifest to results
        #
        if first is None and last is None:
            # not doing everything here atm
            raise ValueError("First and last cannot both be None")
        mani = results.runs_manifest
        possibles = [m for m in mani if m["named_paths_name"] == results.ref.root_major]
        reals = []
        #
        # the manifest has one entry for every instance in a run, so we need to track the
        # run_uuids so we don't over count.
        #
        for _ in possibles:
            #
            # we check for deleted runs because we're looking at the manifest. deleted are
            # no longer available, but they still exist in the manifest, as well as any
            # databases. this will be expensive in some backends, but unless we want to
            # remove the record or update the entries to mark deleted we have to do it. since
            # end up doing this check multiple places (here, possibles, end) we need a
            # better solution like that.
            #
            rh = _["run_home"]
            nos = Nos(rh)
            if not nos.dir_exists():
                continue
            #
            #
            #
            dat = exut.to_datetime(_["time"])
            #
            # because of how we setup begin and end, begin is within the
            # ask and end is in the next unit beyond. i.e. the zeroth minute
            # of today is within and the zeroth minute of tomorrow is
            # outside
            #
            dat = dat.astimezone(timezone.utc) if dat else None
            last = last.astimezone(timezone.utc) if last else None
            first = first.astimezone(timezone.utc) if first else None
            add = False
            if first and last and first <= dat < last:
                add = True
            elif first is None and dat < last:
                add = True
            elif last is None and dat >= first:
                add = True
            if add is True:
                if _["run_home"] not in reals:
                    reals.append(_["run_home"])
        if filter:
            fs = []
            for _ in results.files:
                if _ in reals and _ not in fs:
                    fs.append(_)
            results.files = fs
        else:
            results.files = reals

    @classmethod
    def everything_before(cls, results, name_or_token: str) -> None:
        last = cls.to_date(name_or_token)
        cls.according_to_limit(results, None, last)

    @classmethod
    def everything_after(cls, results, name_or_token: str) -> None:
        first = cls.to_date(name_or_token)
        cls.according_to_limit(results, first, None)

    @classmethod
    def _possibles_for_range(cls, results, name_or_token: str) -> None:
        if name_or_token is None:
            return
        t = cls.range(name_or_token)
        if t is None:
            return
        begin, end = t
        if begin is None:
            return
        cls.according_to_limit(results, begin, end)

    @classmethod
    def range(cls, datestr) -> tuple[datetime, datetime]:
        adate = cls.to_date(datestr)
        if adate is None:
            return None
        adate = adate.replace(tzinfo=timezone.utc)
        #
        # date is the earliest moment in the most specific unit so we
        # need to find the next one of that unit to make our range.
        #
        dashes = datestr.count("-")
        if datestr.endswith("-"):
            dashes -= 1
        if dashes == 4:
            return (adate, adate)
        end = None
        if dashes == 4:
            end = adate + timedelta(minute=1)
        elif dashes == 3:
            end = adate + timedelta(hour=1)
        elif dashes == 2:
            end = adate + timedelta(days=1)
        elif dashes == 1:
            end = adate + relativedelta(months=1)
        elif dashes == 0:
            end = adate + relativedelta(years=1)
        return adate, end

    @classmethod
    def is_date(cls, name: str) -> bool:
        return cls.to_date(name) is not None

    @classmethod
    def to_date(cls, datestr: str) -> bool:
        try:
            s = DateCompleter.get(datestr)
            dat = datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
            return dat
        except Exception:
            ...
        return None
