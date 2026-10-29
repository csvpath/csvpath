from .filesystem_reference_source import FilesystemReferenceSource
from .reference_source import ReferenceSource


class ShadowReferenceSource(ReferenceSource):
    """used when [references] sql = shadow, to prove a SQL configuration
    before using on. every read goes to both the filesystem and SQL; the
    two are compared, any difference is logged as a warning, and the
    filesystem result is returned. a SQL read that raises is logged and
    raised.

    shadow is a dev and test setting, not one to keep on in production:
    it makes every read twice, so it costs more than off.
    """

    #
    # reads whose contract has no order. the rest are compared as they are.
    #
    UNORDERED = ["instance_dirs"]
    COUNTS = ["reads", "matches", "differences", "sql_errors"]

    def __init__(
        self,
        *,
        csvpaths,
        primary: ReferenceSource | None = None,
        secondary: ReferenceSource | None = None,
    ) -> None:
        super().__init__(csvpaths=csvpaths)
        if primary is None:
            primary = FilesystemReferenceSource(csvpaths=csvpaths)
        if secondary is None:
            #
            # imported here, as CsvPaths does: the SQL source imports the
            # SQL integration
            #
            from .sql_reference_source import SqlReferenceSource

            secondary = SqlReferenceSource(csvpaths=csvpaths)
        if not isinstance(primary, ReferenceSource):
            raise TypeError("Primary must be a ReferenceSource")
        if not isinstance(secondary, ReferenceSource):
            raise TypeError("Secondary must be a ReferenceSource")
        self._primary = primary
        self._secondary = secondary
        self._counts = {}
        csvpaths.logger.warning(
            "[references] sql = shadow: every reference read is made from "
            "both the filesystem and SQL and compared. shadow is for dev "
            "and test, not production."
        )

    @property
    def primary(self) -> ReferenceSource:
        return self._primary

    @property
    def secondary(self) -> ReferenceSource:
        return self._secondary

    @property
    def counts(self) -> dict:
        """per read method: reads, matches, differences and sql_errors"""
        return {method: dict(c) for method, c in self._counts.items()}

    def _count(self, *, method: str, what: str) -> None:
        if method not in self._counts:
            self._counts[method] = {c: 0 for c in self.COUNTS}
        self._counts[method][what] += 1

    def _compare(self, *, method: str, args: tuple, kwargs: dict):
        if method is None or not isinstance(method, str) or method.strip() == "":
            raise ValueError("Method must be a non-empty str")
        #
        # the filesystem first: if it raises, e.g. on a bad argument, that
        # is the caller's exception, as under off, and SQL is not read
        #
        fs = getattr(self._primary, method)(*args, **kwargs)
        self._count(method=method, what="reads")
        call = self._call_string(method=method, args=args, kwargs=kwargs)
        try:
            sql = getattr(self._secondary, method)(*args, **kwargs)
        except Exception as ex:
            self._count(method=method, what="sql_errors")
            self.csvpaths.logger.error(f"shadow: SQL {call} raised: {ex}")
            self.csvpaths.logger.exception(ex)
            raise
        if self._same(method=method, fs=fs, sql=sql):
            self._count(method=method, what="matches")
        else:
            self._count(method=method, what="differences")
            self.csvpaths.logger.warning(
                f"shadow: {call} differs: {self.describe(fs=fs, sql=sql)}"
            )
        return fs

    def _same(self, *, method: str, fs, sql) -> bool:
        if (
            method in self.UNORDERED
            and isinstance(fs, list)
            and isinstance(sql, list)
        ):
            return sorted(fs) == sorted(sql)
        return fs == sql

    @staticmethod
    def _call_string(*, method: str, args: tuple, kwargs: dict) -> str:
        parts = [repr(a) for a in args]
        parts += [f"{k}={v!r}" for k, v in kwargs.items()]
        return f"{method}({', '.join(parts)})"

    @staticmethod
    def describe(*, fs, sql) -> str:
        """a short account of how two read results differ. never the
        whole values: manifests can be long."""
        if isinstance(fs, list) and isinstance(sql, list):
            for i in range(max(len(fs), len(sql))):
                a = fs[i] if i < len(fs) else None
                b = sql[i] if i < len(sql) else None
                if i >= len(fs) or i >= len(sql) or a != b:
                    uuid = ShadowReferenceSource._uuid(a)
                    if uuid is None:
                        uuid = ShadowReferenceSource._uuid(b)
                    s = (
                        f"lengths {len(fs)} vs {len(sql)}; "
                        f"first difference at index {i}"
                    )
                    if i >= len(fs):
                        s = f"{s} (filesystem: missing)"
                    elif i >= len(sql):
                        s = f"{s} (sql: missing)"
                    if uuid is not None:
                        s = f"{s}, uuid {uuid}"
                    return s
            #
            # equal lists: only an unordered read compared sorted can be
            # equal here, and _same does not report those
            #
            return f"lengths {len(fs)} vs {len(sql)}, same items"
        if isinstance(fs, dict) and isinstance(sql, dict):
            keys = sorted(
                k
                for k in set(fs.keys()) | set(sql.keys())
                if fs.get(k) != sql.get(k) or (k in fs) != (k in sql)
            )
            s = f"keys differ: {keys}"
            uuid = ShadowReferenceSource._uuid(fs)
            if uuid is None:
                uuid = ShadowReferenceSource._uuid(sql)
            if uuid is not None:
                s = f"{s}, uuid {uuid}"
            return s
        return f"filesystem {type(fs).__name__}, sql {type(sql).__name__}"

    @staticmethod
    def _uuid(value):
        if isinstance(value, dict):
            return value.get("uuid")
        return None

    #
    # FILES
    #
    def file_manifest(self, name: str) -> list:
        return self._compare(method="file_manifest", args=(name,), kwargs={})

    def files_ledger(self) -> list | None:
        return self._compare(method="files_ledger", args=(), kwargs={})

    def file_names(self) -> list[str]:
        return self._compare(method="file_names", args=(), kwargs={})

    #
    # CSVPATHS
    #
    def paths_manifest(self, name: str) -> list:
        return self._compare(method="paths_manifest", args=(name,), kwargs={})

    def paths_ledger(self) -> list:
        return self._compare(method="paths_ledger", args=(), kwargs={})

    def paths_names(self) -> list[str]:
        return self._compare(method="paths_names", args=(), kwargs={})

    #
    # RESULTS
    #
    def results_ledger(self) -> list:
        return self._compare(method="results_ledger", args=(), kwargs={})

    def run_homes(
        self, *, root_major: str | None, name_filter: str | None
    ) -> list[tuple[str, str]]:
        return self._compare(
            method="run_homes",
            args=(),
            kwargs={"root_major": root_major, "name_filter": name_filter},
        )

    def run_manifest(self, run_dir: str) -> dict | None:
        return self._compare(method="run_manifest", args=(run_dir,), kwargs={})

    def instance_manifest(self, instance_dir: str) -> dict | None:
        return self._compare(
            method="instance_manifest", args=(instance_dir,), kwargs={}
        )

    def instance_dirs(self, run_dir: str) -> list[str]:
        return self._compare(method="instance_dirs", args=(run_dir,), kwargs={})
