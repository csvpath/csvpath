import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.values.year_3 import Year3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.util.date_util import DateUtility as daut


def test_metadata():
    f = Year3()
    assert f.name == "year"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (
        Reference3.FILES,
        Reference3.CSVPATHS,
        Reference3.RESULTS,
    )
    assert f.SOURCE == "clock"


def test_no_arg_is_valid():
    Year3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Year3(arg="x").check_valid()


def test_compute_matches_the_current_year():
    assert Year3().compute() == daut.now().year
