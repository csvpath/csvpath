@echo off
::
:: setup the env vars
::
set CSVPATH_CONFIG_PATH=assets\config\jenkins-windows-local.ini

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


call c:\dev\exports.bat

::cmd.exe /C set > gocd_env.txt
echo(
echo "GCS path: "
echo %GCS_CREDENTIALS_PATH%
echo "CsvPath config path: "
echo %CSVPATH_CONFIG_PATH%
::echo "Login account path: "
::echo %PATH%
echo(

::))<-- just here for vim syntax highlighting
:: these four lines DO NOT work fine. that was a mistake.
::
:: cmd.exe /C c:\\Users\python\.local\bin\poetry.exe config installer.prefer-binary true
:: cmd.exe /C c:\\Users\python\.local\bin\poetry.exe env remove --all
:: cmd.exe /C c:\\Users\python\.local\bin\poetry.exe run pip uninstall -y cryptography
:: cmd.exe /C c:\\Users\python\.local\bin\poetry.exe run pip install --no-binary cryptography cryptography
:: cmd.exe /C c:\\Users\python\.local\bin\poetry.exe run pip install --prefer-binary cryptography

:: exp
:: cmd.exe /C c:\\Users\python\.local\bin\poetry.exe run pip install --upgrade pip
:: cmd.exe /C c:\\Users\python\.local\bin\poetry.exe run pip install --upgrade setuptools
::
::cmd.exe /C c:\\Users\python\.local\bin\poetry.exe run pip install --force-reinstall --no-deps pynacl --platform win_amd64 --only-binary=pynacl
::cmd.exe /C c:\\Users\python\.local\bin\poetry.exe run pip install --no-binary pynacl pynacl==1.5.0

::  --force-reinstall
:: cmd.exe /C c:\\Users\python\.local\bin\poetry.exe run pip install --no-cache --no-binary paramiko paramiko
::cmd.exe /C c:\\Users\python\.local\bin\poetry.exe run pip install --force-reinstall --no-binary cryptography cryptography
:: pip config set global.no-cache-dir false
:: cmd.exe /C c:\\Users\python\.local\bin\poetry.exe run pip install --force-reinstall --no-deps cryptography --platform win_amd64 --only-binary=cryptography

:: C:\Program Files (x86)\Go Agent\pipelines\windows-local

::
:: do the build
::
cmd.exe /C c:\Users\python\.local\bin\poetry.exe install
cmd.exe /C c:\Users\python\.local\bin\poetry.exe run pytest


