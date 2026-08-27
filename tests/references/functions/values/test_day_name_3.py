import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.day_name_3 import DayName3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = DayName3()
    assert f.name == "day_name"
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    DayName3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        DayName3(arg="x").check_valid()


def test_compute_matches_the_current_day_name():
    assert DayName3().compute() == daut.now().strftime("%A")
