"""References v3 resolve the same with [references] sql = off and on, for
FILES and CSVPATHS (step 4b).

One CsvPaths registers a varied history with the sql listener group on: a
templated named-file with several versions, a duplicate-bytes
re-registration and a failed registration; a patched named-file; a
named-file deleted and registered again; a deleted named-file; a
named-paths group with several versions and an unchanged reload; a second
group; a deleted group; runs of three groups, one of them templated and
with an id-less statement.

Each reference is then resolved twice on the same CsvPaths, once per mode,
and the ReferenceResults3 must be equal, or both must raise the same
exception type. Since 4c-2 RESULTS are read from SQL under on too. Under
shadow (step 5) the same references must find no difference between the
two sources.
"""

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.sources.filesystem_reference_source import (
    FilesystemReferenceSource,
)
from csvpath.references.sources.reference_source import ReferenceSource
from csvpath.references.sources.shadow_reference_source import (
    ShadowReferenceSource,
)
from csvpath.references.sources.sql_reference_source import SqlReferenceSource
from csvpath.util.box import Box

FIRST = "~ id: first_id ~ $[*][yes()]"
SECOND = "~ id: second_id ~ $[*][no()]"
THIRD = "~ id: third_id ~ $[*][yes()]"
SEP = "\n\n---- CSVPATH ----\n\n"


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


def _register(p: CsvPaths, tmp, *, name: str, n: int, template=None) -> None:
    data = tmp / f"{name}_{n}.csv"
    data.write_text(f"id,amount\n{n},10\n", encoding="utf-8")
    p.file_manager.add_named_file(name=name, path=str(data), template=template)


def _load(p: CsvPaths, tmp, *, name: str, statements: list[str]) -> None:
    f = tmp / f"{name}.csvpaths"
    f.write_text(SEP.join(statements), encoding="utf-8")
    p.paths_manager.add_named_paths_from_file(name=name, file_path=str(f))


@pytest.fixture(scope="module")
def paths(tmp_path_factory):
    _clear_engine()
    tmp = tmp_path_factory.mktemp("sql_parity")
    p = CsvPaths()
    c = p.config
    c.add_to_config(section="inputs", key="files", value=str(tmp / "named_files"))
    c.add_to_config(section="inputs", key="csvpaths", value=str(tmp / "named_paths"))
    c.add_to_config(section="results", key="archive", value=str(tmp / "archive"))
    c.add_to_config(section="listeners", key="groups", value="sql")
    c.add_to_config(section="sql", key="dialect", value="sqlite")
    c.add_to_config(
        section="sql", key="connection_string", value=f"sqlite:///{tmp / 'refs.db'}"
    )
    template = "orders/:filename"
    _register(p, tmp, name="orders", n=0, template=template)
    _register(p, tmp, name="orders", n=1, template=template)
    _register(p, tmp, name="orders", n=1, template=template)
    _register(p, tmp, name="orders", n=2, template=template)
    with pytest.raises(ValueError):
        p.file_manager.add_named_file(name="orders", path="")
    _register(p, tmp, name="people", n=0)
    _register(p, tmp, name="people", n=1)
    p.file_manager.registrar.patch_named_file(name="people", patch={"type": "tsv"})
    _register(p, tmp, name="again", n=0)
    p.file_manager.remove_named_file("again")
    _register(p, tmp, name="again", n=1)
    _register(p, tmp, name="gone", n=0)
    p.file_manager.remove_named_file("gone")
    _load(p, tmp, name="acme", statements=[FIRST])
    _load(p, tmp, name="acme", statements=[FIRST, SECOND])
    _load(p, tmp, name="acme", statements=[FIRST, SECOND])
    _load(p, tmp, name="acme", statements=[FIRST, SECOND, THIRD])
    _load(p, tmp, name="beta", statements=[FIRST])
    _load(p, tmp, name="xgone", statements=[FIRST])
    p.paths_manager.remove_named_paths("xgone")
    #
    # runs (4c-2): acme three times, two ways; beta once; gamma, templated,
    # with an id-less statement
    #
    gamma = tmp / "gamma.csvpaths"
    gamma.write_text(SEP.join([FIRST, "$[*][yes()]"]), encoding="utf-8")
    p.paths_manager.add_named_paths_from_file(
        name="gamma", file_path=str(gamma), template=":0/:run_dir"
    )
    p.collect_paths(pathsname="acme", filename="people")
    p.fast_forward_paths(pathsname="acme", filename="people")
    p.collect_paths(pathsname="acme", filename="orders")
    p.collect_paths(pathsname="beta", filename="people")
    p.collect_paths(pathsname="gamma", filename="orders")
    #
    # a results group run, then removed (4c-3)
    #
    _load(p, tmp, name="rgone", statements=[FIRST])
    p.collect_paths(pathsname="rgone", filename="people")
    p.results_manager.remove_named_results("rgone")
    yield p
    c.add_to_config(section="references", key="sql", value="off")
    _clear_engine()


def _mode(p: CsvPaths, mode: str) -> None:
    p.config.add_to_config(section="references", key="sql", value=mode)


def _resolve(p: CsvPaths, reference: str):
    try:
        finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
        return ("ok", finder.query())
    except Exception as ex:
        return ("raised", type(ex))


def _both(p: CsvPaths, reference: str) -> tuple:
    _mode(p, "off")
    off = _resolve(p, reference)
    assert isinstance(p.reference_source, FilesystemReferenceSource)
    assert not isinstance(p.reference_source, SqlReferenceSource)
    _mode(p, "on")
    on = _resolve(p, reference)
    assert isinstance(p.reference_source, SqlReferenceSource)
    _mode(p, "off")
    return off, on


def _ids(p: CsvPaths) -> dict:
    orders = p.file_manager.get_manifest("orders")
    acme = p.paths_manager.get_manifest_for_name("acme")
    return {
        "@orders_fingerprint": orders[1]["fingerprint"],
        "@orders_uuid": orders[0]["uuid"],
        "@acme_uuid": acme[1]["uuid"],
    }


FILES = [
    "$orders.files.orders/:first()",
    "$orders.files.orders/:last()",
    "$orders.files.*/:last()",
    "$orders.files.:flatten()",
    "$orders.files.:flatten().:first()",
    "$orders.files.:flatten().:last()",
    "$orders.files.:groups()",
    "$orders.files.:groups().:last()",
    "$orders.files.:groups().:from(0):to(1)",
    "$orders.files.:groups().:before(:index(1))",
    "$orders.files.:flatten().:after(:index(0))",
    "$orders.files.:flatten().:index(1)",
    "$orders.files.:manifest()",
    "$orders.files.:manifest():last()",
    "$orders.files.:fingerprint(@orders_fingerprint)",
    "$orders.files.:uuid(@orders_uuid)",
    "$people.files.:index(1)",
    '$orders.files.:status("failed")',
    '$orders.files.:status("complete").:first()',
    '$*.files.:status("failed")',
    '$*.files.:status("complete").:last()',
    "$*.files.:manifest()",
    #
    # the ledger holds a failed registration, which has no file_path and
    # is skipped (see test_star_manifest_field_skips_failures.py)
    #
    "$*.files.:manifest():uuid()",
    "$*.files.:manifest():last()",
    "$*.files.:flatten()",
    "$*.files.:flatten().:last()",
    "$*.files.:groups().:last()",
    "$*.files.:template(:not_empty())",
    "$:regex(/^o/).files.:flatten()",
    "$:regex(/^p/).files.:all()",
    "$people.files.:all()",
    '$people.files.:flatten():type("tsv")',
    "$people.files.:last()",
    "$again.files.:all()",
    "$again.files.:flatten().:first()",
    "$gone.files.:all()",
    "$nope.files.:all()",
]

CSVPATHS = [
    "$acme.csvpaths.:all()",
    "$acme.csvpaths.:first()",
    "$acme.csvpaths.:last()",
    "$acme.csvpaths.:index(1)",
    "$acme.csvpaths.:from(1):to(2):last()",
    "$acme.csvpaths.:before(:index(2))",
    "$acme.csvpaths.:after(:index(0))",
    "$acme.csvpaths.:from(-2)",
    "$acme.csvpaths.:last():uuid()",
    "$acme.csvpaths.:last():fingerprint()",
    "$acme.csvpaths.:last():named_paths_count()",
    "$acme.csvpaths.:last():named_paths_identities()",
    "$acme.csvpaths.:last():manifest()",
    "$acme.csvpaths.:manifest()",
    "$acme.csvpaths.:manifest():last()",
    "$acme.csvpaths.:last().second_id",
    "$acme.csvpaths.:last().first_id",
    "$acme.csvpaths.:all().second_id",
    "$acme.csvpaths.:last():named_paths_name()",
    "$acme.csvpaths.:uuid(@acme_uuid)",
    '$acme.csvpaths.:having("third_id")',
    '$acme.csvpaths.:having("first_id"):from(-2)',
    '$*.csvpaths.:having("first_id"):index(-1)',
    "$*.csvpaths.:all()",
    "$*.csvpaths.:last()",
    "$*.csvpaths.:last():manifest()",
    "$*.csvpaths.:manifest()",
    "$*.csvpaths.:manifest():last()",
    "$*.csvpaths.:uuid()",
    "$*.csvpaths.:manifest():uuid()",
    "$*.csvpaths.:manifest():last():uuid()",
    "$*.csvpaths.:manifest():fingerprint()",
    "$:regex(/^a/).csvpaths.:last()",
    "$:regex(/^z/).csvpaths.:last()",
    "$beta.csvpaths.:all()",
    "$xgone.csvpaths.:all()",
    "$nope.csvpaths.:all()",
]


RESULTS = [
    "$acme.results.:all()",
    "$acme.results.:first()",
    "$acme.results.:last()",
    "$acme.results.:all():last()",
    "$acme.results.:first():named_file_uuid()",
    "$acme.results.:first():named_paths_uuid()",
    "$acme.results.:last():named_file_name()",
    "$acme.results.:last():manifest()",
    "$acme.results.:manifest()",
    "$acme.results.:last().:all()",
    "$acme.results.:last().:all():uuid()",
    "$acme.results.:last().*",
    "$acme.results.:last().:index(1)",
    "$acme.results.:last().:from(1)",
    "$acme.results.:last().first_id",
    "$acme.results.:last().second_id",
    "$acme.results.:last().first_id:data()",
    "$acme.results.:last().first_id:vars()",
    "$acme.results.:last().first_id:meta()",
    "$acme.results.:last().:errors()",
    "$acme.results.:flatten()",
    "$acme.results.:flatten():last()",
    "$acme.results.:flatten():before(:index(2))",
    "$acme.results.:flatten():after(:index(0))",
    "$beta.results.:last().first_id",
    "$gamma.results.:flatten()",
    "$gamma.results.:flatten():last().:all()",
    "$gamma.results.:flatten():last().:index(1)",
    "$*.results.:last()",
    "$*.results.:last():manifest()",
    "$*.results.:manifest()",
    "$*.results.:manifest():last()",
    "$*.results.:manifest():first():run_uuid()",
    "$*.results.:manifest():archive_name()",
    "$*.results.:manifest():index(1)",
    "$*.results.:manifest():run_uuid()",
    '$*.results.:manifest():having("first_id")',
    '$*.results.:manifest():named_paths_name("rgone")',
    "$:regex(/^r/).results.:manifest():last()",
    "$*.results.:flatten():first():uuid()",
    "$*.results.:flatten():error_count(0)",
    '$*.results.:groups():named_file_name("orders")',
    "$:regex(/^b/).results.:last()",
    "$:regex(/^g/).results.:flatten()",
    "$nope.results.:last()",
    "$rgone.results.:last()",
    "$rgone.results.:all()",
]


def _with_ids(p: CsvPaths, reference: str) -> str:
    for var, value in _ids(p).items():
        reference = reference.replace(var, f'"{value}"')
    return reference


ALL = FILES + CSVPATHS + RESULTS


@pytest.mark.parametrize("reference", ALL)
def test_off_and_on_agree(paths, reference):
    off, on = _both(paths, _with_ids(paths, reference))
    assert off == on


def test_most_references_resolve_to_something(paths):
    #
    # parity of empty results or of errors proves little. most of the
    # references above must find something.
    #
    found = 0
    for reference in ALL:
        kind, value = _both(paths, _with_ids(paths, reference))[0]
        if kind == "ok" and len(value) > 0:
            found += 1
    assert found >= 0.85 * len(ALL)


def test_deleted_names_are_gone_in_both_modes(paths):
    for reference in [
        "$gone.files.:all()",
        "$xgone.csvpaths.:all()",
        "$rgone.results.:all()",
    ]:
        off, on = _both(paths, reference)
        assert off == on
        assert off[0] == "raised" or len(off[1]) == 0


def test_star_ledger_read_keeps_the_deleted_group_in_both_modes(paths):
    #
    # under '*', a field reads the root ledger, deleted entries included
    # (2026-10-30). the SQL ledger read keeps deleted rows, as the JSON
    # ledger does, so both modes see xgone.
    #
    for reference in ["$*.csvpaths.:uuid()", "$*.csvpaths.:manifest():uuid()"]:
        off, on = _both(paths, reference)
        assert off == on
        assert any("xgone" in f for f in off[1].files)


def test_star_manifest_set_keeps_the_deleted_run_in_both_modes(paths):
    #
    # the logical RESULTS manifest set (compendium 6.13b, C2a,
    # 2026-10-31) is built from the ledger, deleted runs included, so
    # both modes see rgone's run and resolve the same values; rgone's
    # run manifest is gone in both, so its status is None in both.
    #
    def _resolved(mode: str, reference: str) -> list:
        _mode(paths, mode)
        try:
            finder = ReferenceFinderFactory3.for_reference(
                reference=reference, csvpaths=paths
            )
            return [r.data for r in finder.resolve().results]
        finally:
            _mode(paths, "off")

    reference = '$*.results.:manifest():named_paths_name("rgone"):status()'
    assert _resolved("off", reference) == _resolved("on", reference) == [None]
    for reference in [
        "$*.results.:manifest():run_uuid()",
        "$*.results.:manifest():status()",
        "$*.results.:manifest()",
    ]:
        assert _resolved("off", reference) == _resolved("on", reference), reference


def test_re_registered_name_is_the_new_version_in_both_modes(paths):
    off, on = _both(paths, "$again.files.:all()")
    assert off == on
    assert len(off[1]) == 1
    #
    # version B (again_1.csv), not the deleted A (again_0.csv)
    #
    assert off[1].files[0].endswith("again_1.csv")


def test_shadow_finds_no_differences(paths):
    #
    # step 5: every reference resolved under shadow, on one source, equals
    # off, and the source compared every read without a difference or a
    # SQL error. all 11 reads are exercised.
    #
    references = [_with_ids(paths, r) for r in ALL]
    _mode(paths, "off")
    off = [_resolve(paths, r) for r in references]
    _mode(paths, "shadow")
    try:
        source = paths.reference_source
        assert isinstance(source, ShadowReferenceSource)
        shadow = [_resolve(paths, r) for r in references]
        assert paths.reference_source is source
    finally:
        _mode(paths, "off")
    for reference, a, b in zip(references, off, shadow):
        assert a == b, reference
    counts = source.counts
    assert sorted(counts) == sorted(ReferenceSource.__abstractmethods__)
    for method, c in counts.items():
        assert c["reads"] > 0, method
        assert c["differences"] == 0, method
        assert c["sql_errors"] == 0, method
        assert c["matches"] == c["reads"], method
