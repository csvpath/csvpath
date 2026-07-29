import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_exceptions_3 import ReferenceException3


class _NoArgFunction(Function3):
    NAME = "noarg"
    SUMMARY = "takes nothing"
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = ("files",)
    ARG_TYPES = ()
    ARG_REQUIRED = False


class _RequiredIntArgFunction(Function3):
    NAME = "needsint"
    SUMMARY = "takes a required int"
    ROLE = Function3.POINTER
    DATATYPES = ("files",)
    ARG_TYPES = (int,)
    ARG_REQUIRED = True


class _OptionalStrArgFunction(Function3):
    NAME = "optstr"
    SUMMARY = "takes an optional str"
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = ("files",)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False


class TestCheckValid:
    def test_no_arg_function_accepts_no_arg(self):
        _NoArgFunction().check_valid()  # should not raise

    def test_no_arg_function_rejects_any_arg(self):
        with pytest.raises(ReferenceException3):
            _NoArgFunction(arg="x").check_valid()

    def test_required_arg_missing_raises(self):
        with pytest.raises(ReferenceException3):
            _RequiredIntArgFunction().check_valid()

    def test_required_arg_present_and_correct_type_passes(self):
        _RequiredIntArgFunction(arg=5).check_valid()  # should not raise

    def test_wrong_arg_type_raises(self):
        with pytest.raises(ReferenceException3):
            _RequiredIntArgFunction(arg="not an int").check_valid()

    def test_optional_arg_absent_passes(self):
        _OptionalStrArgFunction().check_valid()  # should not raise

    def test_optional_arg_present_and_correct_type_passes(self):
        _OptionalStrArgFunction(arg="ok").check_valid()  # should not raise

    def test_nested_function3_arg_is_recursively_checked(self):
        class _AcceptsFunctionArg(Function3):
            NAME = "wraps"
            SUMMARY = "takes a nested function"
            ROLE = Function3.CONTEXT_SETTER
            DATATYPES = ("files",)
            ARG_TYPES = (Function3,)
            ARG_REQUIRED = False

        bad_nested = _RequiredIntArgFunction()  # missing its own required arg
        with pytest.raises(ReferenceException3):
            _AcceptsFunctionArg(arg=bad_nested).check_valid()


class TestProperties:
    def test_name_and_arg(self):
        f = _RequiredIntArgFunction(arg=7)
        assert f.name == "needsint"
        assert f.arg == 7

    def test_describe(self):
        f = _NoArgFunction()
        assert f.describe() == {
            "name": "noarg",
            "summary": "takes nothing",
            "role": Function3.CONTEXT_SETTER,
            "datatypes": ("files",),
        }

    def test_equality(self):
        assert _RequiredIntArgFunction(arg=1) == _RequiredIntArgFunction(arg=1)
        assert _RequiredIntArgFunction(arg=1) != _RequiredIntArgFunction(arg=2)
        assert _RequiredIntArgFunction(arg=1) != _NoArgFunction()
