@ECHO OFF
setlocal

call "%~dp0..\packman\packman" pull "%~dp0deps.packman.xml" -p windows-x86_64
if errorlevel 1 exit /b 1

set "PYTHONPATH=%PM_SPHINX_PATH%"
set PYTHONHOME=

"%PM_PYTHON%" -s -S -u "%~dp0build.py" %*
if errorlevel 1 exit /b 1

exit /b 0
