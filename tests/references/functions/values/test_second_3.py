import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.second_3 import Second3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Second3()
    assert f.name == "second"
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
