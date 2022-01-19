@echo off

call "%~dp0..\repo.bat" publish_packages
if %errorlevel% neq 0 ( exit /b %errorlevel% )
