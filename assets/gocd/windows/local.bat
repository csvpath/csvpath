::
:: setup the env vars
::
set CSVPATH_CONFIG_PATH=assets\config\jenkins-windows-local.ini

cmd.exe /C c:\dev\exports.bat

::cmd.exe /C set > gocd_env.txt

echo %GCS_CREDENTIALS_PATH%
echo %CSVPATH_CONFIG_PATH%
echo %PATH%

::
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


