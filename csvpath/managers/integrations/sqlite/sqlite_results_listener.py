from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.util.sqliter import Sqliter
import os


class SqliteResultsListener(Listener):
    def __init__(self, config=None):
        Listener.__init__(self, config=config)
        self.csvpaths = None

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError(
                "Sqlite results listener cannot continue without a CsvPaths instance"
            )
        with Sqliter(
            config=self.csvpaths.config, client_class=SqliteResultsListener
        ) as conn:
            try:
                fsep = "/" if mdata.named_files_root.find("://") > -1 else os.sep
                psep = "/" if mdata.named_paths_root.find("://") > -1 else os.sep
                group_run_data = {
                    "uuid": mdata.uuid_string,
                    "at": mdata.time_string,
                    "time_completed": mdata.time_completed_string,
                    "status": mdata.status,
                    "by_line_run": "Y" if mdata.by_line else "N",
                    "all_completed": "Y" if mdata.all_completed else "N",
                    "all_valid": "Y" if mdata.all_valid else "N",
                    "error_count": mdata.error_count if mdata.error_count else 0,
                    "all_expected_files": "Y" if mdata.all_expected_files else "N",
                    #
                    # context IDs, names, etc.
                    #
                    "archive_name": mdata.archive_name,
                    "run_home": mdata.run_home,
                    #
                    # paths
                    #
                    "named_results_name": mdata.named_results_name,
                    "named_paths_uuid": mdata.named_paths_uuid,
                    "named_paths_name": mdata.named_paths_name,
                    "named_paths_home": f"{mdata.named_paths_root}{psep}{mdata.named_paths_name}",
                    #
                    # file
                    #
                    "named_file_uuid": mdata.named_file_uuid,
                    "named_file_name": mdata.named_file_name,
                    "named_file_home": f"{mdata.named_files_root}{fsep}{mdata.named_file_name}",
                    "named_file_path": mdata.named_file_path,
                    #
                    # these we might not have
                    #
                    "named_file_size": mdata.named_file_size,
                    "named_file_last_change": mdata.named_file_last_change,
                    "named_file_fingerprint": mdata.named_file_fingerprint,
                    #
                    #
                    #
                    "hostname": mdata.hostname,
                    "username": mdata.username,
                    "ip_address": mdata.ip_address,
                    "manifest_path": mdata.manifest_path,
                }
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                        INSERT INTO named_paths_group_run (
                            uuid,
                            at,
                            time_completed,
                            status,
                            by_line_run,
                            all_completed,
                            all_valid,
                            error_count,
                            all_expected_files,
                            archive_name,
                            run_home,
                            named_results_name,
                            named_paths_uuid,
                            named_paths_name,
                            named_paths_home,
                            named_file_uuid,
                            named_file_name,
                            named_file_home,
                            named_file_path,
                            named_file_size,
                            named_file_last_change,
                            named_file_fingerprint,
                            hostname,
                            username,
                            ip_address,
                            manifest_path
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?,
                            ?, ?
                        )
                        ON CONFLICT(uuid) DO UPDATE SET
                            status='{mdata.status}',
                            time_completed='{mdata.time_completed}',
                            all_completed='{group_run_data.get("all_completed")}',
                            all_valid='{group_run_data.get("all_valid")}',
                            error_count='{mdata.error_count}',
                            all_expected_files='{group_run_data.get("all_expected_files")}'

                    """,
                    (*group_run_data.values(),),
                )
            finally:
                conn.commit()
                cursor.close()
