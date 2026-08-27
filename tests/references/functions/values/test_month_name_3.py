import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.month_name_3 import MonthName3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = MonthName3()
    assert f.name == "month_name"
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    MonthName3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        MonthName3(arg="x").check_valid()


def test_compute_matches_the_current_month_name():
    assert MonthName3().compute() == daut.now().strftime("%B")
