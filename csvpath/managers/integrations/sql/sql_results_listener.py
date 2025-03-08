from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from .engine import Db
from .tables import Tables


class SqlResultsListener(Listener):
    def __init__(self, config=None):
        Listener.__init__(self, config=config)
        self.csvpaths = None
        self._tables = None
        self._engine = None
        self._group_run = None

    @property
    def tables(self) -> Tables:
        if self._tables is None:
            self._tables = Tables(self.config, engine=self.engine)
            self._tables.assure_tables()
        return self._tables

    @property
    def engine(self):
        if self._engine is None:
            self._engine = Db.get(self.config)
        return self._engine

    @engine.setter
    def engine(self, engine):
        self._engine = engine

    @property
    def group_run(self) -> Table:
        if self._group_run is None:
            self._group_run = self.tables.group_run
        return self._group_run

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")

        group_run_data = {
            "uuid": mdata.uuid_string,
            "at": mdata.time,
            "time_completed": mdata.time_completed,
            "status": mdata.status,
            "by_line_run": "Y" if mdata.by_line else "N",
            "all_completed": "Y" if mdata.all_completed else "N",
            "all_valid": "Y" if mdata.all_valid else "N",
            "error_count": mdata.error_count or 0,
            "all_expected_files": "Y" if mdata.all_expected_files else "N",
            "archive_name": mdata.archive_name,
            "run_home": mdata.run_home,
            "named_results_name": mdata.named_results_name,
            "named_paths_uuid": mdata.named_paths_uuid,
            "named_paths_name": mdata.named_paths_name,
            "named_paths_home": f"{mdata.named_paths_root}/{mdata.named_paths_name}",
            "named_file_uuid": mdata.named_file_uuid,
            "named_file_name": mdata.named_file_name,
            "named_file_home": f"{mdata.named_files_root}/{mdata.named_file_name}",
            "named_file_path": mdata.named_file_path,
            "named_file_size": mdata.named_file_size or -1,
            "named_file_last_change": mdata.named_file_last_change,
            "named_file_fingerprint": mdata.named_file_fingerprint,
            "hostname": mdata.hostname,
            "username": mdata.username,
            "ip_address": mdata.ip_address,
            "manifest_path": mdata.manifest_path,
        }
        self._upsert_named_paths_group_run(group_run_data)

    def _upsert_named_paths_group_run(self, group_run_data, *, dispose=True):
        with self.engine.connect() as conn:
            dialect = conn.dialect.name
            self.csvpaths.logger.info(
                "Inserting group run results metadata into %s", dialect
            )
            if dialect == "postgresql":
                stmt = (
                    pg_insert(self.group_run)
                    .values(group_run_data)
                    .on_conflict_do_update(
                        index_elements=["uuid"],
                        set_={
                            "status": group_run_data["status"],
                            "time_completed": group_run_data["time_completed"],
                            "all_completed": group_run_data["all_completed"],
                            "all_valid": group_run_data["all_valid"],
                            "error_count": group_run_data["error_count"],
                            "all_expected_files": group_run_data["all_expected_files"],
                        },
                    )
                )
            elif dialect == "sqlite":
                stmt = (
                    sqlite_insert(self.group_run)
                    .values(group_run_data)
                    .on_conflict_do_update(
                        index_elements=["uuid"],
                        set_={
                            "status": group_run_data["status"],
                            "time_completed": group_run_data["time_completed"],
                            "all_completed": group_run_data["all_completed"],
                            "all_valid": group_run_data["all_valid"],
                            "error_count": group_run_data["error_count"],
                            "all_expected_files": group_run_data["all_expected_files"],
                        },
                    )
                )
            elif dialect == "mysql":
                stmt = (
                    mysql_insert(self.group_run)
                    .values(group_run_data)
                    .on_duplicate_key_update(
                        status=group_run_data["status"],
                        time_completed=group_run_data["time_completed"],
                        all_completed=group_run_data["all_completed"],
                        all_valid=group_run_data["all_valid"],
                        error_count=group_run_data["error_count"],
                        all_expected_files=group_run_data["all_expected_files"],
                    )
                )
            elif dialect == "mssql":
                raise NotImplementedError(
                    "SQL Server support for named_paths_group_run is not yet implemented."
                )
            else:
                raise ValueError(f"Unsupported database dialect: {dialect}")
            conn.execute(stmt)
            conn.commit()
        if dispose is True:
            self.engine.dispose()
