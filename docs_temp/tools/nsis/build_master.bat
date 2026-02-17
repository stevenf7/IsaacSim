@echo off

call "%~dp0..\packman\python.bat" "%~dp0..\repoman\installer.py"
if errorlevel 1 goto :fail

exit /B 0

:fail
exit /B %ERRORLEVEL%
