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
from csvpath.util.nos import Nos

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
    #
    # an explicit ':manifest()' gives the manifest holding the entry on
    # query (compendium 5.7, 2026-11-01)
    #
    "$orders.files.:manifest():first()",
    "$orders.files.:manifest():uuid()",
    "$orders.files.:flatten().:last():manifest()",
    "$*.files.:flatten().:last():manifest()",
    "$*.files.:all().:last():manifest()",
    #
    # C1 bare-half revert (2026-11-01): bare '*' reads the live
    # named-files; ':manifest()' the whole ledger, failures included
    #
    '$orders.files.:status("complete")',
    '$*.files.:manifest():status("failed")',
    '$*.files.:manifest():status("complete")',
    #
    # finding E (2026-11-02): a general chain after ':manifest()'
    #
    "$orders.files.:manifest():last():uuid()",
    "$orders.files.:manifest():first():fingerprint()",
    '$orders.files.:manifest():status("complete"):last()',
    '$people.files.:type("tsv"):manifest()',
    "$*.files.:manifest():last():named_file_name()",
    '$*.files.:manifest():status("failed"):named_file_name("orders")',
    '$*.files.:manifest():status("complete"):type("csv"):first():uuid()',
    '$:regex(/^o/).files.:manifest():named_file_name("orders"):last()',
    #
    # finding G (2026-11-02): name_three gates, range before gate, the last
    # value field wins
    #
    '$people.files.:flatten().:type("tsv"):uuid()',
    '$people.files.:flatten().:type("csv"):last()',
    '$orders.files.:flatten().:from(0):to(1):type("csv"):uuid()',
    "$orders.files.:flatten().:last():fingerprint():template()",
    '$*.files.:flatten().:type("tsv"):last():uuid()',
    '$*.files.:all().:last():type("csv")',
    #
    # E3 (2026-11-02): ':definition()' with fields
    #
    "$orders.files.:definition():template()",
    "$orders.files.:definition(:template(:not_none()))",
    "$*.files.:definition():template()",
    "$*.files.:definition(:template(:not_none()))",
    "$:regex(/^o/).files.:definition():template()",
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
    "$acme.csvpaths.:all():manifest()",
    "$*.csvpaths.:all():last():manifest()",
    "$*.csvpaths.:manifest():first()",
    '$:regex(/^a/).csvpaths.:uuid()',
    "$*.csvpaths.:named_paths_name()",
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
    "$acme.results.:last().first_id:errors()",
    "$acme.results.:last().first_id:manifest()",
    "$acme.results.:last().first_id:manifest():uuid()",
    "$*.results.:flatten():manifest():run_uuid()",
    "$acme.results.:all():manifest()",
    "$*.results.:flatten():last():manifest()",
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
    "$*.results.:manifest():last().*",
    "$*.results.:manifest():last().:last():time()",
    '$*.results.:manifest():named_paths_name("rgone").*',
    '$*.results.:manifest():having("first_id"):last().first_id:manifest()',
    '$*.results.:manifest():having("first_id"):last().first_id:vars()',
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
    # under '*', ':manifest()' reads the root ledger, deleted entries
    # included (2026-10-30). the SQL ledger read keeps deleted rows, as the
    # JSON ledger does, so both modes see xgone, by its uuid: each record's
    # path is the ledger (compendium 5.7, 2026-11-01). a bare field reads
    # the live groups (C1 bare-half revert, 2026-11-01), so neither mode
    # sees xgone there.
    #
    off, on = _both(paths, "$*.csvpaths.:uuid()")
    assert off == on
    assert not any("xgone" in f for f in off[1].files)
    bare_uuids = off[1].uuids
    off, on = _both(paths, "$*.csvpaths.:manifest():uuid()")
    assert off == on
    assert set(bare_uuids) < set(off[1].uuids)
    ledger = Nos(paths.config.inputs_csvpaths_path).join("manifest.json")
    assert set(off[1].files) == {ledger}
    _mode(paths, "off")
    xgone = [
        e["uuid"]
        for e in paths.reference_source.paths_ledger()
        if e.get("named_paths_name") == "xgone"
    ]
    assert xgone
    assert set(xgone) <= set(off[1].uuids)
    assert not set(xgone) & set(bare_uuids)


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
    # C2b, 2026-11-01: rgone's instance manifest is gone too
    reference = '$*.results.:manifest():named_paths_name("rgone").first_id:manifest()'
    assert _resolved("off", reference) == _resolved("on", reference) == [None]
    for reference in [
        "$*.results.:manifest():run_uuid()",
        "$*.results.:manifest():status()",
        "$*.results.:manifest()",
        '$*.results.:manifest():named_paths_name("rgone").*:uuid()',
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


@pytest.mark.parametrize(
    "reference",
    [
        "$orders.files.:manifest():first()",
        "$orders.files.:manifest():uuid()",
        "$orders.files.:flatten().:last():manifest()",
        "$*.files.:flatten().:last():manifest()",
        "$*.files.:all().:last():manifest()",
        "$*.files.:manifest():uuid()",
        "$acme.csvpaths.:all():manifest()",
        "$*.csvpaths.:all():last():manifest()",
        "$*.csvpaths.:manifest():first()",
        "$*.csvpaths.:manifest():uuid()",
    ],
)
def test_a_manifest_entry_query_path_is_a_real_manifest(paths, reference):
    #
    # an explicit ':manifest()' gives the manifest.json holding each
    # entry (compendium 5.7, 2026-11-01). each path is a real file on
    # disk, in both modes.
    #
    off, on = _both(paths, reference)
    assert off == on
    assert off[0] == "ok"
    assert off[1].results
    for path in off[1].files:
        assert path.endswith("manifest.json")
        assert Nos(path).exists(), path


def test_bare_star_reads_live_named_files_and_manifest_reads_the_ledger(paths):
    #
    # C1 bare-half revert (2026-11-01, agreed with David; compendium 6.19,
    # NRE 253): a bare '*' read searches each live named-file or group,
    # and ':manifest()' reaches the whole ledger. on a real filesystem,
    # in both modes.
    #
    _mode(paths, "off")
    files_ledger = paths.reference_source.files_ledger()
    paths_ledger = paths.reference_source.paths_ledger()
    failed = [e["uuid"] for e in files_ledger if e.get("status") == "failed"]
    gone = [e["uuid"] for e in files_ledger if e.get("named_file_name") == "gone"]
    xgone = [e["uuid"] for e in paths_ledger if e.get("named_paths_name") == "xgone"]
    assert failed and gone and xgone

    def _uuids(reference: str) -> list:
        off, on = _both(paths, reference)
        assert off == on
        assert off[0] == "ok"
        return off[1].uuids

    complete = _uuids('$*.files.:status("complete")')
    assert complete
    assert not set(gone) & set(complete)
    assert _uuids('$*.files.:status("failed")') == []
    assert _uuids('$*.files.:manifest():status("failed")') == failed
    assert set(gone) <= set(_uuids('$*.files.:manifest():status("complete")'))
    assert not set(xgone) & set(_uuids("$*.csvpaths.:uuid()"))
    assert set(xgone) <= set(_uuids("$*.csvpaths.:manifest():uuid()"))


def test_a_general_manifest_chain_on_a_real_filesystem(paths):
    #
    # finding E (2026-11-02): FILES takes a general chain after
    # ':manifest()'. the new NRE 253 finds the failed orders registration
    # in the ledger set, and a gate filters before the pointer picks. on
    # a real filesystem, in both modes.
    #
    _mode(paths, "off")
    ledger = paths.reference_source.files_ledger()
    orders = paths.file_manager.get_manifest("orders")
    failed = [
        e["uuid"]
        for e in ledger
        if e.get("status") == "failed" and e.get("named_file_name") == "orders"
    ]
    assert failed

    def _resolved(reference: str) -> list:
        off, on = _both(paths, reference)
        assert off == on
        assert off[0] == "ok"
        _mode(paths, "off")
        finder = ReferenceFinderFactory3.for_reference(
            reference=reference, csvpaths=paths
        )
        return finder.query().uuids, [r.data for r in finder.resolve().results]

    uuids, _ = _resolved(
        '$*.files.:manifest():status("failed"):named_file_name("orders")'
    )
    assert uuids == failed
    uuids, values = _resolved("$orders.files.:manifest():last():uuid()")
    assert values == [orders[-1]["uuid"]]
    uuids, values = _resolved("$orders.files.:manifest():uuid():first()")
    assert values == [orders[0]["uuid"]]
    #
    # the ledger's last record is not an orders record, so the name gate
    # must filter before ':last()' picks.
    #
    assert ledger[-1].get("named_file_name") != "orders"
    uuids, values = _resolved(
        '$*.files.:manifest():last():named_file_name("orders"):file_path()'
    )
    orders_records = [
        e for e in ledger if e.get("named_file_name") == "orders"
    ]
    assert uuids == [orders_records[-1]["uuid"]]
    assert values == [orders_records[-1]["file_path"]]


def test_name_three_gates_on_a_real_filesystem(paths):
    #
    # finding G (2026-11-02): a name_three gate filters before the pointer
    # picks, supplies no value, and with no value field the reference
    # resolves to the version bytes. on a real filesystem, in both modes.
    #
    _mode(paths, "off")
    people = paths.file_manager.get_manifest("people")
    tsv = [e["uuid"] for e in people if e.get("type") == "tsv"]
    csv = [e for e in people if e.get("type") == "csv"]
    assert tsv and csv

    def _finder(reference: str):
        off, on = _both(paths, reference)
        assert off == on
        assert off[0] == "ok"
        _mode(paths, "off")
        return ReferenceFinderFactory3.for_reference(
            reference=reference, csvpaths=paths
        )

    finder = _finder('$people.files.:flatten().:type("tsv"):uuid()')
    assert [r.data for r in finder.resolve().results] == tsv
    finder = _finder('$people.files.:flatten().:last():type("csv")')
    assert finder.query().uuids == [csv[-1]["uuid"]]
    with open(csv[-1]["file"], "rb") as f:
        assert finder.resolve().results[0].data == f.read()
    finder = _finder("$people.files.:flatten().:last():fingerprint():template()")
    assert [r.data for r in finder.resolve().results] == [people[-1]["template"]]


def test_definition_chains_on_a_real_filesystem(paths):
    #
    # E3 (2026-11-02): ':definition()' with fields reads each named-file's
    # one definition.json, on a real filesystem, in both modes. Registering
    # with a template does not write definition.json, so this stores one
    # for people, and puts people's definition back afterwards.
    #
    describer = paths.file_manager.describer
    original = describer.get_json("people")
    describer.store_template("people", "people/:filename")

    def _finder(reference: str):
        off, on = _both(paths, reference)
        assert off == on
        assert off[0] == "ok"
        _mode(paths, "off")
        return ReferenceFinderFactory3.for_reference(
            reference=reference, csvpaths=paths
        )

    try:
        finder = _finder("$people.files.:definition():template()")
        assert [r.data for r in finder.resolve().results] == ["people/:filename"]
        finder = _finder("$people.files.:definition(:template(:not_none()))")
        results = finder.resolve().results
        assert len(results) == 1
        with open(results[0].path, "rb") as f:
            assert results[0].data == f.read()
        finder = _finder("$*.files.:definition(:template(:not_none()))")
        home = paths.file_manager.named_file_home("people")
        assert finder.query().files == [Nos(home).join("definition.json")]
    finally:
        describer.store_json("people", original)
