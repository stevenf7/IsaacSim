@echo off

call "%~dp0..\..\..\packman\packman.cmd" pull "%~dp0..\..\..\..\deps\repo-deps.packman.xml"
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\packman\python.bat" "%~dp0..\..\..\repoman\sign_archive.py"
if %errorlevel% neq 0 ( exit /b %errorlevel% )