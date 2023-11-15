@echo off


call "%~dp0..\..\..\..\repo.bat" build -x $@
call "%~dp0..\..\..\..\repo.bat" publish_exts -c release $@
call "%~dp0..\..\..\..\repo.bat" publish_exts -c debug $@

if %errorlevel% neq 0 ( exit /b %errorlevel% )


