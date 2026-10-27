"""FileRegistrar.patch_named_file changes one entry of a named-file's
manifest: its type and/or its file name. It goes through
Registrar.distribute_patch:

  - the registrar runs first. Its metadata_patch applies the patch, writes
    the manifest and sets mdata.manifest_entry to the patched entry. If it
    fails, the error is raised and no other listener runs.
  - then each listener's metadata_patch. Listener's default ignores
    patches; SqlFileListener updates the entry's row, so SQL stays in step
    with the manifest. Failures follow the same rules as distribute_update.

A patch is not a registration: it adds no manifest entry and no root
ledger entry. It patches the arrival's ledger entry in place; see
test_patch_ledger_events.py.

Every test uses its own SQLite file and roots under pytest's tmp_path.
The engine is cached in Box, so each test clears it before and after.
"""

import copy
import json
import os

import pytest
from sqlalchemy import text

from csvpath import CsvPaths
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
from csvpath.managers.integrations.sql.sql_listener import SqlListener
from csvpath.managers.listener import Listener
from csvpath.util.box import Box
from csvpath.util.exceptions import RequiredListenerException
import csvpath.managers.files.file_registrar as file_registrar_module

NO_RAISE_POLICY = "collect, print"


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


def _paths(tmp_path, *, groups: str) -> CsvPaths:
    p = CsvPaths()
    p.config.add_to_config(
        section="inputs", key="files", value=str(tmp_path / "named_files")
    )
    p.config.add_to_config(
        section="inputs", key="csvpaths", value=str(tmp_path / "named_paths")
    )
    p.config.add_to_config(
        section="results", key="archive", value=str(tmp_path / "archive")
    )
    p.config.add_to_config(section="listeners", key="groups", value=groups)
    p.config.add_to_config(section="sql", key="dialect", value="sqlite")
    p.config.add_to_config(
        section="sql",
        key="connection_string",
        value=f"sqlite:///{tmp_path / 'patch.db'}",
    )
    return p


@pytest.fixture
def paths(tmp_path):
    #
    # default and sql listeners on
    #
    _clear_engine()
    yield _paths(tmp_path, groups="default, sql")
    _clear_engine()


@pytest.fixture
def plain(tmp_path):
    #
    # default listeners only, for tests that add their own
    #
    _clear_engine()
    yield _paths(tmp_path, groups="default")
    _clear_engine()


def _register(paths: CsvPaths, tmp_path, *, n: int = 0) -> None:
    data = tmp_path / f"orders_{n}.csv"
    data.write_text(f"id,amount\n{n},10\n", encoding="utf-8")
    paths.file_manager.add_named_file(name="orders", path=str(data))


def _manifest(paths: CsvPaths) -> list:
    #
    # a copy: the manifest can come back as a cached object that a later
    # patch changes in place
    #
    return copy.deepcopy(paths.file_manager.get_manifest("orders"))


def _ledger(paths: CsvPaths) -> list:
    return paths.file_manager.files_root_manifest


def _rows(paths: CsvPaths) -> list[dict]:
    listener = SqlFileListener(config=paths.config)
    listener.csvpaths = paths
    #
    # touching the table makes sure it exists
    #
    _ = listener.named_file
    with listener.engine.connect() as conn:
        result = conn.execute(text("select * from named_file"))
        return [dict(r._mapping) for r in result]


def _row(paths: CsvPaths, *, uuid: str) -> dict:
    rows = [r for r in _rows(paths) if r["uuid"] == uuid]
    assert len(rows) == 1
    return rows[0]


def _patch(paths: CsvPaths, **kwargs) -> None:
    paths.file_manager.registrar.patch_named_file(name="orders", **kwargs)


class _Recording(Listener):
    """records the patched entry it was given"""

    def __init__(self, config) -> None:
        super().__init__(config)
        self.patched = []

    def metadata_update(self, mdata) -> None: ...

    def metadata_patch(self, mdata) -> None:
        self.patched.append(mdata.manifest_entry)


class _UpdatesOnly:
    """a listener that does not subclass Listener and has no
    metadata_patch"""

    def __init__(self, config) -> None:
        self.config = config
        self.csvpaths = None
        self.updates = 0

    def metadata_update(self, mdata) -> None:
        self.updates += 1


class _FailingSqlPatch(SqlListener):
    def metadata_update(self, mdata) -> None: ...

    def metadata_patch(self, mdata) -> None:
        raise RuntimeError("sql patch failed")


# ===================
# the hook
# ===================


def test_listener_ignores_patches_by_default(paths):
    class _Plain(Listener):
        def metadata_update(self, mdata) -> None: ...

    assert _Plain(paths.config).metadata_patch(FileMetadata(paths.config)) is None


def test_file_metadata_has_no_patch_by_default(paths):
    m = FileMetadata(paths.config)
    assert m.patch is None
    assert m.patch_index == -1


def test_distribute_patch_rejects_none(paths):
    with pytest.raises(Exception, match="Metadata cannot be None"):
        paths.file_manager.registrar.distribute_patch(None)


def test_metadata_patch_requires_a_patch(paths):
    with pytest.raises(ValueError, match="no patch"):
        paths.file_manager.registrar.metadata_patch(FileMetadata(paths.config))


# ===================
# argument checks
# ===================


@pytest.mark.parametrize(
    "name,ex",
    [(None, ValueError), ("", ValueError), ("  ", ValueError), (3, TypeError)],
)
def test_bad_name(paths, name, ex):
    with pytest.raises(ex):
        paths.file_manager.registrar.patch_named_file(
            name=name, patch={"type": "csv"}
        )


@pytest.mark.parametrize(
    "patch,ex",
    [
        (None, ValueError),
        ("type=csv", TypeError),
        ({}, ValueError),
        ({"typ": "csv"}, ValueError),
        ({"type": "csv", "mark": "x"}, ValueError),
        ({"type": 3}, TypeError),
        ({"type": None}, TypeError),
        ({"type": " "}, ValueError),
        ({"file_name": ""}, ValueError),
    ],
)
def test_bad_patch(paths, patch, ex):
    with pytest.raises(ex):
        _patch(paths, patch=patch)


@pytest.mark.parametrize("index", ["1", 1.0, True, None])
def test_bad_index(paths, index):
    with pytest.raises(TypeError):
        _patch(paths, patch={"type": "csv"}, index=index)


def test_bad_arguments_change_nothing(paths, tmp_path):
    _register(paths, tmp_path)
    before = _manifest(paths)
    with pytest.raises(ValueError):
        _patch(paths, patch={"typ": "tsv"})
    assert _manifest(paths) == before


# ===================
# the manifest
# ===================


def test_type_patch_changes_the_entry(paths, tmp_path):
    _register(paths, tmp_path)
    _patch(paths, patch={"type": "tsv"})
    assert _manifest(paths)[-1]["type"] == "tsv"


def test_a_patch_is_not_a_registration(paths, tmp_path):
    _register(paths, tmp_path)
    ledger = len(_ledger(paths))
    _patch(paths, patch={"type": "tsv"})
    _patch(paths, patch={"file_name": "renamed.csv"})
    assert len(_manifest(paths)) == 1
    assert len(_ledger(paths)) == ledger
    assert len(_rows(paths)) == 1


def test_file_name_patch_moves_the_file(paths, tmp_path):
    _register(paths, tmp_path)
    old = _manifest(paths)[-1]
    _patch(paths, patch={"file_name": "renamed.csv"})
    entry = _manifest(paths)[-1]
    assert entry["file_home"].endswith(f"{os.sep}renamed.csv")
    assert entry["file"] == os.path.join(
        entry["file_home"], f"{old['fingerprint']}.{old['type']}"
    )
    assert os.path.exists(entry["file"])
    assert not os.path.exists(old["file_home"])


# ===================
# SQL
# ===================


def test_type_patch_updates_the_sql_row(paths, tmp_path):
    _register(paths, tmp_path)
    _patch(paths, patch={"type": "tsv"})
    entry = _manifest(paths)[-1]
    row = _row(paths, uuid=entry["uuid"])
    assert row["type"] == "tsv"
    assert json.loads(row["manifest_entry"]) == entry


def test_file_name_patch_updates_the_sql_row(paths, tmp_path):
    _register(paths, tmp_path)
    _patch(paths, patch={"file_name": "renamed.csv"})
    entry = _manifest(paths)[-1]
    row = _row(paths, uuid=entry["uuid"])
    assert row["file_home"] == entry["file_home"]
    assert row["file_path"] == entry["file"]
    assert json.loads(row["manifest_entry"]) == entry


def test_index_patches_that_entry_and_row_only(paths, tmp_path):
    _register(paths, tmp_path, n=0)
    _register(paths, tmp_path, n=1)
    second_row = _row(paths, uuid=_manifest(paths)[1]["uuid"])
    _patch(paths, patch={"type": "tsv"}, index=0)
    first, second = _manifest(paths)
    assert first["type"] == "tsv"
    assert second["type"] == "csv"
    assert _row(paths, uuid=first["uuid"])["type"] == "tsv"
    assert json.loads(_row(paths, uuid=first["uuid"])["manifest_entry"]) == first
    assert _row(paths, uuid=second["uuid"]) == second_row


def test_missing_row_is_not_inserted(plain, tmp_path):
    #
    # registered before SQL was on: no row, and a patch does not backfill
    #
    _register(plain, tmp_path)
    plain.config.add_to_config(section="listeners", key="groups", value="default, sql")
    _patch(plain, patch={"type": "tsv"})
    assert _manifest(plain)[-1]["type"] == "tsv"
    assert _rows(plain) == []


def test_sql_listener_skips_a_patch_with_no_entry(paths):
    listener = SqlFileListener(config=paths.config)
    listener.csvpaths = paths
    m = FileMetadata(paths.config)
    m.named_file_name = "orders"
    listener.metadata_patch(m)
    assert _rows(paths) == []


# ===================
# distribute_patch
# ===================


def test_the_registrar_patches_before_the_listeners(plain, tmp_path):
    _register(plain, tmp_path)
    rec = _Recording(plain.config)
    plain.file_manager.registrar.add_internal_listener(rec)
    _patch(plain, patch={"type": "tsv"})
    assert rec.patched == [_manifest(plain)[-1]]
    assert rec.patched[0]["type"] == "tsv"


def test_listeners_without_the_hook_are_skipped(plain, tmp_path):
    _register(plain, tmp_path)
    other = _UpdatesOnly(plain.config)
    plain.file_manager.registrar.add_internal_listener(other)
    _patch(plain, patch={"type": "tsv"})
    assert other.updates == 0
    assert _manifest(plain)[-1]["type"] == "tsv"


def test_a_failed_registrar_patch_raises_and_stops(plain, tmp_path):
    _register(plain, tmp_path)
    rec = _Recording(plain.config)
    plain.file_manager.registrar.add_internal_listener(rec)
    before = _manifest(plain)
    with pytest.raises(IndexError):
        _patch(plain, patch={"type": "tsv"}, index=5)
    assert rec.patched == []
    assert _manifest(plain) == before


def test_a_failed_registrar_patch_raises_under_a_no_raise_policy(plain, tmp_path):
    plain.config.add_to_config(section="errors", key="csvpaths", value=NO_RAISE_POLICY)
    _register(plain, tmp_path)
    with pytest.raises(IndexError):
        _patch(plain, patch={"type": "tsv"}, index=5)


@pytest.mark.parametrize("policy", ["raise, collect, print", NO_RAISE_POLICY])
def test_failed_sql_patch_raises_required_under_on(plain, tmp_path, policy):
    plain.config.add_to_config(section="errors", key="csvpaths", value=policy)
    _register(plain, tmp_path)
    plain.config.add_to_config(section="references", key="sql", value="on")
    after = _Recording(plain.config)
    reg = plain.file_manager.registrar
    reg.add_internal_listener(_FailingSqlPatch(config=plain.config))
    reg.add_internal_listener(after)
    with pytest.raises(RequiredListenerException, match="_FailingSqlPatch") as e:
        _patch(plain, patch={"type": "tsv"})
    assert str(e.value.__cause__) == "sql patch failed"
    assert after.patched == []
    #
    # the manifest is the source of truth and was written first
    #
    assert _manifest(plain)[-1]["type"] == "tsv"


def test_failed_sql_patch_is_logged_under_off_without_raise_policy(plain, tmp_path):
    plain.config.add_to_config(section="errors", key="csvpaths", value=NO_RAISE_POLICY)
    _register(plain, tmp_path)
    after = _Recording(plain.config)
    reg = plain.file_manager.registrar
    reg.add_internal_listener(_FailingSqlPatch(config=plain.config))
    reg.add_internal_listener(after)
    _patch(plain, patch={"type": "tsv"})
    assert len(after.patched) == 1


def test_failed_sql_patch_raises_under_off_with_raise_policy(plain, tmp_path):
    plain.config.add_to_config(
        section="errors", key="csvpaths", value="raise, collect, print"
    )
    _register(plain, tmp_path)
    plain.file_manager.registrar.add_internal_listener(
        _FailingSqlPatch(config=plain.config)
    )
    with pytest.raises(RuntimeError, match="sql patch failed"):
        _patch(plain, patch={"type": "tsv"})


# ===================
# blob patch error
# ===================


def test_blob_file_not_found_names_the_file(paths, monkeypatch):
    #
    # a stand-in Nos, so no blob store is touched: the new home "exists"
    # and the old file does not
    #
    class _Nos:
        def __init__(self, path) -> None:
            self.path = path

        def dir_exists(self) -> bool:
            return True

        def exists(self) -> bool:
            return False

    monkeypatch.setattr(file_registrar_module, "Nos", _Nos)
    old = "s3://bucket/orders/orders.csv/abc.csv"
    mani = [
        {
            "file": old,
            "file_home": "s3://bucket/orders/orders.csv",
            "fingerprint": "abc",
            "type": "csv",
        }
    ]
    with pytest.raises(ValueError, match=f"File not found: {old}"):
        paths.file_manager.registrar._patch_blob(mani, 0, {"file_name": "x.csv"})
