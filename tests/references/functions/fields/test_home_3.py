import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.home_3 import Home3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    # narrowed 2026-08-26 -- :home() keeps only the FILES/RESULTS
    # zero-level placeholder role; the old field-read job (SOURCE/KEY)
    # moved to :file_home()/:group_home()/:run_home()/:instance_home().
    f = Home3()
    assert f.name == "home"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES, Reference3.RESULTS)
    assert f.SOURCE is None
    assert f.KEY == {}
    assert f.POSITIONS == {
        Reference3.FILES: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }


def test_no_arg_is_valid():
    Home3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Home3(arg="x").check_valid()
