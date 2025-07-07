set CSVPATH_CONFIG_PATH=assets\config\jenkins-windows-s3.ini
echo %CSVPATH_CONFIG_PATH%


set AWS_ACCESS_KEY_ID=""
set AWS_SECRET_ACCESS_KEY=""
set SFTP_USER=""
set SFTP_PASSWORD=""
set MAILBOX_USER=""
set MAILBOX_PASSWORD=""
set TINPENNY_USER=""
set TINPENNY_PASSWORD=""
set SFTPPLUS_ADMIN_USERNAME=""
set SFTPPLUS_ADMIN_PASSWORD=""
set SFTPPLUS_SERVER=""
set SFTPPLUS_PORT=""
set GCS_CREDENTIALS_PATH=""
set TEST_VAR=""
set AZURE_STORAGE_ACCOUNT_NAME=""
set AZURE_STORAGE_ACCOUNT_KEY=""
set AZURE_STORAGE_CONNECTION_STRING=""
set OTEL_EXPORTER_OTLP_PROTOCOL=""
set OTEL_EXPORTER_OTLP_ENDPOINT=""
set OTEL_EXPORTER_OTLP_HEADERS=""
set OTEL_SERVICE_NAME=""
set OTEL_RESOURCE_ATTRIBUTES=""


call c:\dev\win-exports.bat
cmd.exe /C c:\Users\python\.local\bin\poetry.exe install
cmd.exe /C c:\Users\python\.local\bin\poetry.exe run pytest


