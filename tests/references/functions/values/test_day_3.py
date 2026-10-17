import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.day_3 import Day3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Day3()
    assert f.name == "day"
    # ROLE stays VALUE -- a first attempt changed this to
    # CONTEXT_SETTER and broke this function's own, pre-existing,
    # compendium-explicit VALUE usage in {...} interpolation (6.42).
    # The new bare-context-setter/anchor capability (compendium 6.27,
    # TimeWindowFunction3, added 2026-10-17) is detected structurally
    # instead -- see year_3.py's own comment for the full story.
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Day3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Day3(arg="x").check_valid()


def test_compute_matches_the_current_day():
    assert Day3().compute() == daut.now().day


class TestStartEndDatetime:
    # same window as Today3's own -- :day() is "the current day,"
    # extrapolated from :year()/:month() meaning "the current period
    # at that granularity."
    def test_start_is_midnight_today(self):
        f = Day3()
        start = f.start_datetime()
        now = daut.now()
        assert start == start.replace(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    def test_end_is_end_of_today(self):
        f = Day3()
        end = f.end_datetime()
        now = daut.now()
        assert end == end.replace(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )
