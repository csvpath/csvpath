import json
from sqlalchemy import Table
from csvpath.managers.metadata import Metadata
from csvpath.managers.registrar import Registrar
from .sql_listener import SqlListener


class SqlRunListener(SqlListener):
    """mirrors the archive ledger, the archive's manifest.json, into the
    archive_ledger table. RunRegistrar writes one entry per instance run as
    it starts and sets mdata.ledger_entry and mdata.ledger_index; this
    listener stores exactly that entry and its position."""

    def __init__(self, config=None):
        SqlListener.__init__(self, config=config)
        self._archive_ledger = None

    @property
    def archive_ledger(self) -> Table:
        if self._archive_ledger is None:
            self._archive_ledger = self.tables.archive_ledger
        return self._archive_ledger

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        #
        # mirror only what was actually written. None means the ledger
        # write was skipped or failed.
        #
        if mdata.ledger_entry is None:
            self.csvpaths.logger.info(
                "No archive ledger entry for run %s; not writing a ledger row to SQL",
                mdata.run_home,
            )
            return
        row = self._archive_ledger_row(mdata)
        self._upsert_ledger_row(table=self.archive_ledger, row=row)

    def metadata_delete(self, mdata: Metadata) -> None:
        """marks the rows of a named-results delete: each archive ledger
        row with its entry as RunRegistrar marked it, and each entry's
        instance_run row (its uuid) and named_paths_group_run row (its
        run_uuid). updates, not upserts: a missing row (e.g. written
        before SQL was on) is not backfilled."""
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        runs = []
        for e in mdata.ledger_entries or []:
            values = {
                "ledger_entry": json.dumps(e),
                "status": e.get("status"),
                "lifecycle": e.get("lifecycle"),
            }
            self._mark(table=self.archive_ledger, uuid=e["uuid"], values=values)
            self._mark(
                table=self.tables.instance_run,
                uuid=e["uuid"],
                values={"lifecycle": Registrar.DELETED},
            )
            run_uuid = e.get("run_uuid")
            if run_uuid is not None and run_uuid not in runs:
                runs.append(run_uuid)
        for run_uuid in runs:
            self._mark(
                table=self.tables.group_run,
                uuid=run_uuid,
                values={"lifecycle": Registrar.DELETED},
            )

    def _mark(self, *, table: Table, uuid: str, values: dict) -> None:
        count = self._update_by_uuid(table=table, uuid=uuid, values=values)
        if count == 0:
            self.csvpaths.logger.warning(
                "No SQL row in %s for %s; delete not written to SQL",
                table.name,
                uuid,
            )

    def _archive_ledger_row(self, mdata: Metadata) -> dict:
        """the archive_ledger row for mdata's ledger entry. every value
        comes from mdata, as written by this update."""
        if mdata.ledger_entry is None or mdata.ledger_index is None:
            raise ValueError("Metadata has no ledger entry")
        root = mdata.archive_path
        if root is None or not isinstance(root, str) or root.strip() == "":
            raise ValueError("Archive path must be a non-empty str")
        entry = mdata.ledger_entry
        name = entry.get("named_paths_name")
        if name is None or not isinstance(name, str) or name.strip() == "":
            raise ValueError("Ledger entry has no named-paths name")
        return {
            "uuid": entry["uuid"],
            "at": mdata.time,
            "archive_root": root,
            "named_paths_name": name,
            "ledger_entry": json.dumps(entry),
            "ledger_index": mdata.ledger_index,
            "status": entry.get("status"),
            "lifecycle": entry.get("lifecycle"),
            "run_uuid": entry.get("run_uuid"),
        }
