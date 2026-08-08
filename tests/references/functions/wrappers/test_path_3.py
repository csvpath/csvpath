import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.well_known_files.manifest_3 import Manifest3
from csvpath.references.functions.wrappers.path_3 import Path3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Path3(arg=Manifest3())
    assert f.name == "path"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS)
    assert f.ARG_TYPES == (Function3,)
    assert f.ARG_REQUIRED is True


def test_wrapping_a_function_is_valid():
    Path3(arg=Manifest3()).check_valid()  # should not raise


def test_no_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Path3().check_valid()


def test_a_plain_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Path3(arg="manifest").check_valid()
