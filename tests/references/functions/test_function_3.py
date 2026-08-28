import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import (
    FunctionCall3,
    InterpolatedString3,
    Reference3,
    Variable3,
)
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
            "resolves_as": None,
            "selector_when_argued": False,
        }

    def test_equality(self):
        assert _RequiredIntArgFunction(arg=1) == _RequiredIntArgFunction(arg=1)
        assert _RequiredIntArgFunction(arg=1) != _RequiredIntArgFunction(arg=2)
        assert _RequiredIntArgFunction(arg=1) != _NoArgFunction()


class _SourcedFunction(Function3):
    # mirrors an ordinary field accessor (e.g. Uuid3) -- SOURCE set,
    # no RESOLVES_AS override needed.
    NAME = "sourced"
    SUMMARY = "reads a manifest field"
    ROLE = Function3.VALUE
    DATATYPES = ("files",)
    SOURCE = "manifest"
    KEY = {"files": "some_key"}


class _ClockFunction(Function3):
    # mirrors a SOURCE == "clock" value function (e.g. Year3) -- must
    # NOT be treated as METADATA_FIELD despite having a non-None SOURCE.
    NAME = "clockish"
    SUMMARY = "a pure computed value"
    ROLE = Function3.VALUE
    DATATYPES = ("files",)
    SOURCE = "clock"


class _WholeResourceFunction(Function3):
    # mirrors a functions/well_known_files/ class (e.g. Errors3) --
    # explicit RESOLVES_AS override, no SOURCE at all.
    NAME = "wholeresource"
    SUMMARY = "reads a whole well-known file"
    ROLE = Function3.VALUE
    DATATYPES = ("files",)
    RESOLVES_AS = Reference3.METADATA_FILE


class _NarrowingFunction(Function3):
    # mirrors Idchain3 -- explicit RESOLVES_AS override to METADATA_FIELD,
    # despite having no SOURCE either.
    NAME = "narrows"
    SUMMARY = "narrows a parent's whole-resource read"
    ROLE = Function3.VALUE
    DATATYPES = ("files",)
    RESOLVES_AS = Reference3.METADATA_FIELD


class TestMetadataKind:
    # added 2026-08-28, replacing Reference3's old hardcoded
    # _METADATA_FILE_FUNCTIONS/_METADATA_FIELD_FUNCTIONS name tuples --
    # confirmed by direct inspection (not assumed) that this classmethod
    # reproduces both tuples' membership exactly, across all 124
    # functions registered at the time of the switch.
    def test_plain_function_with_neither_source_nor_override_is_none(self):
        assert _NoArgFunction.metadata_kind() is None

    def test_source_implies_metadata_field_with_no_override_needed(self):
        assert _SourcedFunction.metadata_kind() == Reference3.METADATA_FIELD

    def test_clock_source_is_excluded_despite_being_non_none(self):
        # a bare computed value (e.g. :year()) has no entity/manifest
        # context at all -- neither METADATA_FILE nor METADATA_FIELD.
        assert _ClockFunction.metadata_kind() is None

    def test_resolves_as_override_wins_for_whole_resource_functions(self):
        assert _WholeResourceFunction.metadata_kind() == Reference3.METADATA_FILE

    def test_resolves_as_override_works_with_no_source_at_all(self):
        assert _NarrowingFunction.metadata_kind() == Reference3.METADATA_FIELD


class TestSelectorWhenArgued:
    # added 2026-08-28 -- declarative replacement for
    # FilesReferenceFinder3's original bespoke
    # _is_bare_fingerprint_reference(). See ReferenceFinder3.
    # _is_bare_selector_reference() for the shared recognition helper
    # that reads this flag.
    def test_defaults_to_false(self):
        assert _NoArgFunction.SELECTOR_WHEN_ARGUED is False

    def test_can_be_declared_true(self):
        class _SelectorFunction(Function3):
            NAME = "selectorish"
            SUMMARY = "selects by a known field value when argued"
            ROLE = Function3.VALUE
            DATATYPES = ("files",)
            ARG_TYPES = (str,)
            ARG_REQUIRED = False
            SELECTOR_WHEN_ARGUED = True

        assert _SelectorFunction.SELECTOR_WHEN_ARGUED is True

    def test_surfaces_in_describe(self):
        f = _NoArgFunction()
        assert f.describe()["selector_when_argued"] is False
