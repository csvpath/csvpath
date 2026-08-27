from datetime import timedelta

import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.yesterday_3 import Yesterday3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Yesterday3()
    assert f.name == "yesterday"
    assert f.ROLE == Function3.VALUE
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Yesterday3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Yesterday3(arg="x").check_valid()


def test_compute_matches_yesterdays_date_as_iso_string():
    expected = (daut.now() - timedelta(days=1)).date().isoformat()
    assert Yesterday3().compute() == expected
