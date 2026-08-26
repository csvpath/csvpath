import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.today_3 import Today3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Today3()
    assert f.name == "today"
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Today3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Today3(arg="x").check_valid()


def test_compute_matches_todays_date_as_iso_string():
    assert Today3().compute() == daut.now().date().isoformat()
