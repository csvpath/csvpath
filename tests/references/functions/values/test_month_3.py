import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.month_3 import Month3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Month3()
    assert f.name == "month"
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Month3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Month3(arg="x").check_valid()


def test_compute_matches_the_current_month():
    assert Month3().compute() == daut.now().month
