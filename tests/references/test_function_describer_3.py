from csvpath.references.function_describer_3 import Function3Describer
from csvpath.references.functions.fields.template_3 import Template3
from csvpath.references.functions.fields.uuid_3 import Uuid3
from csvpath.references.functions.filters.idchain_3 import Idchain3
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from csvpath.references.functions.selectors.having_3 import Having3
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

    def test_whole_resource_function_shows_resolves_as_metadata_file(self):
        # RESOLVES_AS override -- added 2026-08-28, replacing the old
        # hardcoded _METADATA_FILE_FUNCTIONS tuple.
        doc = Function3Describer.describe(Log3)
        assert "Resolves as" in doc
        assert "metadata_file" in doc

    def test_narrowing_function_with_no_source_still_shows_resolves_as_metadata_field(
        self,
    ):
        # Idchain3 has no SOURCE of its own -- its METADATA_FIELD
        # classification comes entirely from its own RESOLVES_AS
        # override, proving the row reflects metadata_kind()'s actual
        # answer, not just a raw SOURCE passthrough.
        doc = Function3Describer.describe(Idchain3)
        assert "Resolves as" in doc
        assert "metadata_field" in doc

    def test_ordinary_field_accessor_shows_resolves_as_metadata_field_via_source(self):
        # Uuid3 has no RESOLVES_AS override at all -- metadata_kind()
        # derives METADATA_FIELD purely from its SOURCE == "manifest".
        assert Uuid3.RESOLVES_AS is None
        doc = Function3Describer.describe(Uuid3)
        assert "Resolves as" in doc
        assert "metadata_field" in doc

    def test_non_metadata_function_has_no_resolves_as_row(self):
        # Having3 is a plain CONTEXT_SETTER with no SOURCE and no
        # RESOLVES_AS -- the row should not appear at all, same as
        # "having" never appeared in either old hardcoded tuple.
        doc = Function3Describer.describe(Having3)
        assert "Resolves as" not in doc


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
