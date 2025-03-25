from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.util.sqliter import Sqliter
import os


class SqliteResultListener(Listener):
    def __init__(self, config=None):
        Listener.__init__(self, config=config)
        self.csvpaths = None

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError(
                "Sqlite result listener cannot continue without a CsvPaths instance"
            )
        with Sqliter(
            config=self.csvpaths.config, client_class=SqliteResultListener
        ) as conn:
            try:
                instance_run_data = {
                    "uuid": mdata.uuid_string,
                    "at": mdata.time_string,
                    "group_run_uuid": mdata.named_paths_uuid_string,
                    "instance_identity": mdata.instance_identity,
                    "instance_index": mdata.instance_index,
                    "instance_home": mdata.instance_home,
                    "source_mode_preceding": mdata.source_mode_preceding,
                    "preceding_instance_identity": mdata.preceding_instance_identity,
                    "actual_data_file": mdata.actual_data_file,
                    "valid": "Y" if mdata.valid else "N",
                    "completed": "Y" if mdata.completed else "N",
                    "error_count": mdata.error_count if mdata.error_count else 0,
                    "number_of_files_expected": mdata.number_of_files_expected,
                    "number_of_files_generated": mdata.number_of_files_generated,
                    "files_expected": "Y" if mdata.files_expected else "N",
                    "lines_scanned": mdata.lines_scanned,
                    "lines_total": mdata.lines_total,
                    "lines_matched": mdata.lines_matched,
                    "manifest_path": mdata.manifest_path,
                }
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                        INSERT INTO instance_run (
                            uuid,
                            at,
                            group_run_uuid,
                            instance_identity,
                            instance_index,
                            instance_home,
                            source_mode_preceding,
                            preceding_instance_identity,
                            actual_data_file,
                            valid,
                            completed,
                            error_count,
                            number_of_files_expected,
                            number_of_files_generated,
                            files_expected,
                            lines_scanned,
                            lines_total,
                            lines_matched,
                            manifest_path
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?
                        )
                        ON CONFLICT(uuid) DO UPDATE SET
                            valid='{instance_run_data.get("valid")}',
                            completed='{instance_run_data.get("completed")}',
                            error_count='{mdata.error_count}',
                            number_of_files_expected='{instance_run_data.get("number_of_files_expected")}',
                            number_of_files_generated='{instance_run_data.get("number_of_files_generated")}',
                            files_expected='{instance_run_data.get("files_expected")}',
                            lines_scanned='{mdata.lines_scanned}',
                            lines_total='{mdata.lines_total}',
                            lines_matched='{mdata.lines_matched}'
                    """,
                    (*instance_run_data.values(),),
                )
            finally:
                conn.commit()
                cursor.close()
