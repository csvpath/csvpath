#
# ':file()' and ':printouts()' read a file in a run instance's directory, so
# their argument must be a bare file name. Until 2026-11-21 only a literal
# ':file()' argument was checked: ':file(@f)' with '/etc/hosts' read and
# returned that file, '../..' paths walked out of the archive, and
# ':printouts()' was never checked at all (found by the reviewer on #790,
# confirmed live). BareNameUtility checks the literal when the function is
# built, a resolved value when it resolves, and the name again where it
# meets the file system.
#
import os

import pytest

from csvpath.references.functions.well_known_files.bare_name_utility import (
    BareNameUtility as baut,
)
from csvpath.references.functions.well_known_files.file_3 import File3
from csvpath.references.functions.well_known_files.printouts_3 import Printouts3
from csvpath.references.reference_exceptions_3 import (
    ReferenceException3,
    ReferenceRuntimeException3,
)
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.results_reference_finder_3 import ResultsReferenceFinder3
from tests.references.test_results_wildcard_paths_3 import runs  # noqa: F401

PATHS = [
    "../manifest.json",
    "../../../../named_files/alpha/manifest.json",
    "/etc/hosts",
    "sub/x.txt",
    "sub\\x.txt",
    "C:secret.txt",
    "x\x00.txt",
    "..",
    "",
    "   ",
]


class TestBareNameUtility:
    @pytest.mark.parametrize(
        "name", ["vars.json", "orders.parquet", "greetings", "a b.txt"]
    )
    def test_a_bare_name_passes(self, name):
        assert baut.problem(name) is None
        baut.check(function_name="file", name=name)

    @pytest.mark.parametrize("name", PATHS)
    def test_a_path_or_empty_name_raises(self, name):
        assert baut.problem(name) is not None
        with pytest.raises(ReferenceException3, match="run instance's directory"):
            baut.check(function_name="file", name=name)

    def test_a_non_string_raises(self):
        with pytest.raises(ReferenceException3, match="must be a string"):
            baut.check(function_name="file", name=3)

    def test_the_function_name_is_required(self):
        with pytest.raises(ValueError):
            baut.check(function_name="", name="x")


class TestFunctions:
    @pytest.mark.parametrize("cls", [File3, Printouts3])
    @pytest.mark.parametrize("name", [p for p in PATHS if p.strip()])
    def test_a_literal_path_raises_when_built(self, cls, name):
        with pytest.raises(ReferenceException3, match="bare file name|cannot be empty"):
            cls(arg=name).check_valid()

    @pytest.mark.parametrize("cls", [File3, Printouts3])
    def test_a_resolved_path_raises(self, cls):
        f = cls(arg="ok.txt")
        f.check_valid()
        f.arg = "../../x.txt"
        with pytest.raises(ReferenceException3, match="bare file name"):
            f.check_resolved()

    def test_printouts_with_no_name_is_still_the_default(self):
        Printouts3().check_valid()


class TestTheJoinIsGuarded:
    # checked again where the name meets the file system, whatever route
    # the argument took
    @pytest.mark.parametrize("cls", [File3, Printouts3])
    def test_accessor_file_path(self, cls):
        accessor = cls(arg="ok")
        accessor.arg = "../x"
        with pytest.raises(ReferenceException3, match="bare file name"):
            ResultsReferenceFinder3._accessor_file_path(
                instance_dir="/tmp/instance", accessor=accessor
            )


class TestThroughAReference:
    @pytest.fixture
    def outside(self, tmp_path):
        secret = tmp_path / "secret.txt"
        secret.write_text("do not read", encoding="utf-8")
        return str(secret)

    def _finder(self, runs, reference, value):  # noqa: F811
        p, _ = runs
        finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
        if value is not None:
            finder.set_variable("f", value=value)
        return finder

    @pytest.mark.parametrize(
        "reference",
        [
            "$acme.results.:last().first_id:file(@f)",
            '$acme.results.:last().first_id:file("{@f}")',
            "$acme.results.:last().first_id:printouts(@f)",
        ],
    )
    def test_an_absolute_path_is_never_read(self, runs, reference, outside):  # noqa: F811
        finder = self._finder(runs, reference, outside)
        with pytest.raises(ReferenceRuntimeException3, match="bare file name"):
            finder.resolve_from(finder.query())

    @pytest.mark.parametrize(
        "value", ["../manifest.json", "../../../../named_files/orders/manifest.json"]
    )
    def test_a_parent_path_is_never_read(self, runs, value):  # noqa: F811
        finder = self._finder(runs, "$acme.results.:last().first_id:file(@f)", value)
        with pytest.raises(ReferenceRuntimeException3, match="bare file name"):
            finder.query()

    def test_a_literal_printouts_path_raises(self, runs):  # noqa: F811
        with pytest.raises(ReferenceException3, match="bare file name"):
            self._finder(
                runs, '$acme.results.:last().first_id:printouts("../x")', None
            ).query()

    def test_a_bare_name_still_reads(self, runs):  # noqa: F811
        finder = self._finder(
            runs, "$acme.results.:last().first_id:file(@f)", "vars.json"
        )
        data = finder.resolve_from(finder.query()).results[0].data
        assert data is not None
        assert os.path.basename(finder.query().results[0].path) != "secret.txt"
