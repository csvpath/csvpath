import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.year_3 import Year3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Year3()
    assert f.name == "year"
    # ROLE stays VALUE -- a first attempt changed this to
    # CONTEXT_SETTER and broke this function's own, pre-existing,
    # compendium-explicit VALUE usage in {...} interpolation (6.42).
    # The new bare-context-setter/anchor capability (compendium 6.27,
    # TimeWindowFunction3, added 2026-10-17) is detected structurally
    # instead -- see year_3.py's own comment for the full story.
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (
        Reference3.FILES,
        Reference3.CSVPATHS,
        Reference3.RESULTS,
    )
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Year3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Year3(arg="x").check_valid()


def test_compute_matches_the_current_year():
    assert Year3().compute() == daut.now().year


class TestStartEndDatetime:
    # TimeWindowFunction3's own window -- the first/last moment of the
    # CURRENT year, added 2026-10-17.
    def test_start_is_january_first_midnight(self):
        f = Year3()
        start = f.start_datetime()
        now = daut.now()
        assert start == start.replace(
            year=now.year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )

    def test_end_is_december_31_end_of_day(self):
        f = Year3()
        end = f.end_datetime()
        now = daut.now()
        assert end == end.replace(
            year=now.year,
            month=12,
            day=31,
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )

    def test_start_and_end_are_naive(self):
        f = Year3()
        assert f.start_datetime().tzinfo is None
        assert f.end_datetime().tzinfo is None
