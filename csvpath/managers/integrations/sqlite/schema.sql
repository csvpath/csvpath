
       CREATE TABLE IF NOT EXISTS named_paths_group_run (
                uuid varchar(40) PRIMARY KEY not null,
                at datetime not null,
                archive_name varchar(100),
                time_completed datetime,
                all_completed varchar(1) default 'N',
                all_valid varchar(1) default 'N',
                all_expected_files varchar(1) default 'N',
                error_count int,
                status varchar(20),
                by_line_run varchar(1) default 'Y',
                run_home varchar(250),
                named_results_name varchar(45),
                named_paths_uuid varchar(40) not null,
                named_paths_name varchar(45) not null,
                named_paths_home varchar(250) not null,
                named_file_uuid varchar(40) not null,
                named_file_name varchar(45) not null,
                named_file_home varchar(500) not null,
                named_file_path varchar(500) not null,
                named_file_size int default -1,
                named_file_last_change,
                named_file_fingerprint varchar(70),
                hostname varchar(45),
                username varchar(45),
                ip_address varchar(40),
                manifest_path varchar(250)
        );

        CREATE TABLE IF NOT EXISTS instance_run(
                uuid varchar(40) PRIMARY KEY not null,
                at datetime not null,
                group_run_uuid varchar(40) not null,
                instance_identity varchar(100),
                instance_index int default -1,
                instance_home varchar(250) not null,
                source_mode_preceding varchar(1) default 'N',
                preceding_instance_identity varchar(100),
                actual_data_file varchar(500),
                number_of_files_expected int default -1,
                number_of_files_generated int default -1,
                files_expected varchar(1) default 'Y',
                valid varchar(1) default 'N',
                completed varchar(1) default 'N',
                lines_scanned int default 0,
                lines_total int default 0,
                lines_matched int default 0,
                error_count int default -1,
                manifest_path varchar(250) not null,
                FOREIGN KEY(group_run_uuid) REFERENCES named_paths_group_run(uuid)
        );



