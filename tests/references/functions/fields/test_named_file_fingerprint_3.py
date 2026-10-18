import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_file_fingerprint_3 import (
    NamedFileFingerprint3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedFileFingerprint3()
    assert f.name == "named_file_fingerprint"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULTS: "named_file_fingerprint"}


def test_no_arg_is_valid():
    NamedFileFingerprint3().check_valid()  # should not raise


class TestGateArgument:
    # ARG_TYPES widened 2026-10-18 from () -- normative_reference_
    # examples.txt's own worked example ("select all runs that used a
    # specific version of a named-file": "$*.results.:flatten():
    # named_file_fingerprint(\"4fd50acf...\")") needs a string argument
    # to GATE a pooled RESULTS candidate list by this field.
    def test_string_arg_is_valid(self):
        NamedFileFingerprint3(arg="4fd50acf").check_valid()  # should not raise

    def test_int_arg_is_rejected(self):
        with pytest.raises(ReferenceException3):
            NamedFileFingerprint3(arg=1).check_valid()
