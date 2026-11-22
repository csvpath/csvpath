#
# CSVPATHS name_three wildcards and statement pointers (name_one gap
# review, item N). NRE: '$acme.csvpaths.:last().:all()' and '.*' "are
# equivalent", and '$acme.csvpaths.:last().:index(0)' is the statement at
# index 0. Each raised: ':all()'/':index()'/':first()'/':last()' were "not
# legal at name_three for csvpaths" and '*' needed "a literal statement
# identity/index". A pointer picks from a range when there is one (6.28).
#
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    CORPUS_CONFIG,
    _measure,
    _problems,
)

VERSION = "$validate_orders.csvpaths.:last()"


@pytest.fixture(scope="module")
def corpus():
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = os.path.abspath(CORPUS_CONFIG)
    try:
        yield CsvPaths()
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _identities(*, p, reference: str) -> list:
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    return [r.identity for r in finder.query().results]


def _all(p) -> list:
    return _identities(p=p, reference=f"{VERSION}.:from(0)")


def test_all_and_star_are_every_statement(corpus):
    every = _all(corpus)
    assert len(every) > 1
    assert _identities(p=corpus, reference=f"{VERSION}.:all()") == every
    assert _identities(p=corpus, reference=f"{VERSION}.*") == every


@pytest.mark.parametrize(
    "three,pick",
    [
        (".:index(0)", 0),
        (".:first()", 0),
        (".:index(-1)", -1),
        (".:last()", -1),
        (".:index(1)", 1),
    ],
)
def test_a_pointer_is_a_statement_by_position(corpus, three, pick):
    assert _identities(p=corpus, reference=f"{VERSION}{three}") == [_all(corpus)[pick]]


def test_a_pointer_picks_from_a_range(corpus):
    every = _all(corpus)
    assert _identities(p=corpus, reference=f"{VERSION}.:from(1):first()") == [every[1]]
    assert _identities(p=corpus, reference=f"{VERSION}.:to(1):last()") == [every[1]]


def test_an_index_past_the_end_is_nothing(corpus):
    assert _identities(p=corpus, reference=f"{VERSION}.:index(99)") == []


def test_a_star_root_is_one_statement_per_version(corpus):
    # one per selected version, as the literal roots give
    star = _identities(p=corpus, reference="$*.csvpaths.:last().:first()")
    literal = []
    for name in ("check_zipcodes", "scan_invoices", "validate_orders"):
        literal += _identities(p=corpus, reference=f"${name}.csvpaths.:last().:first()")
    assert star and sorted(star) == sorted(literal)


@pytest.mark.parametrize(
    "reference,message",
    [
        (f"{VERSION}.first_id:first()", "literal identity"),
        (f"{VERSION}.*:all()", "only one wildcard"),
        (f"{VERSION}.:first():last()", "one pointer"),
    ],
)
def test_combinations_that_still_raise(corpus, reference, message):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=corpus)
    with pytest.raises(ReferenceException3, match=message):
        finder.query()


@pytest.mark.parametrize(
    "reference",
    [
        f"{VERSION}.:all()",
        f"{VERSION}.*",
        f"{VERSION}.:index(0)",
        f"{VERSION}.:last()",
        f"{VERSION}.:from(1):first()",
        "$validate_orders.csvpaths.*.:first()",
        "$*.csvpaths.:last().:first()",
    ],
)
def test_the_estimate_keeps_its_contract(corpus, reference):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=corpus)
    measured, raised = _measure(corpus, reference)
    assert _problems(finder.estimate(), measured, raised) == []


# ===================
# a group with more statements than the estimate assumes (reviewer on #798)
# ===================

import configparser  # noqa: E402

SEP = "\n\n---- CSVPATH ----\n\n"


@pytest.fixture(scope="module")
def big(tmp_path_factory):
    # one named-paths group with 7 statements; a config file with no cache
    tmp = tmp_path_factory.mktemp("csvpaths_big_group")
    config = configparser.RawConfigParser()
    config.read(os.environ["CSVPATH_CONFIG_PATH"])
    path = tmp / "config.ini"
    for (section, key), value in {
        ("config", "path"): str(path),
        ("inputs", "files"): str(tmp / "named_files"),
        ("inputs", "csvpaths"): str(tmp / "named_paths"),
        ("results", "archive"): str(tmp / "archive"),
        ("listeners", "groups"): "",
        ("cache", "use_cache"): "no",
    }.items():
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, value)
    with open(path, "w", encoding="utf-8") as f:
        config.write(f)
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = str(path)
    try:
        p = CsvPaths()
        group = tmp / "big.csvpaths"
        group.write_text(
            SEP.join(f"~ id: s{n} ~ $[*][yes()]" for n in range(7)), encoding="utf-8"
        )
        p.paths_manager.add_named_paths_from_file(name="big", file_path=str(group))
        yield p
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


class TestABigGroup:
    def test_every_statement_in_declaration_order(self, big):
        assert _identities(p=big, reference="$big.csvpaths.:last().:all()") == [
            f"s{n}" for n in range(7)
        ]
        assert _identities(p=big, reference="$big.csvpaths.:last().:index(6)") == ["s6"]
        assert _identities(
            p=big, reference="$big.csvpaths.:last().:from(2):to(4):last()"
        ) == ["s4"]
        assert _identities(p=big, reference="$big.csvpaths.:last().:index(-8)") == []

    @pytest.mark.parametrize(
        "reference",
        [
            "$big.csvpaths.:last().:all()",
            "$big.csvpaths.:last().*",
            "$big.csvpaths.:last().:from(0)",
            "$*.csvpaths.:last().*",
            "$big.csvpaths.:last().:last()",
            "$big.csvpaths.:last().:index(6)",
        ],
    )
    def test_the_estimate_keeps_its_contract(self, big, reference):
        # every statement is an estimate (the ledger does not count them),
        # not a bound of 4 per version
        finder = ReferenceFinderFactory3.for_reference(
            reference=reference, csvpaths=big
        )
        measured, raised = _measure(big, reference)
        assert _problems(finder.estimate(), measured, raised) == []

    def test_a_pointer_resolves_to_its_statement(self, big):
        def data(reference):
            finder = ReferenceFinderFactory3.for_reference(
                reference=reference, csvpaths=big
            )
            return [r.data for r in finder.resolve_from(finder.query()).results]

        assert data("$big.csvpaths.:last().:index(3)") == data(
            "$big.csvpaths.:last().s3"
        )
        assert data("$big.csvpaths.:last().:last()") == data("$big.csvpaths.:last().s6")
