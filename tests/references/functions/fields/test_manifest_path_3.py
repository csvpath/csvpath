import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.manifest_path_3 import ManifestPath3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = ManifestPath3()
    assert f.name == "manifest_path"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS, Reference3.RESULTS)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.CSVPATHS: "manifest_path",
        Reference3.RESULTS: "manifest_path",
        Reference3.RESULT: "manifest_path",
    }


def test_no_arg_is_valid():
    ManifestPath3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        ManifestPath3(arg="x").check_valid()
