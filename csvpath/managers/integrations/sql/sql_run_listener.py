import json
from sqlalchemy import Table
from csvpath.managers.metadata import Metadata
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
