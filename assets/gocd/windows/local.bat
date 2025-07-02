set CSVPATH_CONFIG_PATH=assets\config\jenkins-windows-local.ini
echo %CSVPATH_CONFIG_PATH%
cmd.exe /C c:\\dev\exports.bat
:: cmd.exe /C c:\\Users\python\.local\bin\poetry.exe env remove --all

cmd.exe /C c:\\Users\python\.local\bin\poetry.exe env remove --all
cmd.exe /C c:\\Users\python\.local\bin\poetry.exe env use python
cmd.exe /C c:\\Users\python\.local\bin\poetry.exe install --only-binary=cryptography

cmd.exe /C c:\\Users\python\.local\bin\poetry.exe install
cmd.exe /C c:\\Users\python\.local\bin\poetry.exe run pytest


