@echo off

:: Veify formatting
call "%~dp0..\..\..\..\format_code.bat" --verify
if %errorlevel% neq 0 ( exit /b %errorlevel% )


