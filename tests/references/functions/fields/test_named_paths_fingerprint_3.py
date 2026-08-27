import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_paths_fingerprint_3 import (
    NamedPathsFingerprint3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedPathsFingerprint3()
    assert f.name == "named_paths_fingerprint"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KIND == "fingerprint"
    assert f.KEY == {Reference3.RESULTS: "named_paths_fingerprint"}


def test_no_arg_is_valid():
    NamedPathsFingerprint3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        NamedPathsFingerprint3(arg="x").check_valid()
