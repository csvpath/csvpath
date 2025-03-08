from sqlalchemy import create_engine, Table, Engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from .engine import Db
from .tables import Tables


class SqlResultListener(Listener):
    def __init__(self, config=None):
        Listener.__init__(self, config=config)
        self.csvpaths = None
        self._tables = None
        self._engine = None
        self._instance_run = None

    @property
    def tables(self) -> Tables:
        if self._tables is None:
            self._tables = Tables(self.config, engine=self.engine)
            self._tables.assure_tables()
        return self._tables

    @property
    def instance_run(self) -> Table:
        if self._instance_run is None:
            self._instance_run = self.tables.instance_run
        return self._instance_run

    @property
    def engine(self):
        if self._engine is None:
            self._engine = Db.get(self.config)
        return self._engine

    @engine.setter
    def engine(self, engine):
        self._engine = engine

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
            "source_mode_preceding": mdata.source_mode_preceding,
            "preceding_instance_identity": mdata.preceding_instance_identity,
            "actual_data_file": mdata.actual_data_file,
            "valid": "Y" if mdata.valid else "N",
            "completed": "Y" if mdata.completed else "N",
            "error_count": mdata.error_count if mdata.error_count else 0,
            "number_of_files_expected": mdata.number_of_files_expected,
            "number_of_files_generated": mdata.number_of_files_generated,
            "files_expected": "Y" if mdata.files_expected else "N",
            "lines_scanned": mdata.lines_scanned,
            "lines_total": mdata.lines_total,
            "lines_matched": mdata.lines_matched,
            "manifest_path": mdata.manifest_path,
        }
        self._upsert_instance_run(instance_run_data)

    def _upsert_instance_run(self, instance_run_data, *, dispose=True):
        with self.engine.connect() as conn:
            dialect = conn.dialect.name
            self.csvpaths.logger.info("Inserting run result metadata into %s", dialect)
            if dialect == "postgresql":
                # Postgres `ON CONFLICT` support
                stmt = (
                    pg_insert(self.instance_run)
                    .values(instance_run_data)
                    .on_conflict_do_update(
                        index_elements=["uuid"],  # Unique constraint column
                        set_={
                            "valid": instance_run_data["valid"],
                            "completed": instance_run_data["completed"],
                            "error_count": instance_run_data["error_count"],
                            "number_of_files_expected": instance_run_data[
                                "number_of_files_expected"
                            ],
                            "number_of_files_generated": instance_run_data[
                                "number_of_files_generated"
                            ],
                            "files_expected": instance_run_data["files_expected"],
                            "lines_scanned": instance_run_data["lines_scanned"],
                            "lines_total": instance_run_data["lines_total"],
                            "lines_matched": instance_run_data["lines_matched"],
                        },
                    )
                )
            elif dialect == "mysql":
                # MySQL `ON DUPLICATE KEY UPDATE` support
                stmt = (
                    mysql_insert(self.instance_run)
                    .values(instance_run_data)
                    .on_duplicate_key_update(
                        valid=instance_run_data["valid"],
                        completed=instance_run_data["completed"],
                        error_count=instance_run_data["error_count"],
                        number_of_files_expected=instance_run_data[
                            "number_of_files_expected"
                        ],
                        number_of_files_generated=instance_run_data[
                            "number_of_files_generated"
                        ],
                        files_expected=instance_run_data["files_expected"],
                        lines_scanned=instance_run_data["lines_scanned"],
                        lines_total=instance_run_data["lines_total"],
                        lines_matched=instance_run_data["lines_matched"],
                    )
                )
            elif dialect == "mssql":
                # SQL Server `MERGE` support (not implemented in this example)
                raise NotImplementedError("SQL Server support is not yet implemented.")
            elif dialect == "sqlite":
                stmt = (
                    sqlite_insert(self.instance_run)
                    .values(instance_run_data)
                    .on_conflict_do_update(
                        index_elements=["uuid"],  # Unique constraint column
                        set_={
                            "valid": instance_run_data["valid"],
                            "completed": instance_run_data["completed"],
                            "error_count": instance_run_data["error_count"],
                            "number_of_files_expected": instance_run_data[
                                "number_of_files_expected"
                            ],
                            "number_of_files_generated": instance_run_data[
                                "number_of_files_generated"
                            ],
                            "files_expected": instance_run_data["files_expected"],
                            "lines_scanned": instance_run_data["lines_scanned"],
                            "lines_total": instance_run_data["lines_total"],
                            "lines_matched": instance_run_data["lines_matched"],
                        },
                    )
                )
            else:
                raise ValueError(f"Unsupported database dialect: {dialect}")
            conn.execute(stmt)
            conn.commit()
        if dispose is True:
            self.engine.dispose()
