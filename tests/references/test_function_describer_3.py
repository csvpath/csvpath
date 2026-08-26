from csvpath.references.function_describer_3 import Function3Describer
from csvpath.references.functions.fields.template_3 import Template3
from csvpath.references.functions.filters.idchain_3 import Idchain3
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from csvpath.references.functions.values.year_3 import Year3
from csvpath.references.functions.well_known_files.log_3 import Log3


class TestDescribeOneFunction:
    # compendium 5.4: reference functions must be self-documenting,
    # able to output markdown. Function3.describe() (unchanged by this)
    # is the machine-readable half; this is the human-readable half.
    def test_includes_name_and_summary(self):
        doc = Function3Describer.describe(Year3)
        assert "## year" in doc
        assert Year3.SUMMARY in doc

    def test_includes_role_and_datatypes(self):
        doc = Function3Describer.describe(Year3)
        assert "value" in doc
        assert "files" in doc and "csvpaths" in doc and "results" in doc

    def test_no_arg_function_says_argument_none(self):
        doc = Function3Describer.describe(Year3)
        assert "none" in doc.lower()

    def test_required_arg_function_shows_type_and_required(self):
        doc = Function3Describer.describe(Idchain3)
        assert "required" in doc
        assert "Regex3" in doc

    def test_field_accessor_shows_source_and_key(self):
        doc = Function3Describer.describe(Template3)
        assert "manifest" in doc
        assert "template" in doc

    def test_bare_source_function_shows_bare_source(self):
        doc = Function3Describer.describe(Template3)
        assert "definition" in doc

    def test_clock_function_shows_source_clock(self):
        doc = Function3Describer.describe(Year3)
        assert "clock" in doc

    def test_positions_are_rendered_when_declared(self):
        doc = Function3Describer.describe(Template3)
        assert "name_one" in doc


class TestDescribeAll:
    def test_includes_every_registered_function_in_the_index(self):
        doc = Function3Describer.describe_all()
        for name in ReferenceFunctionFactory.registered_names():
            assert f"#{name}" in doc

    def test_includes_a_full_block_for_a_spot_checked_function(self):
        doc = Function3Describer.describe_all()
        assert "## log" in doc
        assert Log3.SUMMARY in doc

    def test_index_and_blocks_agree_on_function_count(self):
        doc = Function3Describer.describe_all()
        names = ReferenceFunctionFactory.registered_names()
        for name in names:
            assert doc.count(f"## {name}\n") == 1
