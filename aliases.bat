doskey pytest=poetry run pytest
doskey set_local=set CSVPATH_CONFIG_PATH=assets\config\jenkins-windows-local.ini
doskey set_sftp=set CSVPATH_CONFIG_PATH=assets\config\jenkins-local-sftp.ini
doskey set_s3=set CSVPATH_CONFIG_PATH=assets\config\jenkins-local-s3.ini
doskey set_azure=set CSVPATH_CONFIG_PATH=assets\config\jenkins-local-azure.ini
doskey set_gcs=set CSVPATH_CONFIG_PATH=assets\config\jenkins-local-gcs.ini

doskey config=echo %CSVPATH_CONFIG_PATH%
