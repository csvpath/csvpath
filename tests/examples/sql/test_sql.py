import unittest
import pytest
import datetime
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.exc import IntegrityError
from csvpath import CsvPaths
from csvpath.managers.integrations.sql.sql_result_listener import SqlResultListener
from csvpath.managers.integrations.sql.sql_results_listener import SqlResultsListener
from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
from csvpath.managers.integrations.sql.sql_paths_listener import SqlPathsListener
from csvpath.managers.integrations.sql.tables import Tables


class TestSql(unittest.TestCase):
    def setUp(self):
        self._engine = self.sqlite_engine()

    def sqlite_engine(self) -> Engine:
        engine = create_engine("sqlite:///:memory:")
        return engine

    def test_sql_table_creation(self):
        paths = CsvPaths()
        #
        # instance run. do this first because it has a FK that needs to
        # not blow up if we create this table first.
        #
        listener = SqlResultListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine
        table = listener.instance_run
        assert table.name == "instance_run"
        assert "uuid" in table.c
        assert "valid" in table.c
        #
        # group run
        #
        listener = SqlResultsListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine
        table = listener.group_run
        assert table.name == "named_paths_group_run"
        assert "uuid" in table.c
        assert "run_home" in table.c
        #
        # named-files
        #
        listener = SqlFileListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine
        table = listener.named_file
        assert table.name == "named_file"
        assert "uuid" in table.c
        assert "file_home" in table.c
        #
        # named-paths
        #
        listener = SqlPathsListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine
        table = listener.named_paths
        assert table.name == "named_paths"
        assert "uuid" in table.c
        assert "paths_home" in table.c

    # =======================
    # inserts
    # =======================

    def test_sql_named_paths_data_insertion(self):
        paths = CsvPaths()
        listener = SqlPathsListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine  # Use in-memory SQLite
        named_paths_data = {
            "uuid": "test-uuid",
            "at": datetime.datetime.now(),
            "paths_name": "aname",
            "paths_home": "a/b/c/aname",
            "group_file_path": "a/b/c/aname/afile.csv/abcsd.csv",
            "paths_count": 5,
            "ip_address": "0.0.0.0",
            "hostname": "mymachine",
            "username": "fish",
            "paths_root": "i/j/k",
            "base_path": "e/f/g",
            "manifest_path": "a/b/c/aname/manifest.json",
        }
        listener._upsert_named_paths(named_paths_data, dispose=False)
        with listener.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM named_paths WHERE uuid = 'test-uuid'")
            ).fetchone()
            assert result
            assert result[0] == "test-uuid"
            assert result.paths_count == 5

    def test_sql_named_file_data_insertion(self):
        paths = CsvPaths()
        listener = SqlFileListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine  # Use in-memory SQLite
        named_file_data = {
            "uuid": "test-uuid",
            "at": datetime.datetime.now(),
            "named_file_name": "afile.csv",
            "origin_path": "x/y/z/afile.csv",
            "name_home": "aname",
            "file_home": "a/b/c/aname",
            "file_path": "a/b/c/aname/afile.csv/abcsd.csv",
            "file_name": "abcsd.csv",
            "mark": None,
            "type": "csv",
            "file_size": 0,
            "ip_address": "0.0.0.0",
            "hostname": "mymachine",
            "username": "fish",
            "files_root": "i/j/k",
            "base_path": "e/f/g",
            "manifest_path": "a/b/c/aname/manifest.json",
        }
        listener._upsert_named_file(named_file_data, dispose=False)
        with listener.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM named_file WHERE uuid = 'test-uuid'")
            ).fetchone()
            assert result
            assert result[0] == "test-uuid"
            assert result.type == "csv"

    def test_sql_instance_run_data_insertion(self):
        paths = CsvPaths()
        listener = SqlResultListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine  # Use in-memory SQLite
        instance_run_data = {
            "uuid": "test-uuid",
            "at": datetime.datetime.now(),
            "group_run_uuid": "test-group-uuid",
            "instance_identity": "test-instance",
            "instance_index": 1,
            "instance_home": "/path/to/instance",
            "source_mode_preceding": "N",
            "preceding_instance_identity": None,
            "actual_data_file": None,
            "number_of_files_expected": 10,
            "number_of_files_generated": 10,
            "files_expected": "Y",
            "valid": "Y",
            "completed": "Y",
            "error_count": 0,
            "lines_scanned": 100,
            "lines_total": 100,
            "lines_matched": 100,
            "manifest_path": "/path/to/manifest",
        }
        listener._upsert_instance_run(instance_run_data, dispose=False)
        # Verify the inserted data
        with listener.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM instance_run WHERE uuid = 'test-uuid'")
            ).fetchone()
            assert result
            assert result[0] == "test-uuid"
            assert result.valid == "Y"

    def test_sql_group_run_data_insertion(self):
        paths = CsvPaths()
        listener = SqlResultsListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine  # Use in-memory SQLite
        group_run_data = {
            "uuid": "test-uuid",
            "at": datetime.datetime.now(),
            "time_completed": datetime.datetime.now(),
            "status": "completed",
            "by_line_run": "Y",
            "all_completed": "Y",
            "all_valid": "N",
            "error_count": 2,
            "all_expected_files": "Y",
            "archive_name": "test-archive",
            "run_home": "/path/to/run_home",
            "named_results_name": "test-results",
            "named_paths_uuid": "test-named-paths-uuid",
            "named_paths_name": "test-named-paths",
            "named_paths_home": "/path/to/paths_home",
            "named_file_uuid": "test-file-uuid",
            "named_file_name": "test-file",
            "named_file_home": "/path/to/file_home",
            "named_file_path": "/path/to/file",
            "named_file_size": 12345,
            "named_file_last_change": datetime.datetime.now(),
            "named_file_fingerprint": "abcdef123456",
            "hostname": "test-host",
            "username": "test-user",
            "ip_address": "192.168.1.1",
            "manifest_path": "/path/to/manifest",
        }
        listener._upsert_named_paths_group_run(group_run_data, dispose=False)
        with self._engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM named_paths_group_run WHERE uuid = 'test-uuid'")
            ).fetchone()
            assert result
            assert result[0] == "test-uuid"
            assert result.status == "completed"

    # =======================
    # updates
    # =======================

    def test_sql_upsert_named_paths_functionality(self):
        paths = CsvPaths()
        listener = SqlPathsListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine
        # Initial insert
        named_paths_data = {
            "uuid": "test-uuid",
            "at": datetime.datetime.now(),
            "paths_name": "aname",
            "paths_home": "a/b/c/aname",
            "group_file_path": "a/b/c/aname/afile.csv/abcsd.csv",
            "paths_count": 5,
            "ip_address": "0.0.0.0",
            "hostname": "mymachine",
            "username": "fish",
            "paths_root": "i/j/k",
            "base_path": "e/f/g",
            "manifest_path": "a/b/c/aname/manifest.json",
        }
        listener._upsert_named_paths(named_paths_data, dispose=False)
        # Update the data
        updated_named_paths_data = named_paths_data.copy()
        updated_named_paths_data["paths_count"] = 7  # Change the value
        listener._upsert_named_paths(updated_named_paths_data, dispose=False)
        # Verify the updated data
        with listener.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM named_paths WHERE uuid = 'test-uuid'")
            ).fetchone()
            assert result.uuid == "test-uuid"
            assert result.paths_count == 7

    def test_sql_upsert_named_file_functionality(self):
        paths = CsvPaths()
        listener = SqlFileListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine
        # Initial insert
        named_file_data = {
            "uuid": "test-uuid",
            "at": datetime.datetime.now(),
            "named_file_name": "afile.csv",
            "origin_path": "x/y/z/afile.csv",
            "name_home": "aname",
            "file_home": "a/b/c/aname",
            "file_path": "a/b/c/aname/afile.csv/abcsd.csv",
            "file_name": "abcsd.csv",
            "mark": None,
            "type": "csv",
            "file_size": 0,
            "ip_address": "0.0.0.0",
            "hostname": "mymachine",
            "username": "fish",
            "files_root": "i/j/k",
            "base_path": "e/f/g",
            "manifest_path": "a/b/c/aname/manifest.json",
        }
        listener._upsert_named_file(named_file_data, dispose=False)
        # Update the data
        updated_named_file_data = named_file_data.copy()
        updated_named_file_data["mark"] = "#"  # Change the value
        updated_named_file_data["file_size"] = 2000  # Change the value
        listener._upsert_named_file(updated_named_file_data, dispose=False)
        # Verify the updated data
        with listener.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM named_file WHERE uuid = 'test-uuid'")
            ).fetchone()
            assert result.uuid == "test-uuid"
            assert result.mark == "#"
            assert result.file_size == 2000

    def test_sql_upsert_instance_run_functionality(self):
        paths = CsvPaths()
        listener = SqlResultListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine
        # Initial insert
        instance_run_data = {
            "uuid": "test-uuid",
            "at": datetime.datetime.now(),
            "group_run_uuid": "test-group-uuid",
            "instance_identity": "test-instance",
            "instance_index": 1,
            "instance_home": "/path/to/instance",
            "source_mode_preceding": "N",
            "preceding_instance_identity": None,
            "actual_data_file": None,
            "number_of_files_expected": 10,
            "number_of_files_generated": 10,
            "files_expected": "Y",
            "valid": "Y",
            "completed": "Y",
            "error_count": 0,
            "lines_scanned": 100,
            "lines_total": 100,
            "lines_matched": 100,
            "manifest_path": "/path/to/manifest",
        }
        listener._upsert_instance_run(instance_run_data, dispose=False)

        # Update the data
        updated_run_data = instance_run_data.copy()
        updated_run_data["valid"] = "N"  # Change the value
        listener._upsert_instance_run(updated_run_data, dispose=False)

        # Verify the updated data
        with listener.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM instance_run WHERE uuid = 'test-uuid'")
            ).fetchone()
            assert result.uuid == "test-uuid"
            assert result.valid == "N"

    def test_upsert_group_run_functionality(self):
        paths = CsvPaths()
        listener = SqlResultsListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine

        # Initial insert
        group_run_data = {
            "uuid": "test-uuid",
            "at": datetime.datetime.now(),
            "time_completed": datetime.datetime.now(),
            "status": "completed",
            "by_line_run": "Y",
            "all_completed": "Y",
            "all_valid": "N",
            "error_count": 2,
            "all_expected_files": "Y",
            "archive_name": "test-archive",
            "run_home": "/path/to/run_home",
            "named_results_name": "test-results",
            "named_paths_uuid": "test-named-paths-uuid",
            "named_paths_name": "test-named-paths",
            "named_paths_home": "/path/to/paths_home",
            "named_file_uuid": "test-file-uuid",
            "named_file_name": "test-file",
            "named_file_home": "/path/to/file_home",
            "named_file_path": "/path/to/file",
            "named_file_size": 12345,
            "named_file_last_change": datetime.datetime.now(),
            "named_file_fingerprint": "abcdef123456",
            "hostname": "test-host",
            "username": "test-user",
            "ip_address": "192.168.1.1",
            "manifest_path": "/path/to/manifest",
        }
        listener._upsert_named_paths_group_run(group_run_data, dispose=False)

        # Update the data
        updated_group_run_data = group_run_data.copy()
        updated_group_run_data["status"] = "failed"  # Change the status
        listener._upsert_named_paths_group_run(updated_group_run_data, dispose=False)

        # Verify the updated data
        with listener.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM named_paths_group_run WHERE uuid = 'test-uuid'")
            ).fetchone()
            assert result.uuid == "test-uuid"
            assert result.status == "failed"

    # =======================
    # invalid data
    # =======================

    def test_sql_instance_invalid_data(self):
        paths = CsvPaths()
        listener = SqlResultListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine
        # Missing uuid, instance_home, manifest_path; tho not group_run_uuid
        invalid_data = {
            "at": datetime.datetime.now(),
            "group_run_uuid": "test-group-uuid",
        }
        with pytest.raises(KeyError):
            listener._upsert_instance_run(invalid_data)

    def test_sql_group_run_invalid_data(self):
        paths = CsvPaths()
        listener = SqlResultsListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine
        # Missing required field (e.g., "uuid")
        invalid_data = {
            "at": datetime.datetime.now(),
            "status": "completed",
            # Missing "uuid" and other fields
        }
        with pytest.raises(KeyError):
            listener._upsert_named_paths_group_run(invalid_data)

    def test_sql_named_file_invalid_data(self):
        paths = CsvPaths()
        listener = SqlFileListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine
        # Missing required field (e.g., "uuid")
        invalid_data = {
            "at": datetime.datetime.now(),
            "status": "completed",
            # Missing "uuid" and other fields
        }
        with pytest.raises(KeyError):
            listener._upsert_named_file(invalid_data)

    def test_sql_named_paths_invalid_data(self):
        paths = CsvPaths()
        listener = SqlPathsListener(config=paths.config)
        listener.csvpaths = paths
        listener.engine = self._engine
        # Missing required field (e.g., "uuid")
        invalid_data = {
            "at": datetime.datetime.now(),
            "status": "completed",
            # Missing "uuid" and other fields
        }
        with pytest.raises(KeyError):
            listener._upsert_named_paths(invalid_data)
