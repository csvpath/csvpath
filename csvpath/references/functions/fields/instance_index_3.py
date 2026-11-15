from ...reference_3 import Reference3
from ..function_3 import Function3
from ...reference_exceptions_3 import ReferenceException3
from ..filters.predicate_function_3 import PredicateFunction3


class InstanceIndex3(Function3):
    #
    # Result Instance Manifest (table 6)'s own "instance_index" -- the
    # 0-based index of this csvpath statement within the named-paths
    # group, distinct from Identity3/:identity() (the statement's own
    # name, or that same index stringified when unnamed).
    #
    NAME = "instance_index"
    SUMMARY = "The 0-based index of the resolved csvpath-statement instance within its named-paths group."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    ARG_TYPES = (int, PredicateFunction3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "instance_index",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}

    @classmethod
    def transform_value(cls, value):
        """the stored index as an int. The framework writes it as a string
        (Result.run_index = f"{run_index}"), so ':instance_index(1)' never
        matched and ':instance_index(:above(1))' raised a TypeError
        (reviewer on #659); the run-dir ordering already reads it as an int
        (_list_instance_identities()). A missing index stays None; a value
        that is not a whole number raises (decision D23)."""
        if value is None or isinstance(value, bool):
            return None if value is None else cls._not_an_index(value)
        if isinstance(value, int):
            return value
        try:
            return int(str(value))
        except ValueError:
            return cls._not_an_index(value)

    @classmethod
    def _not_an_index(cls, value):
        raise ReferenceException3(
            f"instance_index {value!r} is not a whole number, so it cannot be "
            "read as a statement's index."
        )
