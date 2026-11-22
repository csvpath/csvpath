#
# a bare FILES ':fingerprint("…")' / ':uuid("…")' in name_one (compendium
# 6.19, 6.44). Two bugs found checking the spec text (#799):
# - resolve raised "does not support resolve_kind='metadata_field'"; the
#   selector picks one version, so it resolves to the version's bytes
# - under '$*' (and ':regex()'/':choice()') query raised "field functions
#   attached directly to name_one"; 6.19: it "search[es] for the given
#   fingerprint across all named-files ... each live named-file in turn"
#
import json
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_exceptions_3 import (
    ReferenceException3,
    ReferenceRuntimeException3,
)
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import (  # noqa: F401
    NAMES,
    _config_file,
    layout,
)


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
    with pytest.raises(
        ReferenceException3, match="already identifies one specific version"
    ):
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


# ===================
# the same bytes registered more than once (reviewer on #800)
# ===================


@pytest.fixture(scope="module")
def dup(tmp_path_factory):
    # 'dup' has content A at x.csv and at y/x.csv, and content B; 'twin' has A
    tmp = tmp_path_factory.mktemp("bare_selector_dup")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        p = CsvPaths()
        for n, (name, template, text) in enumerate(
            [
                ("dup", None, "id\nA\n"),
                ("dup", "y/:filename", "id\nA\n"),
                ("dup", None, "id\nB\n"),
                ("twin", None, "id\nA\n"),
            ]
        ):
            src = tmp / "src" / str(n)
            src.mkdir(parents=True)
            (src / "x.csv").write_text(text, encoding="utf-8")
            p.file_manager.add_named_file(
                name=name, path=str(src / "x.csv"), template=template
            )
        yield p
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _fingerprint_a(p) -> str:
    return p.file_manager.get_manifest("twin")[0]["fingerprint"]


class TestDuplicateContent:
    def test_every_version_with_the_bytes(self, dup):
        fp = _fingerprint_a(dup)
        uuids = [
            r.uuid
            for r in _finder(p=dup, reference=f'$*.files.:fingerprint("{fp}")')
            .query()
            .results
        ]
        assert len(uuids) == 3
        assert (
            len(
                [
                    r
                    for r in _finder(
                        p=dup, reference=f'$dup.files.:fingerprint("{fp}")'
                    )
                    .query()
                    .results
                ]
            )
            == 2
        )

    def test_resolve_reads_one_version_file_at_a_time(self, dup):
        # 5.3: several version files raise at resolve; resolve_each reads each
        finder = _finder(
            p=dup, reference=f'$*.files.:fingerprint("{_fingerprint_a(dup)}")'
        )
        selection = finder.query()
        with pytest.raises(ReferenceException3, match="more than one"):
            finder.resolve_from(selection)
        assert [r.data for r in finder.resolve_each(selection).results] == [
            b"id\nA\n"
        ] * 3

    def test_a_variable_argument_on_either_root(self, dup):
        # the literal root read the unresolved argument and matched nothing
        fp = _fingerprint_a(dup)
        for reference in (
            "$dup.files.:fingerprint(@fp)",
            '$dup.files.:fingerprint("{@fp}")',
            "$*.files.:fingerprint(@fp)",
        ):
            finder = _finder(p=dup, reference=reference)
            finder.set_variable("fp", value=fp)
            assert finder.query().results, reference

    def test_the_estimate_keeps_its_contract(self, dup):
        reference = f'$*.files.:fingerprint("{_fingerprint_a(dup)}")'
        measured, raised = _measure(dup, reference)
        assert (
            _problems(_finder(p=dup, reference=reference).estimate(), measured, raised)
            == []
        )


def test_a_uuid_in_two_manifests_raises(tmp_path_factory):
    # D4/D31 c: inconsistent framework data raises and is logged
    tmp = tmp_path_factory.mktemp("bare_selector_d4")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        p = CsvPaths()
        for n, name in enumerate(("one", "two")):
            src = tmp / "src" / str(n)
            src.mkdir(parents=True)
            (src / "x.csv").write_text(f"id\n{n}\n", encoding="utf-8")
            p.file_manager.add_named_file(name=name, path=str(src / "x.csv"))
        stray = p.file_manager.get_manifest("one")[0]
        path = os.path.join(p.file_manager.named_file_home("two"), "manifest.json")
        with open(path, encoding="utf-8") as f:
            two = json.load(f)
        two.append(stray)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(two, f)
        for reference in (
            f'$two.files.:uuid("{stray["uuid"]}")',
            f'$*.files.:uuid("{stray["uuid"]}")',
        ):
            with pytest.raises(ReferenceRuntimeException3, match="inconsistent"):
                ReferenceFinderFactory3.for_reference(
                    reference=reference, csvpaths=p
                ).query()
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous
