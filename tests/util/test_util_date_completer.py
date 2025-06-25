import unittest
import pytest
import os
from datetime import datetime
from csvpath.util.references.tools.date_completer import DateCompleter


class TestUtilDateCompleter(unittest.TestCase):
    def test_bracket_dates(self):
        ffrom, tto = DateCompleter.get_bracket_dates("2025-")
        assert ffrom.year == 2025
        assert ffrom.month == 1
        assert ffrom.day == 1
        assert ffrom.hour == 0
        assert ffrom.minute == 0
        assert ffrom.second == 0

        assert tto.year == 2026
        assert tto.month == 1
        assert tto.day == 1
        assert tto.hour == 0
        assert tto.minute == 0
        assert tto.second == 0

        ffrom, tto = DateCompleter.get_bracket_dates("2025-02-")
        assert ffrom.year == 2025
        assert ffrom.month == 2
        assert ffrom.day == 1
        assert ffrom.hour == 0
        assert ffrom.minute == 0
        assert ffrom.second == 0

        assert tto.year == 2025
        assert tto.month == 3
        assert tto.day == 1
        assert tto.hour == 0
        assert tto.minute == 0
        assert tto.second == 0

        ffrom, tto = DateCompleter.get_bracket_dates("2025-02-03")
        assert ffrom.year == 2025
        assert ffrom.month == 2
        assert ffrom.day == 3
        assert ffrom.hour == 0
        assert ffrom.minute == 0
        assert ffrom.second == 0

        assert tto.year == 2025
        assert tto.month == 2
        assert tto.day == 4
        assert tto.hour == 0
        assert tto.minute == 0
        assert tto.second == 0

        with pytest.raises(ValueError):
            DateCompleter.get_bracket_dates("2025-02-03 01")

        ffrom, tto = DateCompleter.get_bracket_dates("2025-02-03_")
        assert ffrom.year == 2025
        assert ffrom.month == 2
        assert ffrom.day == 3
        assert ffrom.hour == 0
        assert ffrom.minute == 0
        assert ffrom.second == 0

        assert tto.year == 2025
        assert tto.month == 2
        assert tto.day == 4
        assert tto.hour == 0
        assert tto.minute == 0
        assert tto.second == 0

        ffrom, tto = DateCompleter.get_bracket_dates("2025-02-03_02")
        assert ffrom.year == 2025
        assert ffrom.month == 2
        assert ffrom.day == 3
        assert ffrom.hour == 2
        assert ffrom.minute == 0
        assert ffrom.second == 0

        assert tto.year == 2025
        assert tto.month == 2
        assert tto.day == 3
        assert tto.hour == 3
        assert tto.minute == 0
        assert tto.second == 0

        with pytest.raises(ValueError):
            DateCompleter.get_bracket_dates("2025-02-03_02-9")

        ffrom, tto = DateCompleter.get_bracket_dates("2025-02-03_02-09")
        assert ffrom.year == 2025
        assert ffrom.month == 2
        assert ffrom.day == 3
        assert ffrom.hour == 2
        assert ffrom.minute == 9
        assert ffrom.second == 0

        assert tto.year == 2025
        assert tto.month == 2
        assert tto.day == 3
        assert tto.hour == 2
        assert tto.minute == 10
        assert tto.second == 0

        ffrom, tto = DateCompleter.get_bracket_dates("2025-02-03_02-09-03")
        assert ffrom.year == 2025
        assert ffrom.month == 2
        assert ffrom.day == 3
        assert ffrom.hour == 2
        assert ffrom.minute == 9
        assert ffrom.second == 3

        assert tto.year == 2025
        assert tto.month == 2
        assert tto.day == 3
        assert tto.hour == 2
        assert tto.minute == 9
        assert tto.second == 4

    def test_to_date(self):
        d = DateCompleter.to_date("2025-02-01_00-00-00")
        assert d is not None
        assert isinstance(d, datetime)
        assert d.year == 2025
        assert d.day == 1
        assert d.hour == 0

    def test_get_completed_date(self):
        d = DateCompleter.get("2025-02-")
        assert d == "2025-02-01_00-00-00"

    def test_smallest_unit(self):
        s = "2025-"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "year"

        s = "2025-02"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "month"

        s = "2025-0"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "month"

        s = "2025-02-"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "month"

        s = "2025-02-10"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "day"

        s = "2025-02-9"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "day"

        s = "2025-02-10_"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "day"

        s = "2025-02-10_1"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "hour"

        s = "2025-02-10_19"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "hour"

        s = "2025-02-10_01-"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "hour"

        s = "2025-02-10_01-4"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "minute"

        s = "2025-02-10_01-44"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "minute"

        s = "2025-02-10_01-44-"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "minute"

        s = "2025-02-10_01-04-1"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "second"

        s = "2025-02-10_01-04-17"
        unit = DateCompleter.smallest_unit(s)
        print(f"unit of {s}: {unit}")
        assert unit == "second"
