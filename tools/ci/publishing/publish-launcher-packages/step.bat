@echo off

call "%~dp0..\..\..\publish_launcher_package.bat"
if %errorlevel% neq 0 ( exit /b %errorlevel% )


