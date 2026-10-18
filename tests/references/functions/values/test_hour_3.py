import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.hour_3 import Hour3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Hour3()
    assert f.name == "hour"
    # ROLE stays VALUE -- a first attempt changed this to
    # CONTEXT_SETTER and broke this function's own, pre-existing,
    # compendium-explicit VALUE usage in {...} interpolation (6.42).
    # The new bare-context-setter/anchor capability (compendium 6.27,
    # TimeWindowFunction3, added 2026-10-17) is detected structurally
    # instead -- see year_3.py's own comment for the full story.
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Hour3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Hour3(arg="x").check_valid()


def test_compute_matches_the_current_12_hour_clock():
    assert Hour3().compute() == int(daut.now().strftime("%I"))


class TestStartEndDatetime:
    # the window is always the real 24-hour current hour, regardless
    # of the 12-hour display value compute() returns.
    def test_start_is_top_of_the_current_hour(self):
        f = Hour3()
        start = f.start_datetime()
        now = daut.now()
        assert start == start.replace(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=0,
            second=0,
            microsecond=0,
        )

    def test_end_is_bottom_of_the_current_hour(self):
        f = Hour3()
        end = f.end_datetime()
        now = daut.now()
        assert end == end.replace(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=59,
            second=59,
            microsecond=999999,
        )
