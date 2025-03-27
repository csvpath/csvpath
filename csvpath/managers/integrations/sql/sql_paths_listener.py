from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from csvpath.managers.metadata import Metadata
from .sql_listener import SqlListener
from .updates import Updates


class SqlPathsListener(SqlListener):
    def __init__(self, config=None):
        SqlListener.__init__(self, config=config)
        self._named_paths = None

    @property
    def named_paths(self) -> Table:
        if self._named_paths is None:
            self._named_paths = self.tables.named_paths
        return self._named_paths

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        named_paths_data = {
            "uuid": mdata.uuid_string,
            "at": mdata.time,
            "paths_root": mdata.named_paths_root,
            "paths_name": mdata.named_paths_name,
            "paths_home": mdata.named_paths_home,
            "group_file_path": mdata.group_file_path,
            "paths_count": mdata.named_paths_count,
            "ip_address": mdata.ip_address,
            "hostname": mdata.hostname,
            "username": mdata.username,
            "base_path": mdata.base_path,
            "manifest_path": mdata.manifest_path,
            "template": mdata.template,
        }
        self._upsert_named_paths(named_paths_data)

    def _upsert_named_paths(self, named_paths_data: dict):
        try:
            self._upsert_named_paths_unreliably(named_paths_data)
        except Exception:
            Updates(self.engine).do_updates()
            self._upsert_named_paths_unreliably(named_paths_data)

    def _upsert_named_paths_unreliably(self, named_paths_data: dict):
        with self.engine.connect() as conn:
            dialect = conn.dialect.name
            self.csvpaths.logger.info("Inserting named-paths metadata into %s", dialect)
            stmt = None
            if dialect in ["postgresql", "sqlite"]:
                ist = pg_insert if dialect == "postgresql" else sqlite_insert
                stmt = (
                    ist(self.named_paths)
                    .values(named_paths_data)
                    .on_conflict_do_update(
                        index_elements=["uuid"], set_=self._set(named_paths_data)
                    )
                )
            elif dialect == "mysql":
                stmt = (
                    mysql_insert(self.named_paths)
                    .values(named_paths_data)
                    .on_duplicate_key_update(self._set(named_paths_data))
                )
            elif dialect == "mssql":
                raise NotImplementedError("SQL Server support is not yet implemented.")
            else:
                raise ValueError(f"Unsupported database dialect: {dialect}")
            conn.execute(stmt)
            conn.commit()

    def _set(self, named_paths_data) -> dict:
        return {
            "paths_root": named_paths_data["paths_name"],
            "paths_name": named_paths_data["paths_name"],
            "paths_home": named_paths_data["paths_home"],
            "group_file_path": named_paths_data["group_file_path"],
            "paths_count": named_paths_data["paths_count"],
            "ip_address": named_paths_data["ip_address"],
            "hostname": named_paths_data["hostname"],
            "username": named_paths_data["username"],
            "template": named_paths_data.get("template"),
        }
