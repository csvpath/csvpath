"""The named-files and named-paths root ledgers are written whatever
[listeners] groups says (#442). FileRegistrar and PathsRegistrar run
FilesListener / PathsListener as built-in listeners: right after the
registrar itself, before internal and configured listeners.

Configs from before this change list them as default.file /
default.paths. A configured listener whose class is built in is skipped,
so the ledger is written once. A subclass is a different class and still
runs.

Every test uses its own roots under pytest's tmp_path.
"""

import json

import pytest

from csvpath.util.box import Box

from csvpath import CsvPaths
from csvpath.managers.files.files_listener import FilesListener
from csvpath.managers.listener import Listener
from csvpath.managers.paths.paths_listener import PathsListener
from csvpath.util.config import Config

FILES_LISTENER = "from csvpath.managers.files.files_listener import FilesListener"
PATHS_LISTENER = "from csvpath.managers.paths.paths_listener import PathsListener"


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
    if "default" in groups:
        #
        # as in configs from before the ledger writers were built in
        #
        p.config.add_to_config(
            section="listeners", key="default.file", value=FILES_LISTENER
        )
        p.config.add_to_config(
            section="listeners", key="default.paths", value=PATHS_LISTENER
        )
    p.config.add_to_config(section="sql", key="dialect", value="sqlite")
    p.config.add_to_config(
        section="sql",
        key="connection_string",
        value=f"sqlite:///{tmp_path / 'ledger.db'}",
    )
    return p


@pytest.fixture(autouse=True)
def _clear_engine():
    #
    # the SQL engine is cached in Box; the sql group tests use their own
    # database
    #
    def clear():
        box = Box()
        e = box.get(key=Box.SQL_ENGINE)
        if e is not None:
            e.dispose()
            box.remove(Box.SQL_ENGINE)

    clear()
    yield
    clear()


def _register(paths: CsvPaths, tmp_path, *, n: int = 0) -> None:
    data = tmp_path / f"orders_{n}.csv"
    data.write_text(f"id,amount\n{n},10\n", encoding="utf-8")
    paths.file_manager.add_named_file(name="orders", path=str(data))


def _load(paths: CsvPaths, tmp_path, *, statement: str = "$[*][yes()]") -> None:
    f = tmp_path / "orders.csvpaths"
    f.write_text(statement, encoding="utf-8")
    paths.paths_manager.add_named_paths_from_file(name="orders", file_path=str(f))


def _files_ledger(paths: CsvPaths) -> list:
    return paths.file_manager.files_root_manifest or []


def _paths_ledger(paths: CsvPaths) -> list:
    return paths.paths_manager.paths_root_manifest or []


class _SeesLedger(Listener):
    """records the ledger's length when it is updated"""

    def __init__(self, config, *, read) -> None:
        super().__init__(config)
        self.read = read
        self.lengths = []

    def metadata_update(self, mdata) -> None:
        self.lengths.append(len(self.read()))


class _MyFilesListener(FilesListener):
    """a customized ledger writer"""


# ===================
# built-in listeners
# ===================


def test_registrars_have_their_ledger_writers_built_in(tmp_path):
    p = _paths(tmp_path, groups="")
    files = p.file_manager.registrar._built_in_listeners
    paths = p.paths_manager.registrar._built_in_listeners
    assert [type(b) for b in files] == [FilesListener]
    assert [type(b) for b in paths] == [PathsListener]
    assert files[0].csvpaths is p
    assert files[0].config is p.config


def test_add_built_in_listener_rejects_none(tmp_path):
    p = _paths(tmp_path, groups="")
    with pytest.raises(ValueError):
        p.file_manager.registrar.add_built_in_listener(None)


# ===================
# the ledgers are written whatever groups says
# ===================


@pytest.mark.parametrize("groups", ["", "sql", "activation", "default"])
def test_files_ledger_has_one_entry_per_registration(tmp_path, groups):
    p = _paths(tmp_path, groups=groups)
    _register(p, tmp_path, n=0)
    _register(p, tmp_path, n=1)
    ledger = _files_ledger(p)
    assert [e["uuid"] for e in ledger] == [
        e["uuid"] for e in p.file_manager.get_manifest("orders")
    ]


@pytest.mark.parametrize("groups", ["", "sql", "activation", "default"])
def test_paths_ledger_has_one_entry_per_load(tmp_path, groups):
    p = _paths(tmp_path, groups=groups)
    _load(p, tmp_path, statement="$[*][yes()]")
    _load(p, tmp_path, statement="$[*][no()]")
    ledger = _paths_ledger(p)
    assert [e["uuid"] for e in ledger] == [
        e["uuid"] for e in p.paths_manager.get_manifest_for_name("orders")
    ]


def test_unchanged_reload_still_adds_a_paths_ledger_entry(tmp_path):
    #
    # as before; marking it is a later change
    #
    p = _paths(tmp_path, groups="")
    _load(p, tmp_path)
    _load(p, tmp_path)
    assert len(p.paths_manager.get_manifest_for_name("orders")) == 1
    assert len(_paths_ledger(p)) == 2


def test_built_in_listed_twice_still_writes_once(tmp_path):
    p = _paths(tmp_path, groups="default, mine")
    p.config.add_to_config(section="listeners", key="mine.file", value=FILES_LISTENER)
    p.config.add_to_config(
        section="listeners", key="mine.paths", value=PATHS_LISTENER
    )
    _register(p, tmp_path)
    _load(p, tmp_path)
    assert len(_files_ledger(p)) == 1
    assert len(_paths_ledger(p)) == 1


# ===================
# order: built-ins run before everything but the registrar
# ===================


def test_files_ledger_is_written_before_internal_listeners(tmp_path):
    p = _paths(tmp_path, groups="")
    probe = _SeesLedger(p.config, read=lambda: _files_ledger(p))
    p.file_manager.registrar.add_internal_listener(probe)
    _register(p, tmp_path, n=0)
    _register(p, tmp_path, n=1)
    assert probe.lengths == [1, 2]


def test_paths_ledger_is_written_before_internal_listeners(tmp_path):
    p = _paths(tmp_path, groups="")
    probe = _SeesLedger(p.config, read=lambda: _paths_ledger(p))
    p.paths_manager.registrar.add_internal_listener(probe)
    _load(p, tmp_path, statement="$[*][yes()]")
    _load(p, tmp_path, statement="$[*][no()]")
    assert probe.lengths == [1, 2]


# ===================
# configured duplicates are skipped, subclasses are not
# ===================


@pytest.mark.parametrize(
    "manager,cmd",
    [("file_manager", FILES_LISTENER), ("paths_manager", PATHS_LISTENER)],
)
def test_a_configured_built_in_is_skipped(tmp_path, manager, cmd):
    p = _paths(tmp_path, groups="")
    registrar = getattr(p, manager).registrar
    listeners = []
    registrar.load_additional_listener(cmd, listeners)
    registrar.load_additional_listener(cmd, listeners)
    assert listeners == []


def test_a_configured_subclass_still_runs(tmp_path):
    p = _paths(tmp_path, groups="")
    listeners = []
    p.file_manager.registrar.load_additional_listener(
        f"from {__name__} import _MyFilesListener", listeners
    )
    assert [type(lst) for lst in listeners] == [_MyFilesListener]


def test_other_configured_listeners_still_load(tmp_path):
    p = _paths(tmp_path, groups="")
    listeners = []
    p.file_manager.registrar.load_additional_listener(
        "from csvpath.managers.integrations.sql.sql_file_listener "
        "import SqlFileListener",
        listeners,
    )
    assert [type(lst).__name__ for lst in listeners] == ["SqlFileListener"]


# ===================
# patches
# ===================


def test_a_patch_leaves_the_files_ledger_alone(tmp_path):
    #
    # as before; patching the ledger entry is a later change
    #
    p = _paths(tmp_path, groups="")
    _register(p, tmp_path)
    before = json.dumps(_files_ledger(p))
    p.file_manager.registrar.patch_named_file(name="orders", patch={"type": "tsv"})
    assert json.dumps(_files_ledger(p)) == before


# ===================
# the default config
# ===================


def test_default_config_has_no_default_listener_lines():
    text = Config.DEFAULT_CONFIG
    assert "default.file" not in text
    assert "default.paths" not in text
    assert FILES_LISTENER not in text
    assert PATHS_LISTENER not in text
    assert "\ngroups = activation\n" in text
