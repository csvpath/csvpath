#
# the wildcard combinations the spec rules out (compendium 4.2b, 4.3b,
# 4.3d; NRE 421-440 and 479-499), checked by ReferenceFinder3.
# _check_wildcards() in every datatype before anything is read. Each was
# accepted silently, or raised "does not yet support", until the name_one
# gap review (2026-11-19). These need no data: query() raises first, and
# a plain CsvPaths with no named-files is enough.
#
import pytest

from csvpath import CsvPaths
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.reference_finder_3 import ReferenceFinder3
from csvpath.references.reference_parser_3 import ReferenceParser3


@pytest.fixture(scope="module")
def csvpaths():
    return CsvPaths()


def _parsed(reference: str, csvpaths):
    return ReferenceParser3(string=reference, csvpaths=csvpaths).parsed


# ===================
# name_one: one grouping wildcard
# ===================


@pytest.mark.parametrize(
    "reference",
    [
        # two in one chain: accepted before, in RESULTS and CSVPATHS
        "$acme.results.:all():all()",
        "$acme.csvpaths.:all():all()",
        "$acme.results.:groups():all()",
        # as path segments (4.3b, NRE 425-427): raised "does not yet
        # support", which read as a promise
        "$acme.files.:all()/:all()",
        "$acme.files.:groups()/:all()",
        "$acme.files.:groups()/:groups()",
        "$acme.results.:all()/:groups()",
        "$acme.results.:groups()/:all()",
        # 4.5's last two examples; the 4.3b rule wins
        "$acme.files.:all()/*/:all()",
        "$acme.files.:all()/:all()/:all()",
    ],
)
def test_name_one_has_one_grouping_wildcard(reference, csvpaths):
    with pytest.raises(ReferenceException3, match="only one grouping wildcard"):
        ReferenceFinder3._check_wildcards(_parsed(reference, csvpaths))


# ===================
# name_one: nothing after :flatten() is a '*'
# ===================


@pytest.mark.parametrize(
    "reference",
    [
        # 4.3d, 4.5, NRE 435/466: illegal; FILES accepted it
        "$acme.files.:flatten()/*",
        "$acme.results.:flatten()/*",
        "$acme.files.:flatten()/*/:name(\"orders.csv\")",
        "$acme.files.2025/:flatten()/*",
    ],
)
def test_no_star_directly_after_flatten(reference, csvpaths):
    with pytest.raises(ReferenceException3, match="after ':flatten\\(\\)' is not legal"):
        ReferenceFinder3._check_wildcards(_parsed(reference, csvpaths))


@pytest.mark.parametrize(
    "reference",
    [
        # accepted in RESULTS; FILES raised "does not yet support"
        "$acme.results.:flatten():flatten()",
        "$acme.files.:flatten()/:flatten()",
        "$acme.results.:flatten()/:flatten()",
    ],
)
def test_one_flatten(reference, csvpaths):
    with pytest.raises(ReferenceException3, match="only one ':flatten\\(\\)'"):
        ReferenceFinder3._check_wildcards(_parsed(reference, csvpaths))


@pytest.mark.parametrize(
    "reference",
    [
        # NRE 476-477, 4.2b, 4.3e: the finders raised, the estimator did not
        "$acme.results.:last().:groups()",
        "$acme.results.:last().:groups():manifest()",
        "$acme.files.*.:flatten()",
        "$acme.csvpaths.:last().:groups()",
    ],
)
def test_no_deep_wildcard_in_name_three(reference, csvpaths):
    with pytest.raises(ReferenceException3, match="name_one wildcard only"):
        ReferenceFinder3._check_wildcards(_parsed(reference, csvpaths))


# ===================
# name_three: one wildcard
# ===================


@pytest.mark.parametrize(
    "reference",
    [
        # NRE 497-498, 4.2b: accepted before
        "$acme.files.*.:all():all()",
        "$acme.results.:last().:all():all()",
        # raised before, with other messages
        "$acme.files.*.*:all()",
        "$acme.results.:last().*:all()",
        "$acme.csvpaths.:last().*:all()",
    ],
)
def test_name_three_has_one_wildcard(reference, csvpaths):
    with pytest.raises(ReferenceException3, match="name_three can have only one wildcard"):
        ReferenceFinder3._check_wildcards(_parsed(reference, csvpaths))


# ===================
# legal combinations pass
# ===================


@pytest.mark.parametrize(
    "reference",
    [
        "$acme.files.:all()",
        "$acme.files.:groups().:last()",
        "$acme.files.:flatten().:all()",
        "$acme.files.:groups().:all()",
        "$acme.files.:flatten()",
        "$acme.files.*/:flatten()",
        '$acme.files.:flatten()/:name("orders.csv")',
        "$acme.files.*/*/*",
        "$acme.files.*/:groups()",
        "$acme.files.:flatten()/:all()",
        "$acme.files.*/:all()/*",
        # a literal between ':flatten()' and the '*' removes the ambiguity
        # (reviewer on #785: this worked before and must still)
        "$acme.files.:flatten()/2026/*",
        "$acme.files.:flatten()/orders/*/:name(\"four.csv\")",
        # not settled by the spec; passes (decision log)
        "$acme.files.:flatten()/:all()/*",
        "$acme.results.:all()/*:last()",
        "$acme.results.:last().:all()",
        "$acme.results.:last().*",
        "$acme.csvpaths.:all():last()",
        # an ':all()' nested in an argument is not a wildcard of the chain
        '$acme.results.:last().:all():having(:errors(:idchain("add[0]")))',
    ],
)
def test_legal_combinations_pass(reference, csvpaths):
    ReferenceFinder3._check_wildcards(_parsed(reference, csvpaths))


def test_a_none_reference_raises():
    with pytest.raises(ValueError):
        ReferenceFinder3._check_wildcards(None)


# ===================
# each finder runs it before reading
# ===================


@pytest.mark.parametrize(
    "reference",
    [
        "$acme.files.:flatten()/*",
        "$acme.files.*.:all():all()",
        "$acme.csvpaths.:all():all()",
        "$acme.results.:all():all()",
        "$acme.results.:last().:all():all()",
        # under a traversal root too
        "$*.files.:flatten()/*",
        "$*.results.:all():all()",
        "$*.csvpaths.:all():all()",
    ],
)
def test_every_finder_raises_before_reading(reference, csvpaths):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=csvpaths)
    with pytest.raises(ReferenceException3, match="wildcard|after ':flatten"):
        finder.query()
