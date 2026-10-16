import pytest

from csvpath.references.functions.well_known_files.original_3 import Original3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Original3()
    assert f.name == "original"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.RESOLVES_AS == Reference3.METADATA_FILE


def test_no_arg_is_valid():
    Original3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Original3(arg="x").check_valid()
