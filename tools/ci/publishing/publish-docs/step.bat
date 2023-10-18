@echo off
setlocal

call "%~dp0..\..\..\..\repo.bat" docs --config release --stage publish --edition production
if %errorlevel% neq 0 ( exit /b %errorlevel% )
