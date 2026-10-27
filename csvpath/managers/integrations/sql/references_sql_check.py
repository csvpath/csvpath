from sqlalchemy import inspect, text
from csvpath.util.config import ReferencesSql
from csvpath.util.config_exception import ConfigurationException
from .engine import Db
from .tables import Tables
from .updates import Updates


class ReferencesSqlCheck:
    """fail-fast checks for [references] sql = on | shadow. references that
    read from SQL depend on the SQL listeners having written every
    registration and run, so a configuration that cannot do that is an
    error, not a degraded mode.

    the checks need other settings and a database connection, so they are
    not part of Config.validate_config, which runs on every add_to_config.
    """

    #
    # listener type -> the SQL listener class that must be configured for it
    #
    LISTENERS = {
        "file": "SqlFileListener",
        "paths": "SqlPathsListener",
        "result": "SqlResultListener",
        "results": "SqlResultsListener",
    }
    TABLES = ["named_file", "named_paths", "instance_run", "named_paths_group_run"]
    ENTRY_COLUMN = "manifest_entry"
    #
    # only the appended-list manifests have positions. see
    # Metadata.manifest_index.
    #
    INDEX_COLUMN = "manifest_index"
    INDEX_COLUMN_TABLES = ["named_file", "named_paths"]
    #
    # the SQL reference source skips deleted versions by lifecycle
    #
    LIFECYCLE_COLUMN = "lifecycle"
    #
    # the root-ledger mirrors. they hold ledger_entry, not manifest_entry,
    # and were created complete, so only their existence and indexes are
    # checked.
    #
    LEDGER_TABLES = ["named_file_ledger", "named_paths_ledger"]

    @classmethod
    def check(cls, *, csvpaths) -> None:
        """raises a ConfigurationException listing every problem found.
        does nothing when [references] sql = off."""
        if csvpaths is None:
            raise ValueError("CsvPaths cannot be None")
        if csvpaths.config.references_sql == ReferencesSql.OFF.value:
            return
        problems = cls.problems(csvpaths=csvpaths)
        if len(problems) > 0:
            msg = "[references] sql = {} cannot be used: {}".format(
                csvpaths.config.references_sql, "; ".join(problems)
            )
            csvpaths.logger.error(msg)
            raise ConfigurationException(msg)

    @classmethod
    def problems(cls, *, csvpaths) -> list[str]:
        """returns the problems found, regardless of [references] sql"""
        if csvpaths is None:
            raise ValueError("CsvPaths cannot be None")
        config = csvpaths.config
        problems = []
        settings_missing = False
        dialect = config.get(section="sql", name="dialect")
        if not isinstance(dialect, str) or dialect.strip() == "":
            problems.append("[sql] dialect is not set")
            settings_missing = True
        conn = config.get(section="sql", name="connection_string")
        if not isinstance(conn, str) or conn.strip() == "":
            problems.append("[sql] connection_string is not set")
            settings_missing = True
        for listener_type, name in cls.LISTENERS.items():
            if not cls._has_listener(
                config=config, listener_type=listener_type, name=name
            ):
                problems.append(
                    f"{name} is not configured for {listener_type} events in [listeners] groups"
                )
        if settings_missing:
            return problems
        try:
            engine = Db.get(config)
            with engine.connect() as connection:
                connection.execute(text("select 1"))
        except Exception as ex:
            csvpaths.logger.exception(ex)
            problems.append(f"cannot connect to the [sql] database: {ex}")
            return problems
        problems += cls._table_problems(config=config, engine=engine)
        return problems

    @classmethod
    def _has_listener(cls, *, config, listener_type: str, name: str) -> bool:
        for cmd in config.additional_listeners(listener_type):
            if isinstance(cmd, str) and cmd.split()[-1] == name:
                return True
        return False

    @classmethod
    def _table_problems(cls, *, config, engine) -> list[str]:
        #
        # a new database has no tables until the first write, and one from
        # before manifest_entry, manifest_index or the indexes lacks them
        # until the first failed insert. the listeners fix both the same
        # way, so we do too before checking, rather than reporting a
        # database that is simply unused.
        #
        Tables(config, engine=engine).assure_tables()
        if len(cls._missing(engine=engine)) > 0:
            Updates(engine).do_updates()
        return cls._missing(engine=engine)

    @classmethod
    def _missing(cls, *, engine) -> list[str]:
        missing = []
        insp = inspect(engine)
        for table in cls.TABLES:
            if not insp.has_table(table):
                missing.append(f"table {table} does not exist")
                continue
            cols = [c["name"] for c in insp.get_columns(table)]
            if cls.ENTRY_COLUMN not in cols:
                missing.append(f"table {table} has no {cls.ENTRY_COLUMN} column")
            if table in cls.INDEX_COLUMN_TABLES and cls.INDEX_COLUMN not in cols:
                missing.append(f"table {table} has no {cls.INDEX_COLUMN} column")
            if table in cls.INDEX_COLUMN_TABLES and cls.LIFECYCLE_COLUMN not in cols:
                missing.append(f"table {table} has no {cls.LIFECYCLE_COLUMN} column")
            missing += cls._missing_indexes(insp=insp, table=table)
        for table in cls.LEDGER_TABLES:
            if not insp.has_table(table):
                missing.append(f"table {table} does not exist")
                continue
            missing += cls._missing_indexes(insp=insp, table=table)
        return missing

    @classmethod
    def _missing_indexes(cls, *, insp, table: str) -> list[str]:
        indexes = [i["name"] for i in insp.get_indexes(table)]
        return [
            f"table {table} has no index {name}"
            for name in Tables.INDEXES[table]
            if name not in indexes
        ]
