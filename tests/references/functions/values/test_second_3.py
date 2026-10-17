import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.second_3 import Second3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Second3()
    assert f.name == "second"
    # ROLE stays VALUE -- a first attempt changed this to
    # CONTEXT_SETTER and broke this function's own, pre-existing,
    # compendium-explicit VALUE usage in {...} interpolation (6.42).
    # The new bare-context-setter/anchor capability (compendium 6.27,
    # TimeWindowFunction3, added 2026-10-17) is detected structurally
    # instead -- see year_3.py's own comment for the full story.
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Second3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Second3(arg="x").check_valid()


def test_compute_is_within_a_reasonable_window_of_now():
    # seconds tick during the test itself, so an exact equality check
    # (like every other clock function's own test) would be flaky --
    # a several-second window is generous enough to never legitimately
    # fail while still proving compute() reads a real clock, not a
    # constant.
    before = daut.now()
    computed = Second3().compute()
    after = daut.now()
    assert before.second <= computed <= after.second or (
        after.second < before.second  # minute rolled over mid-test
    )


class TestStartEndDatetime:
    # the finest granularity in the family -- start/end still span the
    # whole second (:00.000000 to :00.999999), not a true instant.
    # Microsecond-level ticking during the test makes an exact
    # equality check flaky -- bound by before/after the same way
    # compute()'s own test does.
    def test_start_and_end_span_the_same_second(self):
        before = daut.now().replace(tzinfo=None)
        f = Second3()
        start = f.start_datetime()
        end = f.end_datetime()
        after = daut.now().replace(tzinfo=None)
        assert start.microsecond == 0
        assert end.microsecond == 999999
        assert start.replace(microsecond=0) == end.replace(microsecond=0)
        assert before.replace(microsecond=0) <= start <= after.replace(
            microsecond=999999
        )
