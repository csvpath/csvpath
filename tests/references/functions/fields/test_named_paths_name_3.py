import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_paths_name_3 import NamedPathsName3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedPathsName3()
    assert f.name == "named_paths_name"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS, Reference3.RESULTS)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.CSVPATHS: "named_paths_name",
        Reference3.RESULTS: "named_paths_name",
    }


def test_no_arg_is_valid():
    NamedPathsName3().check_valid()  # should not raise


class TestGateArgument:
    # ARG_TYPES widened 2026-10-18 from () -- compendium 6.7's "name"
    # functional group (:named_paths_name()/:named_results_name()/
    # :named_file_name()) shares the retrieve/select duality rule
    # :uuid() already has. A string argument GATES a pooled RESULTS
    # candidate list by this field (normative_reference_examples.txt's
    # own "$*.results.:manifest():named_paths_name(\"orders\"):
    # yesterday()"); not supported for CSVPATHS (see
    # CsvpathsReferenceFinder3's own guard -- redundant there).
    def test_string_arg_is_valid(self):
        NamedPathsName3(arg="orders").check_valid()  # should not raise

    def test_int_arg_is_rejected(self):
        with pytest.raises(ReferenceException3):
            NamedPathsName3(arg=1).check_valid()
