import calendar

import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.month_3 import Month3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Month3()
    assert f.name == "month"
    # ROLE stays VALUE -- a first attempt changed this to
    # CONTEXT_SETTER and broke this function's own, pre-existing,
    # compendium-explicit VALUE usage in {...} interpolation (6.42).
    # The new bare-context-setter/anchor capability (compendium 6.27,
    # TimeWindowFunction3, added 2026-10-17) is detected structurally
    # instead -- see year_3.py's own comment for the full story.
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Month3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Month3(arg="x").check_valid()


def test_compute_matches_the_current_month():
    assert Month3().compute() == daut.now().month


class TestStartEndDatetime:
    def test_start_is_first_of_month_midnight(self):
        f = Month3()
        start = f.start_datetime()
        now = daut.now()
        assert start == start.replace(
            year=now.year,
            month=now.month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    def test_end_is_last_day_of_month_end_of_day(self):
        f = Month3()
        end = f.end_datetime()
        now = daut.now()
        last_day = calendar.monthrange(now.year, now.month)[1]
        assert end == end.replace(
            year=now.year,
            month=now.month,
            day=last_day,
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )
