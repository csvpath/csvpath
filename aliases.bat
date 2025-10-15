doskey pytest=poetry run pytest
doskey set_local=set CSVPATH_CONFIG_PATH=assets\config\jenkins-windows-local.ini
doskey set_sftp=set CSVPATH_CONFIG_PATH=assets\config\jenkins-windows-sftp.ini
doskey set_s3=set CSVPATH_CONFIG_PATH=assets\config\jenkins-windows-s3.ini
doskey set_azure=set CSVPATH_CONFIG_PATH=assets\config\jenkins-windows-azure.ini
doskey set_gcs=set CSVPATH_CONFIG_PATH=assets\config\jenkins-windows-gcs.ini

doskey config=echo %CSVPATH_CONFIG_PATH%
doskey textpad="c:\Program Files\TextPad\TextPad.exe" 