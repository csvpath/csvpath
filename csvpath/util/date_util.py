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
    def all_after(cls, adate, dates: list) -> list:
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
        adate = adate.replace(tzinfo=timezone.utc)
        dates = cls.proper_dates(dates)
        for i, dt in enumerate(dates):
            if dt > adate:
                dates[i] = None
        return dates
