from .filesystem_reference_source import FilesystemReferenceSource
from .reference_source import ReferenceSource


class ReferencesSqlCoverage:
    """reports whether SQL holds everything the JSON root ledgers hold, so
    that [references] sql = on would see what off sees.

    SQL is never backfilled: switch the SQL listeners on after JSON
    ledgers already exist and SQL only has what came after. under on,
    references would quietly miss the older entries. shadow catches this
    only for the references you run; this checks the whole config at once.

    for each datatype it compares the root ledger in the filesystem with
    the SQL mirror of it, by uuid. both are read scoped to the current
    config's roots. missing entries are split by ledger position: those
    before SQL's first entry mean SQL was switched on late; those after
    it are gaps, i.e. SQL writes failed while it was on.

    the report is advisory. it never raises over what it finds and does
    not stop anyone using on. if ReferencesSqlCheck finds problems, SQL is
    not read and the problems are the report.
    """

    #
    # datatype -> (ledger read, the entry key naming the named-file or
    # named-paths group)
    #
    LEDGERS = {
        "files": ("files_ledger", "named_file_name"),
        "csvpaths": ("paths_ledger", "named_paths_name"),
        "results": ("results_ledger", "named_paths_name"),
    }
    #
    # the counts that must all be 0 for a ledger to be covered
    #
    GAPS = ["missing", "only_in_sql", "differ", "no_uuid", "duplicate_uuids"]

    def __init__(
        self,
        *,
        csvpaths,
        primary: ReferenceSource | None = None,
        secondary: ReferenceSource | None = None,
    ) -> None:
        if csvpaths is None:
            raise ValueError("CsvPaths cannot be None")
        if primary is not None and not isinstance(primary, ReferenceSource):
            raise TypeError("Primary must be a ReferenceSource")
        if secondary is not None and not isinstance(secondary, ReferenceSource):
            raise TypeError("Secondary must be a ReferenceSource")
        self.csvpaths = csvpaths
        self._primary = primary
        self._secondary = secondary

    @property
    def primary(self) -> ReferenceSource:
        if self._primary is None:
            self._primary = FilesystemReferenceSource(csvpaths=self.csvpaths)
        return self._primary

    @property
    def secondary(self) -> ReferenceSource:
        if self._secondary is None:
            #
            # imported here, as CsvPaths does: the SQL source imports the
            # SQL integration. built only after the check finds no problems
            #
            from .sql_reference_source import SqlReferenceSource

            self._secondary = SqlReferenceSource(csvpaths=self.csvpaths)
        return self._secondary

    def report(self) -> dict:
        from csvpath.managers.integrations.sql.references_sql_check import (
            ReferencesSqlCheck,
        )

        config = self.csvpaths.config
        report = {
            "config": config.config_path,
            "mode": config.references_sql,
            "problems": ReferencesSqlCheck.problems(csvpaths=self.csvpaths),
            "ledgers": {},
            "covered": False,
        }
        if len(report["problems"]) > 0:
            return report
        for datatype, (method, name_key) in self.LEDGERS.items():
            fs = getattr(self.primary, method)()
            try:
                sql = getattr(self.secondary, method)()
            except Exception as ex:
                self.csvpaths.logger.error(
                    f"SQL coverage: SQL {method}() raised: {ex}"
                )
                self.csvpaths.logger.exception(ex)
                raise
            report["ledgers"][datatype] = self.compare(
                json_ledger=fs, sql_ledger=sql, name_key=name_key
            )
        report["covered"] = all(
            self.ledger_covered(ledger=ledger)
            for ledger in report["ledgers"].values()
        )
        return report

    @classmethod
    def ledger_covered(cls, *, ledger: dict) -> bool:
        if not isinstance(ledger, dict):
            raise TypeError("Ledger must be a dict")
        return (
            all(ledger[k] == 0 for k in cls.GAPS) and not ledger["order_differs"]
        )

    @classmethod
    def compare(
        cls, *, json_ledger: list | None, sql_ledger: list | None, name_key: str
    ) -> dict:
        """compares one ledger as the filesystem and SQL hold it"""
        #
        # None: no manifest.json yet, nothing registered
        #
        json = [] if json_ledger is None else json_ledger
        sql = [] if sql_ledger is None else sql_ledger
        if not isinstance(json, list):
            raise TypeError("JSON ledger must be a list")
        if not isinstance(sql, list):
            raise TypeError("SQL ledger must be a list")
        if not isinstance(name_key, str) or name_key.strip() == "":
            raise ValueError("Name key must be a non-empty str")
        sql_by_uuid = {}
        for e in sql:
            sql_by_uuid[cls._uuid(e)] = e
        seen = set()
        duplicates = 0
        no_uuid = 0
        differ = 0
        both = []
        missing = []
        for i, e in enumerate(json):
            uuid = cls._uuid(e)
            if uuid is None:
                no_uuid += 1
                continue
            if uuid in seen:
                duplicates += 1
                continue
            seen.add(uuid)
            if uuid in sql_by_uuid:
                both.append(uuid)
                if sql_by_uuid[uuid] != e:
                    differ += 1
            else:
                missing.append((i, e))
        only_in_sql = len([u for u in sql_by_uuid if u not in seen])
        #
        # by position, not by parsing times: the JSON ledger is in write
        # order, so SQL's first entry is where SQL began
        #
        first = None
        for i, e in enumerate(json):
            if cls._uuid(e) in sql_by_uuid:
                first = i
                break
        before = [m for m in missing if first is None or m[0] < first]
        after = [m for m in missing if first is not None and m[0] > first]
        sql_order = [cls._uuid(e) for e in sql if cls._uuid(e) in seen]
        by_name = {}
        for _, e in missing:
            name = e.get(name_key) if isinstance(e, dict) else None
            by_name[name] = by_name.get(name, 0) + 1
        return {
            "json": len(json),
            "sql": len(sql),
            "both": len(both),
            "missing": len(missing),
            "missing_before_sql": len(before),
            "missing_after_sql": len(after),
            "missing_by_name": by_name,
            "missing_first_time": cls._time(missing[0][1]) if missing else None,
            "missing_last_time": cls._time(missing[-1][1]) if missing else None,
            "sql_first_time": cls._time(json[first]) if first is not None else None,
            "only_in_sql": only_in_sql,
            "differ": differ,
            "no_uuid": no_uuid,
            "duplicate_uuids": duplicates,
            "order_differs": sql_order != both,
        }

    @staticmethod
    def _uuid(entry):
        if isinstance(entry, dict):
            return entry.get("uuid")
        return None

    @staticmethod
    def _time(entry):
        #
        # as written: a label for people, never compared
        #
        if isinstance(entry, dict):
            return entry.get("time")
        return None

    @classmethod
    def format(cls, *, report: dict) -> str:
        """the report as text, for the CLI"""
        if not isinstance(report, dict):
            raise TypeError("Report must be a dict")
        lines = [
            "references SQL coverage",
            f"  config: {report['config']}",
            f"  [references] sql = {report['mode']}",
            "",
        ]
        if len(report["problems"]) > 0:
            lines.append("SQL cannot be used, so it was not read:")
            lines += [f"  - {p}" for p in report["problems"]]
            lines.append("")
            lines.append("NOT READY: fix the problems above and check again.")
            return "\n".join(lines)
        cols = ["json", "sql", "both", "missing", "only_in_sql", "differ"]
        lines.append(f"{'':10}" + "".join(f"{c:>13}" for c in cols))
        for datatype, ledger in report["ledgers"].items():
            lines.append(
                f"{datatype:10}" + "".join(f"{ledger[c]:>13}" for c in cols)
            )
        lines.append("")
        for datatype, ledger in report["ledgers"].items():
            lines += cls._details(datatype=datatype, ledger=ledger)
        if report["covered"]:
            lines.append(
                "COVERED: [references] sql = on will see everything the JSON "
                "ledgers hold."
            )
        else:
            missing = sum(
                ledger["missing"] for ledger in report["ledgers"].values()
            )
            lines.append(
                "NOT COVERED: under [references] sql = on, references would "
                f"not see what off sees ({missing} entries missing from SQL)."
            )
        return "\n".join(lines)

    @classmethod
    def _details(cls, *, datatype: str, ledger: dict) -> list[str]:
        lines = []
        if ledger["missing_before_sql"] > 0:
            if ledger["sql_first_time"] is None:
                when = "SQL has none of this ledger"
            else:
                when = f"all before SQL's first entry ({ledger['sql_first_time']})"
            lines.append(
                f"{datatype}: {ledger['missing_before_sql']} entries missing "
                f"from SQL, {when}: SQL was switched on after they were written"
            )
        if ledger["missing_after_sql"] > 0:
            lines.append(
                f"{datatype}: {ledger['missing_after_sql']} entries missing "
                f"from SQL AFTER its first entry ({ledger['sql_first_time']}): "
                "SQL writes failed while SQL was on"
            )
        if ledger["missing"] > 0:
            by_name = sorted(ledger["missing_by_name"].items(), key=str)
            names = ", ".join(f"{n} {c}" for n, c in by_name)
            lines.append(
                f"  {ledger['missing_first_time']} .. {ledger['missing_last_time']};"
                f" by name: {names}"
            )
        if ledger["only_in_sql"] > 0:
            lines.append(
                f"{datatype}: {ledger['only_in_sql']} entries are in SQL but "
                "not the JSON ledger"
            )
        if ledger["differ"] > 0:
            lines.append(
                f"{datatype}: {ledger['differ']} entries differ between the "
                "JSON ledger and SQL"
            )
        if ledger["order_differs"]:
            lines.append(f"{datatype}: SQL holds the entries in a different order")
        if ledger["no_uuid"] > 0:
            lines.append(
                f"{datatype}: {ledger['no_uuid']} JSON entries have no uuid "
                "and cannot be matched"
            )
        if ledger["duplicate_uuids"] > 0:
            lines.append(
                f"{datatype}: {ledger['duplicate_uuids']} JSON entries repeat "
                "a uuid"
            )
        if len(lines) > 0:
            lines.append("")
        return lines
