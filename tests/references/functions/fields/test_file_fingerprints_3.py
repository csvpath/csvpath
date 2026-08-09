import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.file_fingerprints_3 import (
    FileFingerprints3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = FileFingerprints3()
    assert f.name == "file_fingerprints"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULT: "file_fingerprints"}


def test_no_arg_is_valid():
    FileFingerprints3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        FileFingerprints3(arg="x").check_valid()
