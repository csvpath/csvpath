import datetime
from datetime import timedelta, timezone


class DateCompleter:
    @classmethod
    def get_bracket_dates(
        cls, datestr: str, *, unit: str = None
    ) -> tuple[datetime, datetime]:
        if unit is None:
            unit = cls.smallest_unit(datestr)
        d = cls.to_date(datestr)
        if d is None:
            return (None, None)
        ffrom = None
        tto = None
        if unit == "year":
            ffrom = datetime.datetime(d.year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            tto = datetime.datetime(d.year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        elif unit == "month":
            ffrom = datetime.datetime(d.year, d.month, 1, 0, 0, 0, tzinfo=timezone.utc)
            tto = datetime.datetime(
                d.year, d.month + 1, 1, 0, 0, 0, tzinfo=timezone.utc
            )
        elif unit == "day":
            ffrom = datetime.datetime(
                d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc
            )
            tto = datetime.datetime(
                d.year, d.month, d.day + 1, 0, 0, 0, tzinfo=timezone.utc
            )
        elif unit == "hour":
            ffrom = datetime.datetime(
                d.year, d.month, d.day, d.hour, 0, 0, tzinfo=timezone.utc
            )
            tto = datetime.datetime(
                d.year, d.month, d.day, d.hour + 1, 0, 0, tzinfo=timezone.utc
            )
        elif unit == "minute":
            ffrom = datetime.datetime(
                d.year, d.month, d.day, d.hour, d.minute, 0, tzinfo=timezone.utc
            )
            tto = datetime.datetime(
                d.year, d.month, d.day, d.hour, d.minute + 1, 0, tzinfo=timezone.utc
            )
        elif unit == "second":
            ffrom = datetime.datetime(
                d.year, d.month, d.day, d.hour, d.minute, d.second, tzinfo=timezone.utc
            )
            tto = datetime.datetime(
                d.year,
                d.month,
                d.day,
                d.hour,
                d.minute,
                d.second + 1,
                tzinfo=timezone.utc,
            )
        else:
            raise ValueError(f"Unknown unit: {unit}")
        return (ffrom, tto)

    @classmethod
    def is_date_or_date_prefix(cls, datestr: str) -> datetime:
        if datestr is None:
            return False
        try:
            datestr = cls.get(datestr)
            if datestr is None:
                return False
            date = cls.to_date(datestr)
            return date is not None
        except Exception:
            return False

    @classmethod
    def is_date(cls, datestr: str) -> datetime:
        if datestr is None:
            return False
        return cls.to_date(datestr) is not None

    @classmethod
    def to_date(cls, datestr: str) -> datetime:
        try:
            s = cls.get(datestr)
            dat = datetime.datetime.strptime(f"{s}+0000", "%Y-%m-%d_%H-%M-%S%z")
            dat = dat.astimezone(timezone.utc)
            return dat
        except Exception:
            ...
        return None

    @classmethod
    def complete_if(cls, n: str) -> str:
        try:
            return cls.get(n)
        except Exception:
            return None

    @classmethod
    def get(cls, n: str) -> str:
        if len(n) < 5:
            raise ValueError(
                f"Cannot complete date prefix {n} without at least a year ending in a -"
            )
        chk = cls.complete_to(n)
        t = "2025-01-01_00-00-00"
        dat = f"{n}{t[chk:]}"
        return dat

    @classmethod
    def smallest_unit(cls, n: str = None, c: int = -1) -> str:
        if n is None and c == -1:
            raise ValueError(
                "Provide a completable date string or a number indicating the unit"
            )
        if c < 0:
            c = cls.complete_to(n)
        if c <= 5:
            return "year"
        elif c <= 8:
            return "month"
        elif c <= 11:
            return "day"
        elif c <= 14:
            return "hour"
        elif c <= 17:
            return "minute"
        elif c <= 20:
            return "second"
        raise ValueError(
            f"{len(n)} chars. Cannot be > 18 characters in completable date string"
        )

    @classmethod
    def complete_to(cls, n: str) -> int:
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
        return chk
