@echo off
call "%~dp0..\repo.bat" extension_docs %*
call "%~dp0..\repo.bat" docs --config release %*
