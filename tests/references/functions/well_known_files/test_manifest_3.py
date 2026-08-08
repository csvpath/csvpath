import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.well_known_files.manifest_3 import Manifest3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Manifest3()
    assert f.name == "manifest"
    # VALUE, not POINTER -- :manifest() never narrows/selects anything,
    # even bare; it just accesses whatever's already in scope. See
    # manifest_3.py's own comment for why this was originally wrong.
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)


def test_no_arg_is_valid():
    Manifest3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Manifest3(arg="x").check_valid()
