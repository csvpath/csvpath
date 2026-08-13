import pytest

from csvpath.references.functions.fields.fingerprint_3 import Fingerprint3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Fingerprint3()
    assert f.name == "fingerprint"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.FILES: "fingerprint",
        Reference3.CSVPATHS: "fingerprint",
    }


def test_no_arg_is_valid():
    Fingerprint3().check_valid()  # should not raise


def test_str_arg_is_valid():
    # settled 2026-08-13: an optional str arg supports the bare-lookup
    # shape for FILES ("$alpha.files.:fingerprint('hash...')") -- see
    # FilesReferenceFinder3._is_bare_fingerprint_reference/query().
    Fingerprint3(arg="x").check_valid()  # should not raise


def test_non_str_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Fingerprint3(arg=1).check_valid()
