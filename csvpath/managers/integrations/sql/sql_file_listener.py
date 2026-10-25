import json
from sqlalchemy import Table, update
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
        self._named_file_ledger = None

    @property
    def named_file(self) -> Table:
        if self._named_file is None:
            self._named_file = self.tables.named_file
        return self._named_file

    @property
    def named_file_ledger(self) -> Table:
        if self._named_file_ledger is None:
            self._named_file_ledger = self.tables.named_file_ledger
        return self._named_file_ledger

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        #
        # mirror only what was actually written: the version by the
        # primary registrar, the ledger entry by FilesListener. None means
        # the write was skipped or failed.
        #
        if mdata.manifest_entry is None:
            self.csvpaths.logger.info(
                "No manifest entry for named-file %s; not writing a version to SQL",
                mdata.named_file_name,
            )
        else:
            self._write_named_file(mdata)
        if mdata.ledger_entry is None:
            self.csvpaths.logger.info(
                "No ledger entry for named-file %s; not writing a ledger row to SQL",
                mdata.named_file_name,
            )
        else:
            row = self._ledger_row(
                mdata=mdata,
                root_column="files_root",
                root=mdata.named_files_root,
                name_column="named_file_name",
                name=mdata.named_file_name,
            )
            self._upsert_ledger_row(table=self.named_file_ledger, row=row)

    def _write_named_file(self, mdata: Metadata) -> None:
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
            #
            # capturing cwd to db does not help. base_path is deprecated.
            #
            # "base_path": mdata.base_path,
            "base_path": "",
            "manifest_path": mdata.manifest_path,
            "template": mdata.template,
            "manifest_entry": json.dumps(mdata.manifest_entry),
            "manifest_index": mdata.manifest_index,
        }
        self._upsert_named_file(named_file_data)

    def metadata_patch(self, mdata: Metadata) -> None:
        """updates the row of the patched manifest entry. an update, not an
        upsert: a patch has too little to insert a row, and a missing row
        (e.g. registered before SQL was on) is not backfilled."""
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        entry = mdata.manifest_entry
        if entry is None:
            self.csvpaths.logger.info(
                "No patched manifest entry for named-file %s; not writing to SQL",
                mdata.named_file_name,
            )
            return
        values = {
            "type": entry.get("type"),
            "file_path": entry.get("file"),
            "file_home": entry.get("file_home"),
            "manifest_entry": json.dumps(entry),
        }
        count = self._update_named_file(uuid=entry["uuid"], values=values)
        if count == 0:
            self.csvpaths.logger.warning(
                "No SQL row for named-file %s entry %s; patch not written to SQL",
                mdata.named_file_name,
                entry["uuid"],
            )

    def _update_named_file(self, *, uuid: str, values: dict) -> int:
        try:
            return self._update_named_file_unreliably(uuid=uuid, values=values)
        except Exception:
            Updates(self.engine).do_updates()
            return self._update_named_file_unreliably(uuid=uuid, values=values)

    def _update_named_file_unreliably(self, *, uuid: str, values: dict) -> int:
        with self.engine.connect() as conn:
            self.csvpaths.logger.info(
                "Updating patched named-file metadata in %s", conn.dialect.name
            )
            stmt = (
                update(self.named_file)
                .where(self.named_file.c.uuid == uuid)
                .values(values)
            )
            result = conn.execute(stmt)
            conn.commit()
            return result.rowcount

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
            "manifest_entry": named_file_data.get("manifest_entry"),
            "manifest_index": named_file_data.get("manifest_index"),
        }
