import pytest
from datetime import datetime

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.now_3 import Now3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Now3()
    assert f.name == "now"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (
        Reference3.FILES,
        Reference3.CSVPATHS,
        Reference3.RESULTS,
    )
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Now3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Now3(arg="x").check_valid()


def test_compute_returns_a_datetime_close_to_now():
    result = Now3().compute()
    assert isinstance(result, datetime)
    assert abs((result - daut.now()).total_seconds()) < 5
