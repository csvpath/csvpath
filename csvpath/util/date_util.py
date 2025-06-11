import datetime
from datetime import timezone

from csvpath.matching.util.expression_utility import ExpressionUtility as exut


class DateUtility:
    @classmethod
    def proper_dates(cls, dates: list) -> list:
        dates2 = dates[:]
        for i, dt in enumerate(dates):
            _ = exut.to_datetime(dt)
            dates2[i] = _.replace(tzinfo=timezone.utc)
        dates2.sort()
        return dates2

    @classmethod
    def dates_from_list(cls, dates) -> list:
        #
        # pulls dates out of a list in order. mainly for wrapping
        # all_after and all_before.
        #
        lst = []
        for d in dates:
            if isinstance(d, datetime.datetime):
                lst.append(d)
        return lst

    @classmethod
    def all_after(cls, adate, dates: list) -> list:
        #
        # takes a list of dates and returns those dates
        # after the reference date with Nones representing
        # the positions of dates that were not after
        #
        adate = adate.replace(tzinfo=timezone.utc)
        dates = cls.proper_dates(dates)
        for i, dt in enumerate(dates):
            if adate < dt:
                return dates
            else:
                dates[i] = None
        return dates

    @classmethod
    def all_before(cls, adate, dates: list) -> list:
        #
        # takes a list of dates and returns those dates
        # before the reference date with Nones representing
        # the positions of dates that were not before
        #
        adate = adate.replace(tzinfo=timezone.utc)
        dates = cls.proper_dates(dates)
        for i, dt in enumerate(dates):
            if dt >= adate:
                dates[i] = None
        return dates
