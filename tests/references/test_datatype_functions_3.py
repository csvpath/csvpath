#
# every top-level function in a reference is one of its datatype's (its
# DATATYPES). FILES accepted ':having()', a CSVPATHS and RESULTS function,
# silently (reviewer on #761). query() raises before anything is read.
#
import pytest

from csvpath import CsvPaths
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3


@pytest.fixture(scope="module")
def csvpaths():
    return CsvPaths()


def _finder(reference: str, csvpaths):
    return ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=csvpaths)


def _check(reference: str, csvpaths) -> None:
    finder = _finder(reference, csvpaths)
    finder._check_datatype_functions(finder.ref.parsed)


@pytest.mark.parametrize(
    "reference, message",
    [
        # the reviewer's case: no dot, so no other check caught it
        (
            '$acme.files.:having(:type("csv")):last()',
            "':having()' is not a files function",
        ),
        ("$acme.files.:manifest():run_dir()", "':run_dir()' is not a files function"),
        ("$acme.csvpaths.:on_arrival()", "':on_arrival()' is not a csvpaths function"),
        (
            '$acme.csvpaths.:source_port("x")',
            "':source_port()' is not a csvpaths function",
        ),
        (
            "$acme.results.:last():on_arrival()",
            "':on_arrival()' is not a results function",
        ),
    ],
)
def test_a_function_of_another_datatype_raises(csvpaths, reference, message):
    with pytest.raises(ReferenceException3) as e:
        _check(reference, csvpaths)
    assert str(e.value) == message


@pytest.mark.parametrize(
    "reference",
    [
        '$acme.files.:name("orders.csv").:last():fingerprint()',
        "$acme.files.:flatten().:yesterday():last()",
        '$acme.csvpaths.:having(:uuid("a1")):last()',
        '$acme.results.:last().s:errors(:idchain("add[0]"))',
        # a function only ever nested in an argument is not checked here
        "$acme.results.:last():having(:errors(:count(:above(0))))",
    ],
)
def test_the_datatypes_own_functions_pass(csvpaths, reference):
    _check(reference, csvpaths)


def test_an_unknown_function_is_left_to_the_checks_that_name_it(csvpaths):
    # Reference3 and the finders say "Unknown reference function"
    _check("$acme.files.:nosuch()", csvpaths)


def test_top_level_calls_reads_every_chain(csvpaths):
    finder = _finder("$acme.results.:last():completed().s:valid(:true())", csvpaths)
    names = [c.name for c in finder._top_level_calls(finder.ref.parsed)]
    assert names == ["last", "completed", "valid"]


def test_top_level_calls_rejects_none(csvpaths):
    with pytest.raises(ValueError):
        _finder("$acme.results.:last()", csvpaths)._top_level_calls(None)
