import json
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata

#
# TODO: not using intermediary
#


class FilesListener(Listener):  # Registrar,
    """@private
    this listener tracks all named-file arrivals"""

    def __init__(self, *, config=None, csvpaths=None):
        #
        # FileRegistrar is the primary listener. however,
        # we want another file listener that tracks all files
        # staged at the inputs/named_files level.
        #
        Listener.__init__(self, csvpaths.config if csvpaths else config)
        self.csvpaths = csvpaths
        self.type_name = "files"

    def manifest_path(self) -> str:
        root = self.config.get(section="inputs", name="files")
        mf = Nos(root).join("manifest.json")
        if not Nos(mf).exists():
            with DataFileWriter(path=mf, mode="w") as writer:
                writer.append("[]")
        return mf

    def get_manifest(self, mpath) -> list:
        with DataFileReader(mpath) as reader:
            return json.load(reader.source)

    def _core_from_metadata(self, mdata: Metadata) -> dict:
        mani = {}
        mani["time"] = mdata.time_string
        mani["uuid"] = mdata.uuid_string
        mani["file_manifest"] = mdata.manifest_path
        if mdata.username:
            mani["username"] = mdata.username
        if mdata.hostname:
            mani["hostname"] = mdata.hostname
        if mdata.ip_address:
            mani["ip_address"] = mdata.ip_address
        return mani

    def _prep_update(self, mdata: Metadata) -> dict:
        #
        # every ledger entry has a status; none is implied by absence
        #
        if mdata.status is None:
            raise ValueError("A named-files ledger entry requires a status")
        mani = self._core_from_metadata(mdata)
        mani["type"] = mdata.type
        mani["time"] = mdata.time_string
        mani["named_file_name"] = mdata.named_file_name
        mani["origin_path"] = mdata.origin_path
        mani["fingerprint"] = mdata.fingerprint
        mani["reference"] = mdata.reference
        mani["file_path"] = mdata.file_path
        mani["file_home"] = mdata.file_home
        mani["file_name"] = mdata.file_name
        mani["name_home"] = mdata.name_home
        if mdata.template is not None:
            mani["template"] = mdata.template
        if mdata.mark is not None:
            mani["mark"] = mdata.mark
        mani["manifest_path"] = self.manifest_path()
        mani["status"] = mdata.status
        if getattr(mdata, "registration_uuid", None) is not None:
            mani["registration_uuid"] = mdata.registration_uuid
        return mani

    #
    # the per-name entry's fields a patch changes, and the ledger's names
    # for them
    #
    PATCHED_FIELDS = {
        "type": "type",
        "file": "file_path",
        "file_home": "file_home",
        "file_name": "file_name",
    }

    def metadata_patch(self, mdata: Metadata) -> None:
        """applies a patch, already applied to the per-name entry, to the
        arrival's ledger entry, in place. the entry records the change in
        its own changes list, in its own field names. a ledger with no
        arrival for the entry (e.g. one written before the ledger writer
        was built in) is not backfilled."""
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        entry = mdata.manifest_entry
        if entry is None or mdata.change is None:
            raise ValueError("Metadata has no patched manifest entry")
        manifest_path = self.manifest_path()
        jdata = self.get_manifest(manifest_path)
        index = self._arrival_index(jdata=jdata, uuid=entry["uuid"])
        if index is None:
            if self.csvpaths:
                self.csvpaths.logger.warning(
                    "No ledger entry for named-file %s entry %s; patch not written to the ledger",
                    mdata.named_file_name,
                    entry["uuid"],
                )
            return
        ledger_entry = jdata[index]
        prior = {}
        for field, ledger_field in self.PATCHED_FIELDS.items():
            if ledger_entry.get(ledger_field) != entry.get(field):
                prior[ledger_field] = ledger_entry.get(ledger_field)
                ledger_entry[ledger_field] = entry.get(field)
        change = dict(mdata.change)
        change["from"] = prior
        ledger_entry.setdefault("changes", []).append(change)
        with DataFileWriter(path=manifest_path, mode="w") as writer:
            j = json.dumps(jdata, indent=2)
            writer.sink.write(j)
            writer.sink.flush()
        mdata.ledger_entry = ledger_entry
        mdata.ledger_index = index

    def _arrival_index(self, *, jdata: list, uuid: str) -> int | None:
        """the position of the arrival with uuid. ledgers from before
        failures had their own uuid may also hold a failure with it."""
        if uuid is None or not isinstance(uuid, str) or uuid.strip() == "":
            raise ValueError("Uuid must be a non-empty str")
        for i, e in enumerate(jdata):
            if e.get("uuid") == uuid and e.get("file_path") is not None:
                return i
        return None

    def metadata_failure(self, mdata: Metadata) -> None:
        """a failed registration is a ledger entry like any other"""
        self.metadata_update(mdata)

    def metadata_update(self, mdata: Metadata) -> None:
        mani = self._prep_update(mdata)
        manifest_path = self.manifest_path()
        #
        # this will not be Ok for major implementations. there is a
        # potential for lost updates. however, for small or low risk
        # implementations it will work. replacing with a concurrancy-safe
        # listener would be straightforward. a future todo or some kind
        # of upgrade above the stock library?
        #
        jdata = self.get_manifest(manifest_path)
        jdata.append(mani)
        with DataFileWriter(path=manifest_path, mode="w") as writer:
            j = json.dumps(jdata, indent=2)
            writer.sink.write(j)
            writer.sink.flush()
        mdata.ledger_entry = mani
        mdata.ledger_index = len(jdata) - 1
