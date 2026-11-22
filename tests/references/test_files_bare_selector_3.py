#
# a bare FILES ':fingerprint("…")' / ':uuid("…")' in name_one (compendium
# 6.19, 6.44). Two bugs found checking the spec text (#799):
# - resolve raised "does not support resolve_kind='metadata_field'"; the
#   selector picks one version, so it resolves to the version's bytes
# - under '$*' (and ':regex()'/':choice()') query raised "field functions
#   attached directly to name_one"; 6.19: it "search[es] for the given
#   fingerprint across all named-files ... each live named-file in turn"
#
import pytest

from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import NAMES, layout  # noqa: F401


def _finder(*, p, reference: str):
    return ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)


def _an_entry(p, name: str, index: int) -> dict:
    return p.file_manager.get_manifest(name)[index]


@pytest.mark.parametrize("field", ["fingerprint", "uuid"])
@pytest.mark.parametrize(
    "root", ["$beta", "$*", "$:regex(/^b/)", '$:choice("alpha|beta")']
)
def test_finds_the_version_and_resolves_to_its_bytes(layout, field, root):  # noqa: F811
    p, _ = layout
    entry = _an_entry(p, "beta", 1)
    finder = _finder(p=p, reference=f'{root}.files.:{field}("{entry[field]}")')
    selection = finder.query()
    assert [r.uuid for r in selection.results] == [entry["uuid"]]
    with open(entry["file"], "rb") as f:
        expected = f.read()
    assert [r.data for r in finder.resolve_from(selection).results] == [expected]


def test_a_star_root_is_the_literal_roots_together(layout):  # noqa: F811
    p, _ = layout
    fingerprint = _an_entry(p, "acme", 0)["fingerprint"]
    star = [
        r.uuid
        for r in _finder(p=p, reference=f'$*.files.:fingerprint("{fingerprint}")')
        .query()
        .results
    ]
    literal = []
    for name in NAMES:
        literal += [
            r.uuid
            for r in _finder(
                p=p, reference=f'${name}.files.:fingerprint("{fingerprint}")'
            )
            .query()
            .results
        ]
    assert star and star == literal


def test_no_match_is_nothing(layout):  # noqa: F811
    p, _ = layout
    assert _finder(p=p, reference='$*.files.:fingerprint("nope")').query().results == []


def test_a_name_three_still_raises(layout):  # noqa: F811
    p, _ = layout
    fingerprint = _an_entry(p, "acme", 0)["fingerprint"]
    with pytest.raises(Exception, match="already identifies one specific version"):
        _finder(
            p=p, reference=f'$*.files.:fingerprint("{fingerprint}").:last()'
        ).query()


@pytest.mark.parametrize("root", ["$acme", "$*"])
def test_the_estimate_keeps_its_contract(layout, root):  # noqa: F811
    p, _ = layout
    reference = f'{root}.files.:fingerprint("{_an_entry(p, "acme", 0)["fingerprint"]}")'
    measured, raised = _measure(p, reference)
    assert (
        _problems(_finder(p=p, reference=reference).estimate(), measured, raised) == []
    )
