import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.hour_24_3 import Hour243
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Hour243()
    assert f.name == "hour_24"
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Hour243().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Hour243(arg="x").check_valid()


def test_compute_matches_the_current_24_hour_clock():
    assert Hour243().compute() == daut.now().hour
