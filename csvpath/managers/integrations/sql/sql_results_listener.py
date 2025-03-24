from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from csvpath.managers.metadata import Metadata
from .sql_listener import SqlListener


class SqlResultsListener(SqlListener):
    def __init__(self, config=None):
        SqlListener.__init__(self, config=config)
        self._group_run = None

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
            "by_line_run": "Y"
            if (mdata.by_line is True or mdata.by_line == "Y")
            else "N",
            "all_completed": "Y"
            if (mdata.all_completed is True or mdata.all_completed == "Y")
            else "N",
            "all_valid": "Y"
            if (mdata.all_valid is True or mdata.all_valid == "Y")
            else "N",
            "all_expected_files": "Y"
            if (mdata.all_expected_files is True or mdata.all_expected_files == "Y")
            else "N",
            "error_count": mdata.error_count or 0,
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

    def _upsert_named_paths_group_run(self, group_run_data):
        with self.engine.connect() as conn:
            dialect = conn.dialect.name
            self.csvpaths.logger.info(
                "Inserting group run results metadata into %s", dialect
            )
            if dialect in ["postgresql", "sqlite"]:
                ist = pg_insert if dialect == "postgresql" else sqlite_insert
                stmt = (
                    ist(self.group_run)
                    .values(group_run_data)
                    .on_conflict_do_update(
                        index_elements=["uuid"],
                        set_=self._set(group_run_data),
                    )
                )
            elif dialect == "mysql":
                stmt = (
                    mysql_insert(self.group_run)
                    .values(group_run_data)
                    .on_duplicate_key_update(self._set(group_run_data))
                )
            elif dialect == "mssql":
                raise NotImplementedError("SQL Server support is not yet implemented.")
            else:
                raise ValueError(f"Unsupported database dialect: {dialect}")
            conn.execute(stmt)
            conn.commit()

    def _set(self, group_run_data: dict) -> dict:
        return {
            "status": group_run_data["status"],
            "time_completed": group_run_data["time_completed"],
            "error_count": group_run_data["error_count"],
            "all_completed": "Y"
            if (
                group_run_data["all_completed"] is True
                or group_run_data["all_completed"] == "Y"
            )
            else "N",
            "all_valid": "Y"
            if (
                group_run_data["all_valid"] is True
                or group_run_data["all_valid"] == "Y"
            )
            else "N",
            "all_expected_files": "Y"
            if (
                group_run_data["all_expected_files"] is True
                or group_run_data["all_expected_files"] == "Y"
            )
            else "N",
        }
