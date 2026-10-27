"""[references] sql = off | on | shadow: the setting, the fail-fast checks
for on and shadow (ReferencesSqlCheck), and the raise policy for SQL
listener failures.

Raise policy: when references rely on SQL (on), a failed SQL write always
raises, as a RequiredListenerException that do_i_raise(ex) raises whatever
the error policy says. With off or shadow, SQL is data exhaust and failures
follow the CsvPaths error policy, csvpaths.ecoms.do_i_raise(). Other
listeners keep logging failures without raising.

Every database is a SQLite file under pytest's tmp_path. The engine is
cached in Box, so each test clears it before and after.
"""

import pytest
from sqlalchemy import Column, MetaData, Table, inspect

from csvpath import CsvPaths
from csvpath.managers.errors.error_comms import ErrorCommunications
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.integrations.sql.references_sql_check import (
    ReferencesSqlCheck,
)
from csvpath.managers.integrations.sql.sql_listener import SqlListener
from csvpath.managers.integrations.sql.tables import Tables
from csvpath.managers.listener import Listener
from csvpath.managers.registrar import Registrar
from csvpath.util.box import Box
from csvpath.util.config import ReferencesSql
from csvpath.util.config_exception import ConfigurationException
from csvpath.util.exceptions import CsvPathsException, RequiredListenerException

RAISE_POLICY = "raise, collect, print"
NO_RAISE_POLICY = "collect, print"


class _NoopSql(SqlListener):
    """SqlListener is abstract; this one only adds a no-op metadata_update"""

    def metadata_update(self, mdata) -> None: ...


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


@pytest.fixture
def paths(tmp_path):
    #
    # a CsvPaths with the default and sql listeners on and a working
    # SQLite database. inputs and archive are under tmp_path too, for the
    # tests that register files.
    #
    _clear_engine()
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
    p.config.add_to_config(section="listeners", key="groups", value="default, sql")
    p.config.add_to_config(section="sql", key="dialect", value="sqlite")
    p.config.add_to_config(
        section="sql",
        key="connection_string",
        value=f"sqlite:///{tmp_path / 'refs.db'}",
    )
    yield p
    _clear_engine()


def _set_mode(paths: CsvPaths, mode: str) -> None:
    paths.config.add_to_config(section="references", key="sql", value=mode)


def _break_connection(paths: CsvPaths, tmp_path) -> None:
    #
    # sqlite cannot create a database file in a directory that does not
    # exist
    #
    _clear_engine()
    paths.config.add_to_config(
        section="sql",
        key="connection_string",
        value=f"sqlite:///{tmp_path / 'no_such_dir' / 'refs.db'}",
    )


# ===================
# the setting
# ===================


class TestReferencesSqlSetting:
    def test_defaults_to_off(self, paths):
        assert paths.config.references_sql == ReferencesSql.OFF.value

    def test_blank_is_off(self, paths):
        _set_mode(paths, "")
        assert paths.config.references_sql == ReferencesSql.OFF.value

    @pytest.mark.parametrize("mode", ["off", "on", "shadow"])
    def test_accepts_each_mode(self, paths, mode):
        _set_mode(paths, mode)
        assert paths.config.references_sql == mode

    def test_case_and_space_insensitive(self, paths):
        _set_mode(paths, " Shadow ")
        assert paths.config.references_sql == ReferencesSql.SHADOW.value

    def test_bad_value_raises_on_validation(self, paths):
        with pytest.raises(ConfigurationException):
            _set_mode(paths, "maybe")

    def test_list_value_raises_on_validation(self, paths):
        with pytest.raises(ConfigurationException):
            _set_mode(paths, "on, shadow")


# ===================
# ReferencesSqlCheck
# ===================


class TestReferencesSqlCheck:
    def test_none_csvpaths_raises(self):
        with pytest.raises(ValueError):
            ReferencesSqlCheck.check(csvpaths=None)
        with pytest.raises(ValueError):
            ReferencesSqlCheck.problems(csvpaths=None)

    @pytest.mark.parametrize("mode", ["on", "shadow"])
    def test_good_config_passes(self, paths, mode):
        _set_mode(paths, mode)
        assert ReferencesSqlCheck.problems(csvpaths=paths) == []
        ReferencesSqlCheck.check(csvpaths=paths)

    def test_good_config_leaves_the_tables_in_place(self, paths):
        _set_mode(paths, "on")
        ReferencesSqlCheck.check(csvpaths=paths)
        listener = _NoopSql(config=paths.config)
        insp = inspect(listener.engine)
        for table in ReferencesSqlCheck.TABLES:
            assert insp.has_table(table), table

    def test_off_does_nothing_even_when_misconfigured(self, paths):
        paths.config.add_to_config(section="sql", key="dialect", value="")
        paths.config.add_to_config(section="listeners", key="groups", value="default")
        ReferencesSqlCheck.check(csvpaths=paths)

    def test_missing_dialect(self, paths):
        _set_mode(paths, "on")
        paths.config.add_to_config(section="sql", key="dialect", value="")
        assert ReferencesSqlCheck.problems(csvpaths=paths) == [
            "[sql] dialect is not set"
        ]

    def test_missing_connection_string(self, paths):
        _set_mode(paths, "on")
        paths.config.add_to_config(section="sql", key="connection_string", value="")
        assert ReferencesSqlCheck.problems(csvpaths=paths) == [
            "[sql] connection_string is not set"
        ]

    def test_missing_sql_listeners(self, paths):
        _set_mode(paths, "on")
        paths.config.add_to_config(section="listeners", key="groups", value="default")
        problems = ReferencesSqlCheck.problems(csvpaths=paths)
        assert len(problems) == len(ReferencesSqlCheck.LISTENERS) == 5
        for name in ReferencesSqlCheck.LISTENERS.values():
            assert any(name in p for p in problems), name

    def test_one_missing_sql_listener(self, paths):
        #
        # a custom group that has all but SqlResultsListener
        #
        _set_mode(paths, "on")
        for t, name in [
            ("file", "SqlFileListener"),
            ("paths", "SqlPathsListener"),
            ("result", "SqlResultListener"),
            ("run", "SqlRunListener"),
        ]:
            module = {
                "file": "sql_file_listener",
                "paths": "sql_paths_listener",
                "result": "sql_result_listener",
                "run": "sql_run_listener",
            }[t]
            paths.config.add_to_config(
                section="listeners",
                key=f"mysql.{t}",
                value=f"from csvpath.managers.integrations.sql.{module} import {name}",
            )
        paths.config.add_to_config(
            section="listeners", key="groups", value="default, mysql"
        )
        problems = ReferencesSqlCheck.problems(csvpaths=paths)
        assert len(problems) == 1
        assert "SqlResultsListener" in problems[0]

    def test_unreachable_database(self, paths, tmp_path):
        _set_mode(paths, "on")
        _break_connection(paths, tmp_path)
        problems = ReferencesSqlCheck.problems(csvpaths=paths)
        assert len(problems) == 1
        assert problems[0].startswith("cannot connect to the [sql] database")

    def test_check_lists_every_problem_in_one_exception(self, paths):
        _set_mode(paths, "shadow")
        paths.config.add_to_config(section="sql", key="dialect", value="")
        paths.config.add_to_config(section="listeners", key="groups", value="default")
        with pytest.raises(ConfigurationException) as e:
            ReferencesSqlCheck.check(csvpaths=paths)
        msg = str(e.value)
        assert "[references] sql = shadow" in msg
        assert "[sql] dialect is not set" in msg
        for name in ReferencesSqlCheck.LISTENERS.values():
            assert name in msg, name

    def test_database_from_before_manifest_entry_is_updated(self, paths):
        _set_mode(paths, "on")
        current = Tables(paths.config)
        old = MetaData()
        for t in [
            current.group_run,
            current.instance_run,
            current.named_file,
            current.named_paths,
        ]:
            cols = [
                Column(c.name, c.type, primary_key=c.primary_key, nullable=c.nullable)
                for c in t.columns
                if c.name != "manifest_entry"
            ]
            Table(t.name, old, *cols)
        engine = _NoopSql(config=paths.config).engine
        old.create_all(engine)
        assert ReferencesSqlCheck.problems(csvpaths=paths) == []
        insp = inspect(engine)
        for table in ReferencesSqlCheck.TABLES:
            cols = [c["name"] for c in insp.get_columns(table)]
            assert "manifest_entry" in cols, table


# ===================
# raise policy
# ===================


def _sql_listener(paths: CsvPaths) -> SqlListener:
    listener = _NoopSql(config=paths.config)
    listener.csvpaths = paths
    return listener


class TestUpdateIsRequired:
    def test_listener_default_is_false(self, paths):
        class _Plain(Listener):
            def metadata_update(self, mdata) -> None: ...

        assert _Plain(paths.config).update_is_required() is False

    def test_sql_on_is_required(self, paths):
        _set_mode(paths, "on")
        assert _sql_listener(paths).update_is_required() is True

    @pytest.mark.parametrize("mode", ["off", "shadow"])
    def test_sql_off_and_shadow_are_not_required(self, paths, mode):
        _set_mode(paths, mode)
        paths.config.add_to_config(
            section="errors", key="csvpaths", value=RAISE_POLICY
        )
        assert _sql_listener(paths).update_is_required() is False


class TestRaiseOnUpdateError:
    def test_listener_default_is_false(self, paths):
        class _Plain(Listener):
            def metadata_update(self, mdata) -> None: ...

        assert _Plain(paths.config).raise_on_update_error() is False

    @pytest.mark.parametrize("policy", [RAISE_POLICY, NO_RAISE_POLICY])
    def test_on_always_raises(self, paths, policy):
        _set_mode(paths, "on")
        paths.config.add_to_config(section="errors", key="csvpaths", value=policy)
        assert _sql_listener(paths).raise_on_update_error() is True

    @pytest.mark.parametrize("mode", ["off", "shadow"])
    def test_off_and_shadow_follow_the_policy(self, paths, mode):
        _set_mode(paths, mode)
        paths.config.add_to_config(
            section="errors", key="csvpaths", value=RAISE_POLICY
        )
        assert _sql_listener(paths).raise_on_update_error() is True
        paths.config.add_to_config(
            section="errors", key="csvpaths", value=NO_RAISE_POLICY
        )
        assert _sql_listener(paths).raise_on_update_error() is False

    def test_no_csvpaths_off_is_false(self, paths):
        listener = _NoopSql(config=paths.config)
        assert listener.raise_on_update_error() is False

    def test_no_csvpaths_on_is_true(self, paths):
        _set_mode(paths, "on")
        listener = _NoopSql(config=paths.config)
        assert listener.raise_on_update_error() is True


class _Registrar(Registrar, Listener):
    """a registrar with no additional listeners configured for its type"""

    def __init__(self, csvpaths) -> None:
        Registrar.__init__(self, csvpaths)
        Listener.__init__(self, csvpaths.config)
        self.type_name = "no_such_listener_type"

    def metadata_update(self, mdata) -> None: ...


class _FailingSql(SqlListener):
    def metadata_update(self, mdata) -> None:
        raise RuntimeError("sql write failed")


class _FailingPlain(Listener):
    def metadata_update(self, mdata) -> None:
        raise RuntimeError("integration failed")


class _Recording(Listener):
    def __init__(self, config) -> None:
        super().__init__(config)
        self.updates = 0

    def metadata_update(self, mdata) -> None:
        self.updates += 1


class TestDistributeUpdate:
    def _registrar(self, paths, *listeners) -> _Registrar:
        reg = _Registrar(paths)
        for lst in listeners:
            reg.add_internal_listener(lst)
        return reg

    @pytest.mark.parametrize("policy", [RAISE_POLICY, NO_RAISE_POLICY])
    def test_failing_sql_listener_raises_required_under_on(self, paths, policy):
        _set_mode(paths, "on")
        paths.config.add_to_config(section="errors", key="csvpaths", value=policy)
        after = _Recording(paths.config)
        reg = self._registrar(paths, _FailingSql(config=paths.config), after)
        with pytest.raises(RequiredListenerException, match="_FailingSql") as e:
            reg.distribute_update(FileMetadata(paths.config))
        #
        # chained to what the listener raised
        #
        assert isinstance(e.value.__cause__, RuntimeError)
        assert str(e.value.__cause__) == "sql write failed"
        #
        # raising stops the listeners after it for this update
        #
        assert after.updates == 0

    def test_failing_sql_listener_logged_under_off_without_raise_policy(self, paths):
        paths.config.add_to_config(
            section="errors", key="csvpaths", value=NO_RAISE_POLICY
        )
        after = _Recording(paths.config)
        reg = self._registrar(paths, _FailingSql(config=paths.config), after)
        reg.distribute_update(FileMetadata(paths.config))
        assert after.updates == 1

    def test_failing_sql_listener_raises_under_off_with_raise_policy(self, paths):
        paths.config.add_to_config(
            section="errors", key="csvpaths", value=RAISE_POLICY
        )
        reg = self._registrar(paths, _FailingSql(config=paths.config))
        #
        # the original exception, not a required one: the policy applies
        #
        with pytest.raises(RuntimeError, match="sql write failed") as e:
            reg.distribute_update(FileMetadata(paths.config))
        assert not isinstance(e.value, RequiredListenerException)

    @pytest.mark.parametrize("mode", ["off", "on", "shadow"])
    def test_failing_plain_listener_is_still_only_logged(self, paths, mode):
        _set_mode(paths, mode)
        paths.config.add_to_config(
            section="errors", key="csvpaths", value=RAISE_POLICY
        )
        after = _Recording(paths.config)
        reg = self._registrar(paths, _FailingPlain(paths.config), after)
        reg.distribute_update(FileMetadata(paths.config))
        assert after.updates == 1

    def test_listener_without_the_hook_is_only_logged(self, paths):
        class _DuckTyped:
            config = paths.config

            def metadata_update(self, mdata) -> None:
                raise RuntimeError("duck failed")

        after = _Recording(paths.config)
        reg = self._registrar(paths, _DuckTyped(), after)
        reg.distribute_update(FileMetadata(paths.config))
        assert after.updates == 1


# ===================
# do_i_raise(ex)
# ===================


class _StubCsvPath:
    """stands in for a CsvPath whose validation-mode says not to raise"""

    raise_validation_errors = False


class TestDoIRaise:
    def test_required_raises_without_raise_policy(self, paths):
        paths.config.add_to_config(
            section="errors", key="csvpaths", value=NO_RAISE_POLICY
        )
        assert paths.ecoms.do_i_raise() is False
        assert paths.ecoms.do_i_raise(RequiredListenerException("x")) is True

    def test_required_beats_a_csvpath_override(self):
        stub = _StubCsvPath()
        ecoms = ErrorCommunications(csvpath=stub)
        assert ecoms.do_i_raise() is False
        assert ecoms.do_i_raise(RequiredListenerException("x")) is True

    @pytest.mark.parametrize(
        "ex", [None, RuntimeError("x"), CsvPathsException("x"), ValueError("x")]
    )
    def test_other_exceptions_follow_the_policy(self, paths, ex):
        paths.config.add_to_config(
            section="errors", key="csvpaths", value=NO_RAISE_POLICY
        )
        assert paths.ecoms.do_i_raise(ex) is False
        paths.config.add_to_config(
            section="errors", key="csvpaths", value=RAISE_POLICY
        )
        assert paths.ecoms.do_i_raise(ex) is True

    def test_required_is_not_caught_by_narrow_handlers(self):
        #
        # add_named_paths_from_json and set_named_files_from_json catch
        # only these types; a required failure must pass through them
        #
        assert not issubclass(
            RequiredListenerException, (OSError, ValueError, TypeError)
        )


# ===================
# end to end: registrations and runs with a broken SQL connection
# ===================


def _data_file(tmp_path) -> str:
    data = tmp_path / "orders.csv"
    data.write_text("id,amount\n1,10\n", encoding="utf-8")
    return str(data)


def _paths_file(tmp_path) -> str:
    f = tmp_path / "orders.csvpaths"
    f.write_text("$[*][yes()]", encoding="utf-8")
    return str(f)


def _no_raise_policy(paths: CsvPaths) -> None:
    paths.config.add_to_config(
        section="errors", key="csvpaths", value=NO_RAISE_POLICY
    )


def _register(paths: CsvPaths, tmp_path) -> None:
    #
    # registered while the connection works, so a later run is the only
    # thing that meets the broken one
    #
    paths.file_manager.add_named_file(name="orders", path=_data_file(tmp_path))
    paths.paths_manager.add_named_paths_from_file(
        name="orders", file_path=_paths_file(tmp_path)
    )


def test_file_registration_raises_under_on_when_sql_write_fails(paths, tmp_path):
    _set_mode(paths, "on")
    _no_raise_policy(paths)
    _break_connection(paths, tmp_path)
    with pytest.raises(RequiredListenerException):
        paths.file_manager.add_named_file(name="orders", path=_data_file(tmp_path))


def test_paths_registration_raises_under_on_when_sql_write_fails(paths, tmp_path):
    _set_mode(paths, "on")
    _no_raise_policy(paths)
    _break_connection(paths, tmp_path)
    with pytest.raises(RequiredListenerException):
        paths.paths_manager.add_named_paths_from_file(
            name="orders", file_path=_paths_file(tmp_path)
        )


class FailingResultSql(SqlListener):
    """loaded from [listeners] as a result listener. it fails only the
    instance start update, so the run gets past start_run and the failure
    reaches only the handlers around each csvpath instance. failing the
    completion update too would raise from save(), where nothing catches
    it, and hide whether those handlers let it through."""

    def metadata_update(self, mdata) -> None:
        if mdata.time_completed is None:
            raise RuntimeError("instance_run write failed")


def _fail_instance_writes(paths: CsvPaths) -> None:
    paths.config.add_to_config(
        section="listeners",
        key="failing.result",
        value="from tests.csvpaths.managers.test_references_sql_config import FailingResultSql",
    )
    paths.config.add_to_config(
        section="listeners", key="groups", value="default, sql, failing"
    )


@pytest.mark.parametrize(
    "method", ["collect_paths", "fast_forward_paths", "next_paths"]
)
def test_run_raises_under_on_when_instance_sql_write_fails(paths, tmp_path, method):
    _set_mode(paths, "on")
    _no_raise_policy(paths)
    _register(paths, tmp_path)
    _fail_instance_writes(paths)
    with pytest.raises(RequiredListenerException):
        r = getattr(paths, method)(pathsname="orders", filename="orders")
        if method == "next_paths":
            for _ in r:
                ...


@pytest.mark.parametrize(
    "method", ["collect_by_line", "fast_forward_by_line", "next_by_line"]
)
def test_by_line_raises_under_on_when_instance_sql_write_fails(
    paths, tmp_path, method
):
    _set_mode(paths, "on")
    _no_raise_policy(paths)
    _register(paths, tmp_path)
    _fail_instance_writes(paths)
    with pytest.raises(RequiredListenerException):
        r = getattr(paths, method)(pathsname="orders", filename="orders")
        if method == "next_by_line":
            for _ in r:
                ...


def test_start_run_raises_under_on_when_sql_write_fails(paths, tmp_path):
    _set_mode(paths, "on")
    _no_raise_policy(paths)
    _register(paths, tmp_path)
    _break_connection(paths, tmp_path)
    with pytest.raises(RequiredListenerException):
        paths.collect_paths(pathsname="orders", filename="orders")


@pytest.mark.parametrize("method", ["collect_paths", "collect_by_line"])
def test_run_continues_under_off_when_instance_sql_write_fails(
    paths, tmp_path, method
):
    _no_raise_policy(paths)
    _register(paths, tmp_path)
    _fail_instance_writes(paths)
    getattr(paths, method)(pathsname="orders", filename="orders")
    results = paths.results_manager.get_named_results("orders")
    assert len(results) == 1
