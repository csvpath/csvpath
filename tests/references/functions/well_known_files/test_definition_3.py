import pytest

from csvpath.references.functions.well_known_files.definition_3 import Definition3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Definition3()
    assert f.name == "definition"
    # VALUE, not POINTER -- :definition() never narrows/selects
    # anything, even bare; same reasoning as Manifest3's own role fix
    # (this one was missed in that earlier pass).
    assert f.ROLE == Function3.VALUE
    # unlike Manifest3, results has no definition.json equivalent.
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS)


def test_no_arg_is_valid():
    Definition3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Definition3(arg="x").check_valid()
