from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from csvpath.managers.metadata import Metadata
from .sql_listener import SqlListener
from .updates import Updates


class SqlFileListener(SqlListener):
    def __init__(self, config=None):
        SqlListener.__init__(self, config=config)
        self._named_file = None

    @property
    def named_file(self) -> Table:
        if self._named_file is None:
            self._named_file = self.tables.named_file
        return self._named_file

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        named_file_data = {
            "uuid": mdata.uuid_string,
            "at": mdata.time,
            "named_file_name": mdata.named_file_name,
            "origin_path": mdata.origin_path,
            "name_home": mdata.name_home,
            "file_home": mdata.file_home,
            "file_path": mdata.file_path,
            "file_name": mdata.file_name,
            "mark": mdata.mark,
            "type": mdata.type,
            "file_size": mdata.file_size,
            "ip_address": mdata.ip_address,
            "hostname": mdata.hostname,
            "username": mdata.username,
            "files_root": mdata.named_files_root,
            "base_path": mdata.base_path,
            "manifest_path": mdata.manifest_path,
            "template": mdata.template,
        }
        self._upsert_named_file(named_file_data)

    def _upsert_named_file(self, named_file_data: dict):
        try:
            self._upsert_named_file_unreliably(named_file_data)
        except Exception:
            Updates(self.engine).do_updates()
            self._upsert_named_file_unreliably(named_file_data)

    def _upsert_named_file_unreliably(self, named_file_data: dict):
        with self.engine.connect() as conn:
            dialect = conn.dialect.name
            self.csvpaths.logger.info("Inserting named-file metadata into %s", dialect)
            stmt = None
            if dialect in ["postgresql", "sqlite"]:
                ist = pg_insert if dialect == "postgresql" else sqlite_insert
                stmt = (
                    ist(self.named_file)
                    .values(named_file_data)
                    .on_conflict_do_update(
                        index_elements=["uuid"], set_=self._set(named_file_data)
                    )
                )
            elif dialect == "mysql":
                stmt = (
                    mysql_insert(self.named_file)
                    .values(named_file_data)
                    .on_duplicate_key_update(self._set(named_file_data))
                )
            elif dialect == "mssql":
                raise NotImplementedError("SQL Server support is not yet implemented.")
            else:
                raise ValueError(f"Unsupported database dialect: {dialect}")
            conn.execute(stmt)
            conn.commit()

    def _set(self, named_file_data) -> dict:
        return {
            "files_root": named_file_data["files_root"],
            "file_home": named_file_data["file_home"],
            "file_path": named_file_data["file_path"],
            "file_name": named_file_data["file_name"],
            "mark": named_file_data["mark"],
            "type": named_file_data["type"],
            "file_size": named_file_data["file_size"],
            "ip_address": named_file_data["ip_address"],
            "hostname": named_file_data["hostname"],
            "username": named_file_data["username"],
            "template": named_file_data["template"]
            if "template" in named_file_data
            else None,
        }
