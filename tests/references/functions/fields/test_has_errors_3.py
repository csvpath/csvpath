import pytest

from csvpath.references.functions.fields.has_errors_3 import HasErrors3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = HasErrors3()
    assert f.name == "has_errors"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.RESULTS: "error_count",
        Reference3.RESULT: "error_count",
    }
    assert f.POSITIONS == {
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }


def test_no_arg_is_valid():
    HasErrors3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        HasErrors3(arg="x").check_valid()


class TestTransformValue:
    # mirrors csvpath.managers.results.result.Result.has_errors()
    # (`self.errors_count > 0`) -- reduces the raw "error_count" int to
    # a bool.
    def test_positive_count_is_true(self):
        assert HasErrors3.transform_value(3) is True

    def test_zero_is_false(self):
        assert HasErrors3.transform_value(0) is False

    def test_missing_value_is_false(self):
        # genuinely optional, same treatment every other well-known
        # manifest field gets -- missing is not an error.
        assert HasErrors3.transform_value(None) is False

    def test_non_int_value_is_false(self):
        assert HasErrors3.transform_value("not-a-count") is False
