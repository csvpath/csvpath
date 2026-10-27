class LedgerUtility:
    """@private
    changes to root ledger entries (the named-files and named-paths
    manifest.json at the root of each) that the ledger writers share"""

    @classmethod
    def mark_deleted(
        cls, *, jdata: list, name_key: str, name: str, change: dict, deleted: str
    ) -> list[dict]:
        """marks every entry for name that is not already deleted with the
        deleted lifecycle and appends change to its changes list, in place.
        entries without a lifecycle (written before lifecycles) are marked
        too. returns the marked entries, in ledger order."""
        if jdata is None or not isinstance(jdata, list):
            raise TypeError("Ledger must be a list")
        for label, v in [("Name key", name_key), ("Name", name), ("Deleted", deleted)]:
            if v is None or not isinstance(v, str) or v.strip() == "":
                raise ValueError(f"{label} must be a non-empty str")
        if not isinstance(change, dict) or len(change) == 0:
            raise ValueError("Change must be a non-empty dict")
        marked = []
        for e in jdata:
            if e.get(name_key) != name or e.get("lifecycle") == deleted:
                continue
            e["lifecycle"] = deleted
            e.setdefault("changes", []).append(dict(change))
            marked.append(e)
        return marked
