import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import FunctionCall3, InterpolatedString3, Variable3
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

    def test_str_typed_arg_accepts_interpolated_string(self):
        # ARG_TYPES = (str,) is auto-widened to also accept
        # InterpolatedString3 -- a function that takes a plain string
        # must also accept one containing {...} interpolation.
        good = InterpolatedString3(parts=["x-", Variable3(name="company")])
        _OptionalStrArgFunction(arg=good).check_valid()  # should not raise

    def test_nested_interpolated_string_arg_is_recursively_checked(self):
        # the nested InterpolatedString3 contains a POINTER-role
        # function call, which is illegal inside {...} -- check_valid()
        # must recurse into it, not just check the outer arg's type.
        bad = InterpolatedString3(
            parts=["x-", FunctionCall3(name="first")]
        )
        with pytest.raises(ReferenceException3):
            _OptionalStrArgFunction(arg=bad).check_valid()

    def test_str_typed_arg_accepts_a_bare_variable(self):
        # added 2026-08-27 -- any function with a non-empty ARG_TYPES
        # also accepts a bare @variable, unconditionally (unlike the
        # str-gated InterpolatedString3 widening above) -- the resolved
        # value could be any type, checked later at resolve time, not
        # here.
        _OptionalStrArgFunction(arg=Variable3(name="company")).check_valid()

    def test_int_typed_arg_also_accepts_a_bare_variable(self):
        # proves the widening is unconditional, not just for str-typed
        # functions -- an int-only function accepts @var just as
        # readily.
        _RequiredIntArgFunction(arg=Variable3(name="n")).check_valid()

    def test_no_arg_function_still_rejects_a_bare_variable(self):
        # the Variable3 widening only applies once ARG_TYPES is
        # non-empty -- a function declaring it takes no argument at all
        # must still reject one, @variable included.
        with pytest.raises(ReferenceException3):
            _NoArgFunction(arg=Variable3(name="x")).check_valid()


class TestArgSetter:
    def test_arg_can_be_overwritten_after_construction(self):
        # added 2026-08-27 for ReferenceFinder3._resolve_arg()'s own
        # central, eager resolution -- a Variable3/InterpolatedString3
        # arg gets replaced in place with its real resolved value.
        f = _OptionalStrArgFunction(arg=Variable3(name="company"))
        f.arg = "acme"
        assert f.arg == "acme"


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
