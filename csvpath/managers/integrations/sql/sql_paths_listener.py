import json
from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from csvpath.managers.metadata import Metadata
from csvpath.managers.registrar import Registrar
from .sql_listener import SqlListener
from .updates import Updates


class SqlPathsListener(SqlListener):
    def __init__(self, config=None):
        SqlListener.__init__(self, config=config)
        self._named_paths = None
        self._named_paths_ledger = None

    @property
    def named_paths(self) -> Table:
        if self._named_paths is None:
            self._named_paths = self.tables.named_paths
        return self._named_paths

    @property
    def named_paths_ledger(self) -> Table:
        if self._named_paths_ledger is None:
            self._named_paths_ledger = self.tables.named_paths_ledger
        return self._named_paths_ledger

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        #
        # mirror only what was actually written: the version by the
        # primary registrar, the ledger entry by PathsListener. None means
        # the write was skipped (e.g. no version for an unchanged
        # fingerprint) or failed. an unchanged reload still has a ledger
        # entry.
        #
        if mdata.manifest_entry is None:
            self.csvpaths.logger.info(
                "No manifest entry for named-paths %s; not writing a version to SQL",
                mdata.named_paths_name,
            )
        else:
            self._write_named_paths(mdata)
        if mdata.ledger_entry is None:
            self.csvpaths.logger.info(
                "No ledger entry for named-paths %s; not writing a ledger row to SQL",
                mdata.named_paths_name,
            )
        else:
            row = self._ledger_row(
                mdata=mdata,
                root_column="paths_root",
                root=mdata.named_paths_root,
                name_column="paths_name",
                name=mdata.named_paths_name,
            )
            self._upsert_ledger_row(table=self.named_paths_ledger, row=row)

    def metadata_delete(self, mdata: Metadata) -> None:
        """marks the deleted versions' rows and the marked ledger
        entries' rows deleted"""
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        self._mark_deleted(
            mdata=mdata,
            version_table=self.named_paths,
            ledger_table=self.named_paths_ledger,
            name=mdata.named_paths_name,
        )

    def _write_named_paths(self, mdata: Metadata) -> None:
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
            #
            # base path is deprecated. it was a state leak.
            #
            # "base_path": mdata.base_path,
            "base_path": "",
            "manifest_path": mdata.manifest_path,
            "template": mdata.template,
            "manifest_entry": json.dumps(mdata.manifest_entry),
            "manifest_index": mdata.manifest_index,
            "lifecycle": Registrar.ACTIVE,
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
            "paths_root": named_paths_data["paths_root"],
            "paths_name": named_paths_data["paths_name"],
            "paths_home": named_paths_data["paths_home"],
            "group_file_path": named_paths_data["group_file_path"],
            "paths_count": named_paths_data["paths_count"],
            "ip_address": named_paths_data["ip_address"],
            "hostname": named_paths_data["hostname"],
            "username": named_paths_data["username"],
            "template": named_paths_data.get("template"),
            "manifest_entry": named_paths_data.get("manifest_entry"),
            "manifest_index": named_paths_data.get("manifest_index"),
            "lifecycle": named_paths_data.get("lifecycle"),
        }
