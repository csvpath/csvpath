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
import json
import os

import pytest

from csvpath.references.reference_exceptions_3 import ReferenceRuntimeException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_parser_3 import ReferenceParser3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import (  # noqa: F401
    NAMES,
    _config_file,
    _registered,
    layout,
)

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


# ===================
# gates that filter, one uuid in two manifests, order (reviewer on #795)
# ===================


def _ledger_path(p) -> str:
    return os.path.join(p.config.inputs_files_path, "manifest.json")


@pytest.fixture(scope="module")
def gated(tmp_path_factory):
    # the layout, with alpha's first one.csv no longer complete and beta's
    # second EMEA/two.csv no longer active, in the ledger
    tmp = tmp_path_factory.mktemp("status_gate_gated")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        p, label = _registered(tmp)
        by_label = {v: k for k, v in label.items()}
        with open(_ledger_path(p), encoding="utf-8") as f:
            ledger = json.load(f)
        for record in ledger:
            if record.get("uuid") == by_label["alpha:one.csv#1"]:
                record["status"] = "incomplete"
            if record.get("uuid") == by_label["beta:EMEA/two.csv#2"]:
                record["lifecycle"] = "retired"
        with open(_ledger_path(p), "w", encoding="utf-8") as f:
            json.dump(ledger, f)
        yield p, label
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _labels(gated, reference: str) -> list:
    p, label = gated
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    return [label[r.uuid] for r in finder.query().results]


class TestGatesThatFilter:
    def test_status_excludes_the_incomplete_version(self, gated):
        assert _labels(gated, '$alpha.files.:status("complete").:from(0)') == [
            "alpha:zero.csv#1",
            "alpha:one.csv#2",
        ]

    def test_lifecycle_excludes_the_retired_version(self, gated):
        assert _labels(gated, '$beta.files.:lifecycle("active").:last():uuid()') == [
            "beta:APAC/five.csv#1"
        ]
        assert "beta:EMEA/two.csv#2" not in _labels(
            gated, '$beta.files.:lifecycle("active").:from(0)'
        )

    @pytest.mark.parametrize("three", THREES)
    def test_still_the_name_three_gate_spelling(self, gated, three):
        p, _ = gated
        written = f'$alpha.files.:status("complete"){three}'
        same_as = f'$alpha.files.:flatten().:status("complete"){three[1:]}'
        assert _query(p, written) == _query(p, same_as)

    def test_a_gate_chain_on_a_literal_root(self, gated):
        # raised "field functions attached directly to name_one" while '$*'
        # took it
        assert _labels(
            gated, '$beta.files.:status("complete"):lifecycle("active").:from(0)'
        ) == [
            "beta:EMEA/two.csv#1",
            "beta:APAC/two.csv#1",
            "beta:APAC/two.csv#2",
            "beta:APAC/five.csv#1",
        ]


class TestOrder:
    @pytest.mark.parametrize(
        "three",
        [".:last()", ".:last():uuid()", ".:last():manifest()", ".:from(0):to(0)"],
    )
    def test_a_star_root_gives_name_order(self, gated, three):
        # D31: one per named-file, in name order, for a pointer and its
        # field alike (the first version gave ledger order for the field)
        star = _labels(gated, f'$*.files.:status("complete"){three}')
        literal = []
        for name in NAMES:
            literal += _labels(gated, f'${name}.files.:status("complete"){three}')
        assert star == literal


def test_a_uuid_in_two_manifests_raises(tmp_path_factory):
    # D4/D31: the lone pointer raised; the pipeline dropped it quietly
    tmp = tmp_path_factory.mktemp("status_gate_d4")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        p, label = _registered(tmp)
        alpha = p.file_manager.get_manifest("alpha")
        beta_path = os.path.join(
            p.file_manager.named_file_home("beta"), "manifest.json"
        )
        with open(beta_path, encoding="utf-8") as f:
            beta = json.load(f)
        beta.append(alpha[0])
        with open(beta_path, "w", encoding="utf-8") as f:
            json.dump(beta, f)
        for reference in (
            '$beta.files.:status("complete").:last():uuid()',
            '$:regex(/^b/).files.:status("complete").:from(0)',
        ):
            finder = ReferenceFinderFactory3.for_reference(
                reference=reference, csvpaths=p
            )
            with pytest.raises(ReferenceRuntimeException3, match="inconsistent"):
                finder.query()
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous
