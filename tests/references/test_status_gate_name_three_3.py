#
# a bare FILES ':status()'/':lifecycle()' gate in name_one with more than a
# lone pointer in name_three -- a pointer and a field, a range, a window, a
# gate, ':manifest()' (name_one gap review, item G). Each raised "a field
# accessor or range function riding alongside it is not yet supported".
# The gate's matched versions now go through the ordinary name_three
# pipeline, so a literal root reads as ':flatten().:status(...)' with the
# same name_three, and a '$*'/':regex()' root keeps one group per named-file
# (compendium 4.1b; decision D31).
#
import pytest

from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_parser_3 import ReferenceParser3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import NAMES, layout  # noqa: F401

THREES = [
    ".:last():uuid()",
    ".:first():time()",
    ".:last():manifest()",
    ".:from(1)",
    '.:type("csv")',
    ".:today():last()",
    ".:uuid()",
    ".:from(0):to(0)",
]

GATES = ['status("complete")', 'lifecycle("active")']


def _query(p, reference: str) -> list:
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    return [(str(r.path), r.uuid) for r in finder.query().results]


def _resolved(p, reference: str) -> list:
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    return [r.data for r in finder.resolve_from(finder.query()).results]


class TestWhichShapesTakeThePipeline:
    @pytest.mark.parametrize(
        "three,expected",
        [(None, False), (".:last()", False), (".:index(1)", False)]
        + [(t, True) for t in THREES],
    )
    def test_shapes(self, layout, three, expected):  # noqa: F811
        p, _ = layout
        reference = '$alpha.files.:status("complete")' + (three or "")
        parsed = ReferenceParser3(string=reference, csvpaths=p).parsed
        assert FilesReferenceFinder3._status_gate_takes_the_pipeline(parsed) is expected

    def test_none_raises(self):
        with pytest.raises(ValueError):
            FilesReferenceFinder3._status_gate_takes_the_pipeline(None)


@pytest.mark.parametrize("gate", GATES)
@pytest.mark.parametrize("three", THREES)
def test_a_literal_root_reads_as_the_name_three_gate(layout, gate, three):  # noqa: F811
    # every live version of the named-file, gated, then the same name_three
    p, _ = layout
    written = f"$alpha.files.:{gate}{three}"
    same_as = f"$alpha.files.:flatten().:{gate}{three[1:]}"
    assert _query(p, written) == _query(p, same_as)


@pytest.mark.parametrize(
    "three", [t for t in THREES if t not in ('.:type("csv")', ".:uuid()")]
)
def test_a_star_root_is_one_group_per_named_file(layout, three):  # noqa: F811
    p, _ = layout
    star = _query(p, f'$*.files.:status("complete"){three}')
    literal = []
    for name in NAMES:
        literal += _query(p, f'${name}.files.:status("complete"){three}')
    assert sorted(star) == sorted(literal)


def test_a_field_after_a_pointer_resolves_to_the_field(layout):  # noqa: F811
    p, _ = layout
    uuids = [u for _, u in _query(p, '$*.files.:status("complete").:last()')]
    assert sorted(
        _resolved(p, '$*.files.:status("complete").:last():uuid()')
    ) == sorted(uuids)


def test_a_lone_pointer_keeps_its_results(layout):  # noqa: F811
    # unchanged: _query_status_gate() still answers a lone pointer
    p, _ = layout
    assert _query(p, '$*.files.:status("complete").:last()') == [
        r
        for name in NAMES
        for r in _query(p, f'${name}.files.:status("complete").:last()')
    ]


@pytest.mark.parametrize(
    "reference",
    [f'$alpha.files.:status("complete"){t}' for t in THREES]
    + [f'$*.files.:status("complete"){t}' for t in THREES]
    + ['$:regex(/^(alpha|beta)$/).files.:lifecycle("active").:last():uuid()'],
)
def test_the_estimate_keeps_its_contract(layout, reference):  # noqa: F811
    p, _ = layout
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    measured, raised = _measure(p, reference)
    assert _problems(finder.estimate(), measured, raised) == []
