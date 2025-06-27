set CSVPATH_CONFIG_PATH=assets\config\jenkins-local-azure.ini
echo %CSVPATH_CONFIG_PATH%
cmd.exe /C c:\\dev\exports.bat
c:\Users\python\.local\bin\poetry.exe install
c:\Users\python\.local\bin\poetry.exe run pytest


