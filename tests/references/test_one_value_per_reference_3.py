#
# a reference resolves to at most one value (compendium 5.20b; David,
# 2026-11-18). These pin the classification ReferenceFinder3._value_calls()
# makes, with no data at all: query() raises before anything is read. The
# finder tests pin the raise in each datatype's own shapes.
#
import pytest

from csvpath import CsvPaths
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.reference_results_3 import ReferenceResults3


@pytest.fixture(scope="module")
def csvpaths():
    return CsvPaths()


def _value_names(reference: str, csvpaths) -> list[str]:
    finder = ReferenceFinderFactory3.for_reference(
        reference=reference, csvpaths=csvpaths
    )
    return [call.name for call in finder._value_calls(finder.ref.parsed)]


def _check(reference: str, csvpaths) -> None:
    finder = ReferenceFinderFactory3.for_reference(
        reference=reference, csvpaths=csvpaths
    )
    finder._check_one_value(finder.ref.parsed)


# ===================
# what supplies a value
# ===================


@pytest.mark.parametrize(
    "reference, expected",
    [
        # an unargued field
        ("$acme.results.:last().s:valid()", ["valid"]),
        # a gate (an argued field) is a filter
        ('$orders.files.:all().:last():type("csv"):fingerprint()', ["fingerprint"]),
        # a key-selecting field reads a value: its argument names the key
        (
            '$acme.csvpaths.:definition():destination_port("email")',
            ["destination_port"],
        ),
        # a content accessor supplies its file's content
        ("$acme.results.:last().s:errors()", ["errors"]),
        # a chain head supplies no value of its own; the field reads from it
        ("$orders.files.:manifest():last():uuid()", ["uuid"]),
        ("$orders.files.:manifest()", []),
        # a predicate nested in an argument is not top-level
        ('$acme.results.:last().s:errors(:idchain("add[0]"))', ["errors"]),
        # a filter after a content accessor is a filter
        ('$acme.results.:last().s:errors():idchain("add[0]")', ["errors"]),
        # pointers, ranges and clock values supply none
        ("$acme.results.:from(0):to(2)", []),
        ("$acme.results.:today():last()", []),
        # a repeated field counts twice
        ("$orders.files.:all().:last():uuid():uuid()", ["uuid", "uuid"]),
        # chain heads never count: the ledger set and an instance manifest
        # are a legal pair (reviewer on #742)
        ("$acme.results.:manifest():last().t:manifest()", []),
        # a clock value is never the value: an illegal one keeps its own
        # "not legal" error (reviewer on #742)
        ("$acme.results.:last():completed():now()", ["completed"]),
        ("$acme.results.:last():completed():day_name()", ["completed"]),
        # name_one and name_three together
        ("$acme.results.:last():completed().*:valid()", ["completed", "valid"]),
    ],
)
def test_value_calls(csvpaths, reference, expected):
    assert _value_names(reference, csvpaths) == expected


def test_value_calls_rejects_none(csvpaths):
    finder = ReferenceFinderFactory3.for_reference(
        reference="$acme.results.:last()", csvpaths=csvpaths
    )
    with pytest.raises(ValueError):
        finder._value_calls(None)


# ===================
# the raise
# ===================


@pytest.mark.parametrize(
    "reference",
    [
        "$orders.files.:all().:last():fingerprint():template()",
        "$acme.results.:last().s:valid():completed()",
        '$acme.results.:last().s:errors(:idchain("add[0]")):error_count()',
        '$acme.csvpaths.:definition():destination_port("email"):destination_address("email")',
        "$acme.results.:last():completed().*:valid()",
    ],
)
def test_two_values_raise(csvpaths, reference):
    with pytest.raises(ReferenceException3, match="resolves to one value"):
        _check(reference, csvpaths)


@pytest.mark.parametrize(
    "reference",
    [
        "$orders.files.:all().:last():fingerprint()",
        '$orders.files.:all().:last():type("csv"):fingerprint()',
        "$orders.files.:manifest():last():uuid()",
        '$acme.results.:last().s:errors():idchain("add[0]")',
        "$acme.results.:last()",
    ],
)
def test_one_value_or_none_is_fine(csvpaths, reference):
    _check(reference, csvpaths)


def test_the_message_gives_each_single_value_spelling(csvpaths):
    with pytest.raises(ReferenceException3) as e:
        _check("$acme.results.:last().s:valid():completed()", csvpaths)
    message = str(e.value)
    assert ":valid(), :completed()" in message
    assert "$acme.results.:last().s:completed()" in message
    assert "$acme.results.:last().s:valid()" in message


def test_resolve_from_a_given_selection_checks_too(csvpaths):
    # resolve_from(ReferenceResults3) skips query(); it checks first, and
    # reads nothing (reviewer on #742)
    finder = ReferenceFinderFactory3.for_reference(
        reference="$acme.results.:last().s:valid():completed()", csvpaths=csvpaths
    )
    with pytest.raises(ReferenceException3, match="resolves to one value"):
        finder.resolve_from(ReferenceResults3(results=[]))
    with pytest.raises(ReferenceException3, match="resolves to one value"):
        finder.resolve_each(ReferenceResults3(results=[]))


def test_a_repeated_field_gives_one_spelling(csvpaths):
    with pytest.raises(ReferenceException3) as e:
        _check("$orders.files.:all().:last():uuid():uuid()", csvpaths)
    assert str(e.value).endswith("Keep one: $orders.files.:all().:last():uuid()")


# ===================
# Function3.filters_with()
# ===================


@pytest.mark.parametrize(
    "name, arg_present, expected",
    [
        # an argued manifest field filters
        ("type", True, True),
        # an unargued one is a value
        ("type", False, False),
        # a key-selecting definition field stays a value with an argument
        ("source_port", True, False),
        # a content accessor is never a field filter
        ("errors", True, False),
    ],
)
def test_filters_with(name, arg_present, expected):
    function_cls = ReferenceFunctionFactory.get_registered_class(name)
    arg = "x" if arg_present else None
    assert function_cls.filters_with(arg) is expected
