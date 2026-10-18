from datetime import timedelta

import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.yesterday_3 import Yesterday3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Yesterday3()
    assert f.name == "yesterday"
    # ROLE stays VALUE -- a first attempt changed this to
    # CONTEXT_SETTER and broke this function's own, pre-existing,
    # compendium-explicit VALUE usage in {...} interpolation (6.42).
    # The new bare-context-setter/anchor capability (compendium 6.27,
    # TimeWindowFunction3, added 2026-10-17) is detected structurally
    # instead -- see year_3.py's own comment for the full story.
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Yesterday3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Yesterday3(arg="x").check_valid()


def test_compute_matches_yesterdays_date_as_iso_string():
    expected = (daut.now() - timedelta(days=1)).date().isoformat()
    assert Yesterday3().compute() == expected


class TestStartEndDatetime:
    # compendium 6.27f's own confirmed example: "the first moment of
    # the prior day to the last moment of the prior day."
    def test_start_is_midnight_yesterday(self):
        f = Yesterday3()
        start = f.start_datetime()
        yesterday = daut.now() - timedelta(days=1)
        assert start == start.replace(
            year=yesterday.year,
            month=yesterday.month,
            day=yesterday.day,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    def test_end_is_end_of_yesterday(self):
        f = Yesterday3()
        end = f.end_datetime()
        yesterday = daut.now() - timedelta(days=1)
        assert end == end.replace(
            year=yesterday.year,
            month=yesterday.month,
            day=yesterday.day,
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )
