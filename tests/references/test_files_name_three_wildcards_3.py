#
# FILES name_three wildcards (name_one gap review, items M and O):
# - '.*' is '.:all()' (NRE: '$acme.files.:name("orders.csv").*' and
#   '.:all()' "are equivalent"; compendium 4.2b). It raised "a literal
#   name_three body of this type".
# - under a '$*' root a lone '.:all()' is every version (4.4:
#   '$*.files.:flatten().:all()' is "all 8 most-recent registrations"). It
#   raised "requires name_three to resolve to exactly one pointer".
#
import pytest

from csvpath.references.reference_3 import FunctionCall3, NameThree3, Star3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import LAYOUT, layout  # noqa: F401


def _query(*, p, reference: str) -> list:
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    return [(str(r.path), r.uuid) for r in finder.query().results]


class TestStarBodyAsAll:
    def test_a_star_body_becomes_all(self):
        three = NameThree3(body=Star3())
        three.star_body_as_all()
        assert three.body is None and [f.name for f in three.functions] == ["all"]

    def test_other_bodies_are_left_alone(self):
        three = NameThree3(body="abc", functions=[FunctionCall3(name="uuid")])
        three.star_body_as_all()
        assert three.body == "abc" and [f.name for f in three.functions] == ["uuid"]


EQUIVALENT = [
    # NRE 485
    ('$alpha.files.:name("one.csv").*', '$alpha.files.:name("one.csv").:all()'),
    ("$alpha.files.*.*", "$alpha.files.*.:all()"),
    ("$acme.files.:flatten().*", "$acme.files.:flatten().:all()"),
    ("$beta.files.:all()/*.*", "$beta.files.:all()/*.:all()"),
    # compendium 4.4: all four are every registration
    ("$*.files.:flatten().*", "$*.files.:flatten().:all()"),
    ("$*.files.:groups().*", "$*.files.:groups().:all()"),
    ("$*.files.:flatten().*", "$*.files.:groups().*"),
]


@pytest.mark.parametrize("star,all_form", EQUIVALENT)
def test_star_and_all_are_the_same(layout, star, all_form):  # noqa: F811
    p, _ = layout
    got = _query(p=p, reference=star)
    assert got and sorted(got) == sorted(_query(p=p, reference=all_form))


def test_star_flatten_all_is_every_registration(layout):  # noqa: F811
    # 4.4: "all ... registrations"
    p, _ = layout
    versions = sum(n for _, _, _, n in LAYOUT)
    assert len(_query(p=p, reference="$*.files.:flatten().:all()")) == versions


def test_two_wildcards_in_name_three_still_raise(layout):  # noqa: F811
    # 4.2b, NRE 497
    p, _ = layout
    finder = ReferenceFinderFactory3.for_reference(
        reference="$acme.files.*.*:all()", csvpaths=p
    )
    with pytest.raises(ReferenceException3, match="only one wildcard"):
        finder.query()


@pytest.mark.parametrize("reference", [r for pair in EQUIVALENT for r in pair])
def test_the_estimate_keeps_its_contract(layout, reference):  # noqa: F811
    p, _ = layout
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    measured, raised = _measure(p, reference)
    assert _problems(finder.estimate(), measured, raised) == []
