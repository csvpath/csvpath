from csvpath.references.reference_exceptions_3 import (
    ReferenceException3,
    ReferenceRuntimeException3,
)


class TestReferenceRuntimeException3:
    # added 2026-08-27, David: "we just use a different exception that
    # indicates a 'runtime' error, as opposed to a static analysis
    # error" -- mirrors the matching language's own Args.validate()/
    # Args.matches() (ChildrenException/MatchException) split.
    def test_is_a_subclass_of_reference_exception_3(self):
        # a subclass, not a sibling, so every existing broad
        # `except ReferenceException3` keeps working unchanged.
        assert issubclass(ReferenceRuntimeException3, ReferenceException3)

    def test_can_be_raised_and_caught_as_the_broader_type(self):
        try:
            raise ReferenceRuntimeException3("runtime problem")
        except ReferenceException3 as e:
            assert isinstance(e, ReferenceRuntimeException3)
