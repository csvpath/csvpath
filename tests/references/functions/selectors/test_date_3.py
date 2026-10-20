from datetime import datetime

import pytest

from csvpath.references.functions.selectors.date_3 import Date3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Date3(arg="2025-01-01")
    assert f.name == "date"
    # ROLE stays VALUE -- a first attempt changed this to
    # CONTEXT_SETTER and broke this function's own, pre-existing,
    # compendium-explicit VALUE usage in {...} interpolation (6.42).
    # The new bare-context-setter/anchor capability (compendium 6.27,
    # TimeWindowFunction3, added 2026-10-17) is detected structurally
    # instead -- see year_3.py's own comment for the full story.
    assert f.ROLE == Function3.VALUE
    # DATATYPES widened from (RESULTS,) -- corrected 2026-10-17, FILES/
    # CSVPATHS already accepted a Date3-wrapped bound via From3/To3/
    # Before3/After3's own ARG_TYPES, this class's own DATATYPES was
    # just too narrow to match.
    assert f.DATATYPES == (
        Reference3.FILES,
        Reference3.CSVPATHS,
        Reference3.RESULTS,
    )


def test_str_arg_is_valid():
    Date3(arg="2025-01-01").check_valid()  # should not raise


def test_no_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Date3().check_valid()


def test_non_str_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Date3(arg=1).check_valid()


def test_malformed_date_string_is_rejected():
    # Function3's own generic ARG_TYPES check only confirms the arg IS
    # a str, not that its content is a real calendar date -- added
    # 2026-10-17 alongside start_datetime()/end_datetime(), which would
    # otherwise raise an unwrapped ValueError instead of failing
    # clearly at construction.
    with pytest.raises(ReferenceException3):
        Date3(arg="not-a-date").check_valid()


class TestStartEndDatetime:
    def test_start_is_midnight_of_the_named_date(self):
        f = Date3(arg="2025-01-31")
        assert f.start_datetime() == datetime(2025, 1, 31, 0, 0, 0, 0)

    def test_end_is_end_of_the_named_date(self):
        f = Date3(arg="2025-01-31")
        assert f.end_datetime() == datetime(2025, 1, 31, 23, 59, 59, 999999)


class TestOptionalTimeSuffix:
    # issue #409 -- David: the Framework's own run-dir timestamp form
    # "YYYY-MM-DD_HH-MM-SS" was always allowed, never required, as a
    # date-mode argument in v2 references; the v3 code never caught up
    # (:date() rejected it outright). The time portion narrows
    # granularity from the whole day down to the one named second --
    # it does not change anything about the date-only form.
    def test_date_with_time_is_valid(self):
        Date3(arg="2026-10-20_17-00-00").check_valid()  # should not raise

    def test_date_only_is_still_valid(self):
        Date3(arg="2026-10-20").check_valid()  # should not raise

    def test_malformed_time_suffix_is_still_rejected(self):
        # strptime happily accepts non-zero-padded fields (e.g.
        # "20-0-0" parses fine as 20:00:00) -- a genuinely invalid
        # value is needed to actually exercise the rejection.
        with pytest.raises(ReferenceException3):
            Date3(arg="2026-10-20_99-99-99").check_valid()

    def test_start_and_end_both_land_on_the_named_second(self):
        f = Date3(arg="2026-10-20_17-00-00")
        assert f.start_datetime() == datetime(2026, 10, 20, 17, 0, 0, 0)
        assert f.end_datetime() == datetime(2026, 10, 20, 17, 0, 0, 999999)

    def test_date_only_form_still_spans_the_whole_day(self):
        # confirms the time-suffix addition did not change the
        # existing day-granular behavior for the plain form.
        f = Date3(arg="2026-10-20")
        assert f.start_datetime() == datetime(2026, 10, 20, 0, 0, 0, 0)
        assert f.end_datetime() == datetime(2026, 10, 20, 23, 59, 59, 999999)
