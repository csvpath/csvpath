import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.day_3 import Day3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Day3()
    assert f.name == "day"
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Day3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Day3(arg="x").check_valid()


def test_compute_matches_the_current_day():
    assert Day3().compute() == daut.now().day
