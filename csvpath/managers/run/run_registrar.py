import json
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from csvpath.util.exceptions import InputException
from csvpath.util.ledger_utility import LedgerUtility as leut
from ..listener import Listener
from ..registrar import Registrar
from ..metadata import Metadata
from .run_metadata import RunMetadata


class RunRegistrar(Registrar, Listener):
    def __init__(self, *, config=None, csvpaths=None):
        Registrar.__init__(self, csvpaths)
        Listener.__init__(self, csvpaths.config)
        self.type_name = "run"
        self.archive = self.csvpaths.config.archive_path
        self.csvpaths = csvpaths

    @property
    def manifest_path(self) -> str:
        return Nos(self.archive).join("manifest.json")

    @property
    def manifest(self) -> list:
        if not Nos(self.archive).exists():
            Nos(self.archive).makedirs()
        if not Nos(self.manifest_path).exists():
            with DataFileWriter(path=self.manifest_path) as file:
                json.dump([], file.sink, indent=2)
        with DataFileReader(self.manifest_path) as file:
            return json.load(file.source)

    def metadata_update(self, mdata: Metadata) -> None:
        m = {}
        m["time"] = f"{mdata.time}"
        m["run_uuid"] = mdata.run_uuid_string
        m["run_home"] = mdata.run_home
        m["identity"] = mdata.identity
        m["uuid"] = mdata.uuid_string
        m["named_paths_name"] = mdata.named_paths_name
        m["named_file_name"] = mdata.named_file_name
        mp = self.manifest_path
        m["manifest_path"] = mp
        #
        # adding to help make clearer where assets are for each
        # run. we now have the potential for much more flexibility.
        # it is possible that this is not enough identification.
        #
        m["archive_name"] = mdata.archive_name
        m["archive_path"] = mdata.archive_path
        # m["base_path"] = mdata.base_path
        m["named_files_root"] = mdata.named_files_root
        m["named_paths_root"] = mdata.named_paths_root
        m["template"] = mdata.template or ""
        #
        # the entry is written as the instance run starts. like every root
        # ledger entry, it has a status and a lifecycle; neither is implied
        # by absence.
        #
        m["status"] = Registrar.STARTED
        m["lifecycle"] = Registrar.ACTIVE
        mani = self.manifest
        mani.append(m)
        with DataFileWriter(path=mp) as file:
            json.dump(mani, file.sink, indent=2)
        #
        # for listeners that mirror the archive ledger (e.g. SQL)
        #
        mdata.ledger_entry = m
        mdata.ledger_index = len(mani) - 1

    def delete_named_results(self, *, name: str) -> None:
        """removes a named-results group's results, every run, as a whole.
        the removal is done by metadata_delete, via distribute_delete, so
        listeners that mirror the archive (e.g. SQL) can mark their
        copies."""
        if name is None:
            raise ValueError("Name cannot be None")
        if not isinstance(name, str):
            raise TypeError(f"Name must be a str, not {type(name).__name__}")
        if name.strip() == "":
            raise ValueError("Name cannot be empty")
        mdata = RunMetadata(self.csvpaths.config)
        mdata.named_paths_name = name
        self.distribute_delete(mdata)

    def metadata_delete(self, mdata: Metadata) -> None:
        """removes the group's results folder, then marks the group's
        archive ledger entries deleted, in place, and sets
        mdata.ledger_entries to them as written. the ledger keeps them: it
        is the history. this registrar is also the archive ledger's
        writer, so both happen here."""
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        name = mdata.named_paths_name
        home = Nos(self.archive).join(name)
        nos = Nos(home)
        if not nos.dir_exists():
            raise InputException(f"Named-results {name} not found")
        mdata.run_home = home
        mdata.change = {"time": mdata.time_string, "change": "delete"}
        nos.remove()
        mani = self.manifest
        marked = leut.mark_deleted(
            jdata=mani,
            name_key="named_paths_name",
            name=name,
            change=mdata.change,
            deleted=Registrar.DELETED,
        )
        if len(marked) > 0:
            with DataFileWriter(path=self.manifest_path) as file:
                json.dump(mani, file.sink, indent=2)
        mdata.ledger_entries = marked
