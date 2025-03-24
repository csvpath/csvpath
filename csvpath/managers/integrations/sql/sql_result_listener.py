from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from csvpath.managers.metadata import Metadata
from .sql_listener import SqlListener


class SqlResultListener(SqlListener):
    def __init__(self, config=None):
        SqlListener.__init__(self, config=config)
        self._instance_run = None

    @property
    def instance_run(self) -> Table:
        if self._instance_run is None:
            self._instance_run = self.tables.instance_run
        return self._instance_run

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        instance_run_data = {
            "uuid": mdata.uuid_string,
            "at": mdata.time,
            "group_run_uuid": mdata.named_paths_uuid_string,
            "instance_identity": mdata.instance_identity,
            "instance_index": mdata.instance_index,
            "instance_home": mdata.instance_home,
            "preceding_instance_identity": mdata.preceding_instance_identity,
            "actual_data_file": mdata.actual_data_file,
            "source_mode_preceding": "Y"
            if (
                mdata.source_mode_preceding is True
                or mdata.source_mode_preceding == "Y"
            )
            else "N",
            "valid": "Y" if (mdata.valid is True or mdata.valid == "Y") else "N",
            "completed": "Y"
            if (mdata.completed is True or mdata.completed == "Y")
            else "N",
            "files_expected": "Y"
            if (mdata.files_expected is True or mdata.files_expected == "Y")
            else "N",
            "error_count": mdata.error_count if mdata.error_count else 0,
            "number_of_files_expected": mdata.number_of_files_expected,
            "number_of_files_generated": mdata.number_of_files_generated,
            "lines_scanned": mdata.lines_scanned,
            "lines_total": mdata.lines_total,
            "lines_matched": mdata.lines_matched,
            "manifest_path": mdata.manifest_path,
        }
        self._upsert_instance_run(instance_run_data)

    def _upsert_instance_run(self, instance_run_data):
        with self.engine.connect() as conn:
            dialect = conn.dialect.name
            self.csvpaths.logger.info("Inserting run result metadata into %s", dialect)
            s = self._set(instance_run_data)
            if dialect in ["postgresql", "sqlite"]:
                ist = pg_insert if dialect == "postgresql" else sqlite_insert
                stmt = (
                    ist(self.instance_run)
                    .values(instance_run_data)
                    .on_conflict_do_update(index_elements=["uuid"], set_=s)
                )
            elif dialect == "mysql":
                stmt = (
                    mysql_insert(self.instance_run)
                    .values(instance_run_data)
                    .on_duplicate_key_update(self._set(instance_run_data))
                )
            elif dialect == "mssql":
                raise NotImplementedError("SQL Server support is not yet implemented.")
            else:
                raise ValueError(f"Unsupported database dialect: {dialect}")
            conn.execute(stmt)
            conn.commit()

    def _set(self, instance_run_data: dict) -> dict:
        return {
            "valid": "Y"
            if (instance_run_data["valid"] is True or instance_run_data["valid"] == "Y")
            else "N",
            "completed": "Y"
            if (
                instance_run_data["completed"] is True
                or instance_run_data["completed"] == "Y"
            )
            else "N",
            "error_count": instance_run_data["error_count"],
            "number_of_files_expected": instance_run_data["number_of_files_expected"],
            "number_of_files_generated": instance_run_data["number_of_files_generated"],
            "files_expected": instance_run_data["files_expected"],
            "lines_scanned": instance_run_data["lines_scanned"],
            "lines_total": instance_run_data["lines_total"],
            "lines_matched": instance_run_data["lines_matched"],
        }
